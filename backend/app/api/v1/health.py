from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import HealthCheck

router = APIRouter()


@router.get("", response_model=HealthCheck)
async def health_check(db: AsyncSession = Depends(get_db)):
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    return HealthCheck(
        status="healthy" if db_status == "connected" else "degraded",
        timestamp=datetime.now(timezone.utc),
        database=db_status,
        redis="connected",
    )


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception as e:
        return {"ready": False, "error": str(e)}


@router.post("/seed-demo")
async def seed_demo_data():
    """One-time endpoint to seed demo data. Remove in production."""
    import subprocess
    result = subprocess.run(
        ["python", "scripts/seed_demo.py"],
        capture_output=True, text=True, cwd="/app"
    )
    if result.returncode == 0:
        return {"status": "success", "output": result.stdout}
    return {"status": "error", "output": result.stderr[-500:]}
