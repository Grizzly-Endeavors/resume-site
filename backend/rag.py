import json
import logging
from db import get_db, serialize_float32
from ai.llm import llm_handler
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def apply_diversity_scoring(
    results: List[Dict[str, Any]],
    shown_counts: Dict[str, int],
    penalty_per_showing: float = 0.4,
    max_penalty: float = 0.9
) -> List[Dict[str, Any]]:
    """
    Apply cumulative diversity penalty to previously shown experiences.

    Args:
        results: RAG search results with 'similarity' scores
        shown_counts: Dict of experience IDs to show counts
        penalty_per_showing: Penalty factor per showing (0.4 = 40% per showing)
        max_penalty: Maximum penalty cap (0.9 = 90% max reduction)

    Returns:
        Re-ranked results
    """
    for result in results:
        exp_id = result['id']
        if exp_id in shown_counts:
            count = shown_counts[exp_id]
            penalty = min(penalty_per_showing * count, max_penalty)
            original_score = result['similarity']
            result['similarity'] *= (1 - penalty)
            logger.info(f"[DIVERSITY] Penalized '{result['title']}' (shown {count}x): {original_score:.3f} -> {result['similarity']:.3f}")

    # Re-sort by adjusted similarity
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results


async def search_similar_experiences(
    query: str,
    limit: int = 5,
    shown_counts: Optional[Dict[str, int]] = None
) -> List[Dict[str, Any]]:
    """Search with optional diversity scoring using sqlite-vec."""
    db = await get_db()

    shown_count = sum(shown_counts.values()) if shown_counts else 0
    logger.info(f"[RAG Search] Query: '{query}', Shown counts: {shown_count}")
    query_embedding = await llm_handler.generate_embedding(query, task_type="retrieval_query")

    # Serialize embedding for sqlite-vec
    embedding_blob = serialize_float32(query_embedding)

    # Fetch more results than needed for better diversity (fetch 2x limit)
    fetch_limit = limit * 2 if shown_counts else limit

    # Query sqlite-vec virtual table and join with experiences
    cursor = await db.execute("""
        SELECT
            e.id,
            e.title,
            e.content,
            e.skills,
            e.metadata,
            v.distance
        FROM experience_vectors v
        JOIN vector_mapping m ON v.rowid = m.vector_rowid
        JOIN experiences e ON m.experience_id = e.id
        WHERE v.embedding MATCH ?
        ORDER BY v.distance
        LIMIT ?
    """, [embedding_blob, fetch_limit])

    rows = await cursor.fetchall()

    results = []
    for row in rows:
        # Convert distance to similarity (sqlite-vec uses L2 distance by default)
        # Lower distance = higher similarity
        # Normalize to 0-1 range: similarity = 1 / (1 + distance)
        distance = row["distance"]
        similarity = 1.0 / (1.0 + distance)

        results.append({
            "id": row["id"],
            "title": row["title"],
            "content": row["content"],
            "skills": json.loads(row["skills"]) if row["skills"] else [],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            "similarity": similarity
        })

    # Apply diversity scoring if shown_counts provided
    if shown_counts:
        results = apply_diversity_scoring(results, shown_counts)

    # Return requested limit after re-ranking
    return results[:limit]


async def format_rag_results(results: List[Dict[str, Any]]) -> str:
    formatted = ""
    for r in results:
        formatted += f"Title: {r['title']}\n"
        formatted += f"Skills: {', '.join(r['skills']) if r['skills'] else 'N/A'}\n"
        formatted += f"Content: {r['content']}\n"
        formatted += "---\n"
    return formatted
