import asyncio
import os
import re
import hashlib
import logging
from typing import List, Dict, Any, Optional
from db import init_db, get_db_pool, close_db_pool
from ai.llm import llm_handler
import json

logger = logging.getLogger(__name__)

def parse_markdown_file(file_path: str) -> Dict[str, Any]:
    with open(file_path, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    # Filter out empty lines at the start
    while lines and not lines[0].strip():
        lines.pop(0)
    
    if not lines:
        return {}

    # Title is usually the first line, stripped of '# '
    title = lines[0].strip().lstrip('#').strip()
    body = '\n'.join(lines[1:]).strip()
    
    # Extract skills
    skills = []
    skills_match = re.search(r'\*\*Skills:\*\*\s*(.*)', body, re.IGNORECASE)
    if skills_match:
        skills = [s.strip() for s in skills_match.group(1).split(',')]
        
    # Extract metadata (dates, etc)
    metadata = {}
    dates_match = re.search(r'\*\*Dates:\*\*\s*(.*)', body, re.IGNORECASE)
    if dates_match:
        metadata['date'] = dates_match.group(1).strip()
    
    # Add type based on folder name
    if 'jobs' in file_path:
        metadata['type'] = 'job'
    elif 'projects' in file_path:
        metadata['type'] = 'project'
        
    return {
        "title": title,
        "content": body,
        "skills": skills,
        "metadata": metadata
    }

def compute_file_hash(file_path: str) -> str:
    """Compute MD5 hash of file content."""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        hasher.update(f.read())
    return hasher.hexdigest()

def discover_data_files(data_dir: str) -> Dict[str, tuple[str, str]]:
    """
    Discover all markdown files in data directory.
    Returns: {source_file: (full_path, content_hash)}
    e.g., {"jobs/writer.md": ("/app/data/jobs/writer.md", "abc123...")}
    """
    files = {}
    subdirs = ['jobs', 'projects']

    for subdir in subdirs:
        subdir_path = os.path.join(data_dir, subdir)
        if os.path.exists(subdir_path):
            for filename in os.listdir(subdir_path):
                if filename.endswith(".md"):
                    full_path = os.path.join(subdir_path, filename)
                    source_file = f"{subdir}/{filename}"
                    content_hash = compute_file_hash(full_path)
                    files[source_file] = (full_path, content_hash)

    return files

async def check_needs_update(conn, source_file: str, content_hash: str) -> tuple[bool, Optional[str]]:
    """
    Check if file needs to be updated/inserted.
    Returns: (needs_update: bool, existing_id: Optional[str])
    """
    row = await conn.fetchrow("""
        SELECT id, content_hash FROM experiences WHERE source_file = $1
    """, source_file)

    if not row:
        return (True, None)  # New file, needs insert

    if row['content_hash'] != content_hash:
        return (True, str(row['id']))  # Changed file, needs update

    return (False, str(row['id']))  # No change, skip

async def upsert_experience(conn, source_file: str, content_hash: str, item: Dict[str, Any], embedding: List[float], existing_id: Optional[str]):
    """Insert new or update existing experience."""
    embedding_str = f"[{','.join(map(str, embedding))}]"

    if existing_id:
        # Update existing
        await conn.execute("""
            UPDATE experiences
            SET title = $1, content = $2, skills = $3, metadata = $4,
                embedding = $5, content_hash = $6, last_updated = NOW()
            WHERE id = $7
        """, item['title'], item['content'], item['skills'],
            json.dumps(item['metadata']), embedding_str, content_hash, existing_id)
    else:
        # Insert new
        await conn.execute("""
            INSERT INTO experiences (title, content, skills, metadata, embedding, source_file, content_hash, created_at, last_updated)
            VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
        """, item['title'], item['content'], item['skills'],
            json.dumps(item['metadata']), embedding_str, source_file, content_hash)

async def delete_orphaned_experiences(conn, current_files: set[str]) -> int:
    """Delete DB entries for files that no longer exist."""
    result = await conn.execute("""
        DELETE FROM experiences
        WHERE source_file IS NOT NULL
        AND source_file NOT IN (SELECT unnest($1::text[]))
    """, list(current_files))

    # Extract count from result string "DELETE N"
    return int(result.split()[-1]) if result else 0

async def seed_data():
    """Incremental seeding - only updates changed/new files."""
    await init_db()
    pool = await get_db_pool()

    # Determine data directory path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, 'data')
    if not os.path.exists(data_dir):
        data_dir = os.path.join(os.path.dirname(current_dir), 'data')

    logger.info(f"Starting incremental seed from {data_dir}")

    async with pool.acquire() as conn:
        # Discover all markdown files with hashes
        files = discover_data_files(data_dir)
        logger.info(f"Discovered {len(files)} markdown files")

        if not files:
            logger.warning("No markdown files found in data directory")
            return

        # Track statistics
        stats = {"new": 0, "updated": 0, "skipped": 0, "failed": 0, "deleted": 0}

        # Process each file
        for source_file, (full_path, content_hash) in files.items():
            try:
                # Check if update needed
                needs_update, existing_id = await check_needs_update(conn, source_file, content_hash)

                if not needs_update:
                    logger.info(f"Skipped (no changes): {source_file}")
                    stats["skipped"] += 1
                    continue

                # Parse markdown
                item = parse_markdown_file(full_path)
                if not item:
                    logger.warning(f"Failed to parse: {source_file}")
                    stats["failed"] += 1
                    continue

                # Generate embedding
                logger.info(f"Processing: {source_file} (hash: {content_hash[:8]}...)")
                embedding = await llm_handler.generate_embedding(f"{item['title']}\n{item['content']}")

                # Upsert to database
                await upsert_experience(conn, source_file, content_hash, item, embedding, existing_id)

                if existing_id:
                    logger.info(f"  → Updated existing entry")
                    stats["updated"] += 1
                else:
                    logger.info(f"  → Inserted new entry")
                    stats["new"] += 1

            except Exception as e:
                logger.error(f"Failed to process {source_file}: {e}", exc_info=True)
                stats["failed"] += 1
                # Continue with other files

        # Delete orphaned entries
        deleted = await delete_orphaned_experiences(conn, set(files.keys()))
        stats["deleted"] = deleted
        if deleted > 0:
            logger.info(f"Deleted {deleted} orphaned entries")

        # Log summary
        logger.info(f"Seed complete - New: {stats['new']}, Updated: {stats['updated']}, Skipped: {stats['skipped']}, Failed: {stats['failed']}, Deleted: {stats['deleted']}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(seed_data())
