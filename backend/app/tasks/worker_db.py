"""
Database helpers for Celery workers.

The app-wide engine in app.database is bound to the event loop that created it.
Celery tasks call asyncio.run(), which spins up a *new* loop per invocation, so
reusing that engine raises "attached to a different loop". Each task instead runs
through run_task_async(), which creates a dedicated engine for that single run and
disposes it afterward.
"""
from collections.abc import Awaitable, Callable
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

T = TypeVar("T")


async def _with_session(coro_factory: Callable[[AsyncSession], Awaitable[T]]) -> T:
    """Run coro_factory with a session from a loop-local engine, then dispose it."""
    engine = create_async_engine(settings.database_url.strip(), echo=False, pool_pre_ping=True)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with session_maker() as session:
            return await coro_factory(session)
    finally:
        await engine.dispose()


def run_task(coro_factory: Callable[[AsyncSession], Awaitable[T]]) -> T:
    """
    Synchronous entry point for Celery tasks.

    Usage:
        @celery.task(...)
        def my_task(pa_id):
            async def _run(db):
                ...
            return run_task(_run)
    """
    import asyncio

    return asyncio.run(_with_session(coro_factory))
