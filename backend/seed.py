import asyncio
import os
import re
from typing import List, Dict, Any
from db import init_db, get_db_pool, close_db_pool
from ai.llm import llm_handler
import json

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

async def seed_data():
    await init_db()
    pool = await get_db_pool()
    
    # In container, data is likely copied to /app/data or similar
    # If running locally from backend/, data is in ../data
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check current dir first (container structure: /app/data)
    data_dir = os.path.join(current_dir, 'data')
    if not os.path.exists(data_dir):
        # Fallback to parent dir (local dev structure: backend/../data)
        data_dir = os.path.join(os.path.dirname(current_dir), 'data')
    
    subdirs = ['jobs', 'projects']
    items = []
    
    for subdir in subdirs:
        subdir_path = os.path.join(data_dir, subdir)
        if os.path.exists(subdir_path):
            for filename in os.listdir(subdir_path):
                if filename.endswith(".md"):
                    full_path = os.path.join(subdir_path, filename)
                    print(f"Parsing {full_path}...")
                    item = parse_markdown_file(full_path)
                    if item:
                        items.append(item)
    
    if not items:
        print(f"No markdown items found in {data_dir}/jobs or {data_dir}/projects")
        await close_db_pool()
        return

    print(f"Parsed {len(items)} items from markdown files.")
    
    async with pool.acquire() as conn:
        # Check if data already exists to avoid duplicates (naive check)
        count = await conn.fetchval("SELECT COUNT(*) FROM experiences")
        if count > 0:
            print(f"Database already has {count} items. Skipping seed.")
            return

        for item in items:
            print(f"Processing: {item['title']}")
            embedding = await llm_handler.generate_embedding(f"{item['title']}\n{item['content']}")
            embedding_str = f"[{','.join(map(str, embedding))}]"
            
            await conn.execute("""
                INSERT INTO experiences (title, content, skills, metadata, embedding)
                VALUES ($1, $2, $3, $4, $5)
            """, item['title'], item['content'], item['skills'], json.dumps(item['metadata']), embedding_str)
            
    print("Seeding complete.")
    await close_db_pool()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(seed_data())
