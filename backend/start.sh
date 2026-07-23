#!/bin/bash
set -e

# Databases created before Alembic was wired in (via create_all) have tables
# but no alembic_version row. Stamp those at the baseline revision so
# `upgrade head` only applies migrations added since.
if python - <<'PY'
import asyncio
import os
import sys

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine


async def needs_stamp() -> bool:
    url = os.environ.get("DATABASE_URL", "").strip()
    engine = create_async_engine(url, echo=False)
    try:
        async with engine.connect() as conn:
            tables = await conn.run_sync(lambda c: inspect(c).get_table_names())
    finally:
        await engine.dispose()
    return "prior_auths" in tables and "alembic_version" not in tables


sys.exit(0 if asyncio.run(needs_stamp()) else 1)
PY
then
    echo "Existing schema without alembic_version detected; stamping baseline 001"
    alembic stamp 001
fi

alembic upgrade head

uvicorn app.main:app --host 0.0.0.0 --port 8000
