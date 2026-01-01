import os
import ssl
import asyncpg
from typing import Optional

POOL: Optional[asyncpg.Pool] = None

def get_ssl_context():
    """Create SSL context for PostgreSQL connection with CA certificate."""
    ca_cert_path = os.getenv("PGSSLROOTCERT")
    if ca_cert_path and os.path.exists(ca_cert_path):
        ctx = ssl.create_default_context(cafile=ca_cert_path)
        ctx.check_hostname = False  # PostgreSQL service uses internal DNS
        return ctx
    return None

async def get_db_pool():
    global POOL
    if POOL is None:
        ssl_ctx = get_ssl_context()
        POOL = await asyncpg.create_pool(
            dsn=os.getenv("DATABASE_URL"),
            min_size=1,
            max_size=10,
            ssl=ssl_ctx if ssl_ctx else "require"
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
                embedding vector(768),
                source_file TEXT,
                content_hash TEXT,
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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

        # Create indexes for tracking columns
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_experiences_source_file
            ON experiences(source_file);
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_experiences_content_hash
            ON experiences(content_hash);
        """)

