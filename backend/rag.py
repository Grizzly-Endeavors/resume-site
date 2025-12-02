import json
import logging
from db import get_db_pool
from llm import llm_handler
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def apply_diversity_scoring(
    results: List[Dict[str, Any]],
    shown_ids: List[str],
    penalty: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Apply diversity penalty to previously shown experiences.

    Args:
        results: RAG search results with 'similarity' scores
        shown_ids: List of experience IDs already shown
        penalty: Reduction factor (0.3 = 30% penalty)

    Returns:
        Re-ranked results
    """
    shown_set = set(shown_ids)

    for result in results:
        if result['id'] in shown_set:
            original_score = result['similarity']
            result['similarity'] *= (1 - penalty)
            logger.info(f"[DIVERSITY] Penalized '{result['title']}': {original_score:.3f} -> {result['similarity']:.3f}")

    # Re-sort by adjusted similarity
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results

async def search_similar_experiences(
    query: str,
    limit: int = 5,
    shown_ids: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Search with optional diversity scoring"""
    pool = await get_db_pool()

    logger.info(f"[RAG Search] Query: '{query}', Shown IDs: {len(shown_ids) if shown_ids else 0}")
    query_embedding = await llm_handler.generate_embedding(query, task_type="retrieval_query")

    # Format embedding for pgvector
    embedding_str = f"[{','.join(map(str, query_embedding))}]"

    async with pool.acquire() as conn:
        # Fetch more results than needed for better diversity (fetch 2x limit)
        fetch_limit = limit * 2 if shown_ids else limit

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
            
        # Apply diversity scoring if shown_ids provided
        if shown_ids:
            results = apply_diversity_scoring(results, shown_ids)

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