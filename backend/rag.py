import json
import logging
from db import get_db_pool
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
    """Search with optional diversity scoring"""
    pool = await get_db_pool()

    shown_count = sum(shown_counts.values()) if shown_counts else 0
    logger.info(f"[RAG Search] Query: '{query}', Shown counts: {shown_count}")
    query_embedding = await llm_handler.generate_embedding(query, task_type="retrieval_query")

    # Format embedding for pgvector
    embedding_str = f"[{','.join(map(str, query_embedding))}]"

    async with pool.acquire() as conn:
        # Fetch more results than needed for better diversity (fetch 2x limit)
        fetch_limit = limit * 2 if shown_counts else limit

        rows = await conn.fetch("""
            SELECT id, title, content, skills, metadata, 
                   1 - (embedding <=> $1) as similarity
            FROM experiences
            ORDER BY embedding <=> $1
            LIMIT $2
        """, embedding_str, fetch_limit)
        
        results = []
        for row in rows:
            results.append({
                "id": str(row["id"]),
                "title": row["title"],
                "content": row["content"],
                "skills": row["skills"],
                "metadata": json.loads(row["metadata"]) if isinstance(row["metadata"], str) else row["metadata"],
                "similarity": row["similarity"]
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