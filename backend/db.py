import os
import asyncpg
from typing import Optional

POOL: Optional[asyncpg.Pool] = None

async def get_db_pool():
    global POOL
    if POOL is None:
        POOL = await asyncpg.create_pool(
            dsn=os.getenv("DATABASE_URL"),
            min_size=1,
            max_size=10
        )
    return POOL

async def close_db_pool():
    global POOL
    if POOL:
        await POOL.close()

async def init_db():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Enable pgvector extension
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Create experiences table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS experiences (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                skills TEXT[],
                metadata JSONB DEFAULT '{}'::jsonb,
                embedding vector(768) 
            );
        """)
        # Note: Embedding dimension 3072 is for newer Gemini models.
        # The plan mentioned 1536 (OpenAI) or 384. I'll stick to 768 (Gemini Embedding) or 1536 if requested.
        # The plan says "embedding (vector(1536)) -- or 384 depending on model".
        # Since we are using Gemini as fallback and Cerebras (likely Llama models), we need an embedding model.
        # I'll assume we use a standard embedding model compatible with what we can access. 
        # For now, let's stick to 768 (text-embedding-004 from Google) or similar.
        # Let's check the plan again... it doesn't specify the *embedding* model, just the chat model.
        # I will assume 768 for now as it's a good middle ground and compatible with Google's embeddings.
        
        # Create HNSW index for faster search (disabled for 3072 dimensions)
        # await conn.execute("""
        #     CREATE INDEX IF NOT EXISTS experiences_embedding_idx 
        #     ON experiences USING hnsw (embedding vector_cosine_ops);
        # """)

