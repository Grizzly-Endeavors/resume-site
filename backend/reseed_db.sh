#!/bin/bash
# Script to re-seed the database with fresh embeddings
# This will clear existing experiences and re-import from markdown files

set -e

echo "⚠️  This will DELETE all existing experiences and re-seed from markdown files"
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

# Activate virtual environment
source venv/bin/activate

# Clear existing data
echo "Clearing existing experiences..."
python3 -c "
import asyncio
from db import get_db_pool, close_db_pool

async def clear():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval('SELECT COUNT(*) FROM experiences')
        print(f'Found {count} existing experiences')
        await conn.execute('DELETE FROM experiences')
        print('✓ Cleared all experiences')
    await close_db_pool()

asyncio.run(clear())
"

# Run seed script
echo "Running seed script..."
python3 seed.py

echo "✓ Database re-seeded successfully!"
