#!/bin/bash
# Create tables directly using Python (bypasses alembic psycopg2 issue)
python -c "
import asyncio
from app.database import engine
from app.models import Base

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

asyncio.run(create_tables())
print('Database tables created successfully')
" || echo "Table creation skipped (may already exist)"

# Start the application
uvicorn app.main:app --host 0.0.0.0 --port 8000
