import anthropic
import httpx
import pytest
from unittest.mock import AsyncMock

from app.agents.base import BaseAgent, _is_retryable_claude_error


class _Agent(BaseAgent):
    agent_name = "test_retry"

    async def execute(self, context):  # pragma: no cover - not used
        ...

    def get_system_prompt(self) -> str:
        return "test"


def _status_error(code: int) -> anthropic.APIStatusError:
    req = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    resp = httpx.Response(code, request=req, json={"error": {"message": "x"}})
    if code == 429:
        return anthropic.RateLimitError("rate", response=resp, body=None)
    return anthropic.APIStatusError("overloaded", response=resp, body=None)


def test_retry_predicate_classifies_status_codes():
    assert _is_retryable_claude_error(_status_error(429)) is True
    assert _is_retryable_claude_error(_status_error(529)) is True
    assert _is_retryable_claude_error(_status_error(400)) is False
    assert _is_retryable_claude_error(_status_error(401)) is False


@pytest.fixture
def _no_wait(monkeypatch):
    # Neutralize backoff sleeps so the retry tests run instantly.
    monkeypatch.setattr(BaseAgent.call_claude.retry, "wait", lambda *a, **k: 0)


@pytest.mark.asyncio
async def test_call_claude_retries_on_529_then_succeeds(_no_wait):
    agent = _Agent(db=None)
    ok = object()
    agent.client.messages.create = AsyncMock(
        side_effect=[_status_error(529), _status_error(429), ok]
    )

    result = await agent.call_claude(messages=[{"role": "user", "content": "hi"}])

    assert result is ok
    assert agent.client.messages.create.call_count == 3


@pytest.mark.asyncio
async def test_call_claude_does_not_retry_on_400(_no_wait):
    agent = _Agent(db=None)
    agent.client.messages.create = AsyncMock(side_effect=_status_error(400))

    with pytest.raises(anthropic.APIStatusError):
        await agent.call_claude(messages=[{"role": "user", "content": "hi"}])

    assert agent.client.messages.create.call_count == 1


@pytest.mark.asyncio
async def test_call_claude_gives_up_after_max_attempts(_no_wait):
    agent = _Agent(db=None)
    agent.client.messages.create = AsyncMock(side_effect=_status_error(529))

    with pytest.raises(anthropic.APIStatusError):
        await agent.call_claude(messages=[{"role": "user", "content": "hi"}])

    # stop_after_attempt(4)
    assert agent.client.messages.create.call_count == 4
