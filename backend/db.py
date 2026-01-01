import os
import json
import aiosqlite
import sqlite_vec
from typing import Optional

DB_PATH = os.getenv("DATABASE_PATH", "/app/data/resume.db")
DB: Optional[aiosqlite.Connection] = None


def serialize_float32(vector: list) -> bytes:
    """Serialize a list of floats to binary format for sqlite-vec."""
    import struct
    return struct.pack(f'{len(vector)}f', *vector)


async def get_db() -> aiosqlite.Connection:
    """Get or create database connection."""
    global DB
    if DB is None:
        DB = await aiosqlite.connect(DB_PATH)
        DB.row_factory = aiosqlite.Row

        # Enable extension loading (required for sqlite-vec)
        await DB.execute("SELECT 1")  # Ensure connection is ready
        DB._conn.enable_load_extension(True)

        # Load sqlite-vec extension
        await DB.execute("SELECT load_extension(?)", [sqlite_vec.loadable_path()])

        # Disable extension loading for security
        DB._conn.enable_load_extension(False)
        await DB.commit()
    return DB


async def close_db():
    """Close database connection."""
    global DB
    if DB:
        await DB.close()
        DB = None


async def init_db():
    """Initialize database schema."""
    db = await get_db()

    # Create experiences table for metadata
    await db.execute("""
        CREATE TABLE IF NOT EXISTS experiences (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            skills TEXT DEFAULT '[]',
            metadata TEXT DEFAULT '{}',
            source_file TEXT,
            content_hash TEXT,
            last_updated TEXT DEFAULT (datetime('now')),
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Create indexes
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_experiences_source_file
        ON experiences(source_file)
    """)
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_experiences_content_hash
        ON experiences(content_hash)
    """)

    # Create virtual table for vector search
    # vec0 virtual tables store vectors with a rowid that we'll map to experience id
    await db.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS experience_vectors USING vec0(
            embedding float[768]
        )
    """)

    # Create a mapping table to link vector rowids to experience ids
    await db.execute("""
        CREATE TABLE IF NOT EXISTS vector_mapping (
            vector_rowid INTEGER PRIMARY KEY,
            experience_id TEXT NOT NULL,
            FOREIGN KEY (experience_id) REFERENCES experiences(id) ON DELETE CASCADE
        )
    """)
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_vector_mapping_experience
        ON vector_mapping(experience_id)
    """)

    await db.commit()


# Legacy compatibility aliases
async def get_db_pool():
    """Legacy alias for get_db - returns connection for compatibility."""
    return await get_db()


async def close_db_pool():
    """Legacy alias for close_db."""
    await close_db()
