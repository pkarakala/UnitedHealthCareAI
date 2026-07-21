#!/bin/bash
# Create tables directly using Python (with URL strip fix)
python -c "
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from app.models import Base

async def create_tables():
    url = os.environ.get('DATABASE_URL', '').strip()
    engine = create_async_engine(url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print('Database tables created successfully')

asyncio.run(create_tables())
" || echo "Table creation skipped"

# Start the application
uvicorn app.main:app --host 0.0.0.0 --port 8000
