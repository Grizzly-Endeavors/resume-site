import json
import logging
from db import get_db_pool
from llm import generate_embedding
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

async def search_similar_experiences(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    pool = await get_db_pool()

    logger.info(f"[RAG Search] Generating embedding for query: '{query}'")
    query_embedding = await generate_embedding(query, task_type="retrieval_query")

    # Format embedding for pgvector
    embedding_str = f"[{','.join(map(str, query_embedding))}]"

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, title, content, skills, metadata, 
                   1 - (embedding <=> $1) as similarity
            FROM experiences
            ORDER BY embedding <=> $1
            LIMIT $2
        """, embedding_str, limit)
        
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
            
        return results

async def format_rag_results(results: List[Dict[str, Any]]) -> str:
    formatted = ""
    for r in results:
        formatted += f"Title: {r['title']}\n"
        formatted += f"Skills: {', '.join(r['skills']) if r['skills'] else 'N/A'}\n"
        formatted += f"Content: {r['content']}\n"
        formatted += "---\n"
    return formatted
