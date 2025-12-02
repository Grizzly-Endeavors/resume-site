"""
Debug script to test RAG retrieval and see similarity scores
"""
import asyncio
import os
from dotenv import load_dotenv
from rag import search_similar_experiences
from db import get_db_pool, close_db_pool

load_dotenv()

async def test_queries():
    test_cases = [
        "DevOps experience",
        "AI and machine learning projects",
        "Docker and containerization",
        "Infrastructure and automation",
        "LLM and artificial intelligence",
    ]

    print("=" * 80)
    print("RAG RETRIEVAL DEBUG")
    print("=" * 80)

    for query in test_cases:
        print(f"\n{'='*80}")
        print(f"QUERY: {query}")
        print(f"{'='*80}")

        results = await search_similar_experiences(query, limit=10)

        for i, result in enumerate(results, 1):
            print(f"\n{i}. [{result['similarity']:.4f}] {result['title']}")
            print(f"   Type: {result['metadata'].get('type', 'unknown')}")
            print(f"   Skills: {', '.join(result['skills'][:5]) if result['skills'] else 'None'}")
            print(f"   Content preview: {result['content'][:150]}...")

    await close_db_pool()

if __name__ == "__main__":
    asyncio.run(test_queries())
