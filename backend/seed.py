import asyncio
import os
import re
from typing import List, Dict, Any
from db import init_db, get_db_pool, close_db_pool
from llm import generate_embedding
import json

def parse_markdown_resume(file_path: str) -> List[Dict[str, Any]]:
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Split by headers (assuming # Title format)
    # This is a simple parser, might need more robustness for complex markdown
    sections = re.split(r'^# ', content, flags=re.MULTILINE)
    parsed_items = []
    
    for section in sections:
        if not section.strip():
            continue
            
        lines = section.split('\n')
        title = lines[0].strip()
        body = '\n'.join(lines[1:]).strip()
        
        # Extract skills (naive extraction)
        skills = []
        skills_match = re.search(r'\*\*Skills:\*\*\s*(.*)', body, re.IGNORECASE)
        if skills_match:
            skills = [s.strip() for s in skills_match.group(1).split(',')]
            
        # Extract metadata (dates, etc)
        metadata = {}
        dates_match = re.search(r'\*\*Dates:\*\*\s*(.*)', body, re.IGNORECASE)
        if dates_match:
            metadata['date'] = dates_match.group(1).strip()
            
        parsed_items.append({
            "title": title,
            "content": body,
            "skills": skills,
            "metadata": metadata
        })
        
    return parsed_items

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
    
    resume_file = os.path.join(data_dir, 'resume-item.md')
    
    if not os.path.exists(resume_file):
        print(f"No data file found at {resume_file}")
        return

    items = parse_markdown_resume(resume_file)
    print(f"Parsed {len(items)} items from markdown.")
    
    async with pool.acquire() as conn:
        # Check if data already exists to avoid duplicates (naive check)
        count = await conn.fetchval("SELECT COUNT(*) FROM experiences")
        if count > 0:
            print(f"Database already has {count} items. Skipping seed.")
            return

        for item in items:
            print(f"Processing: {item['title']}")
            embedding = await generate_embedding(f"{item['title']}\n{item['content']}")
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
