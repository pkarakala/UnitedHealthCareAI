from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel

from app.agents.approval import _coerce_money
from app.agents.base import BaseAgent, ClaudeJSONError, _strip_json_fence


class _Agent(BaseAgent):
    agent_name = "test_json"

    async def execute(self, context):  # pragma: no cover
        ...

    def get_system_prompt(self) -> str:
        return "test"


def _reply(text: str):
    return AsyncMock(
        content=[AsyncMock(text=text)],
        usage=AsyncMock(input_tokens=10, output_tokens=5),
    )


def test_strip_json_fence_variants():
    assert _strip_json_fence('{"a": 1}') == '{"a": 1}'
    assert _strip_json_fence('```json\n{"a": 1}\n```') == '{"a": 1}'
    assert _strip_json_fence('```\n{"a": 1}\n```') == '{"a": 1}'


@pytest.mark.asyncio
async def test_parses_fenced_json():
    agent = _Agent(db=None)
    agent.client.messages.create = AsyncMock(return_value=_reply('```json\n{"ok": true}\n```'))
    parsed, ti, to = await agent.call_claude_json("hi")
    assert parsed == {"ok": True}
    assert (ti, to) == (10, 5)


@pytest.mark.asyncio
async def test_retries_on_bad_json_then_succeeds():
    agent = _Agent(db=None)
    agent.client.messages.create = AsyncMock(
        side_effect=[_reply("not json at all"), _reply('{"ok": 1}')]
    )
    parsed, ti, to = await agent.call_claude_json("hi")
    assert parsed == {"ok": 1}
    # Token counts summed across both attempts.
    assert (ti, to) == (20, 10)
    assert agent.client.messages.create.call_count == 2


@pytest.mark.asyncio
async def test_raises_after_exhausting_attempts():
    agent = _Agent(db=None)
    agent.client.messages.create = AsyncMock(return_value=_reply("still not json"))
    with pytest.raises(ClaudeJSONError):
        await agent.call_claude_json("hi")
    assert agent.client.messages.create.call_count == 2


@pytest.mark.asyncio
async def test_rejects_non_object_json():
    agent = _Agent(db=None)
    # Valid JSON, but a list — callers expect a dict for .get().
    agent.client.messages.create = AsyncMock(return_value=_reply("[1, 2, 3]"))
    with pytest.raises(ClaudeJSONError):
        await agent.call_claude_json("hi", max_parse_attempts=1)


@pytest.mark.asyncio
async def test_schema_validation_rejects_then_accepts():
    class Result(BaseModel):
        approved: bool

    agent = _Agent(db=None)
    agent.client.messages.create = AsyncMock(
        side_effect=[_reply('{"wrong": "shape"}'), _reply('{"approved": true}')]
    )
    parsed, _, _ = await agent.call_claude_json("hi", schema=Result)
    assert parsed == {"approved": True}


def test_coerce_money_handles_llm_junk():
    assert _coerce_money(1200) == 1200.0
    assert _coerce_money(1200.5) == 1200.5
    assert _coerce_money("$1,200.00") == 1200.0
    assert _coerce_money("TBD") == 0.0  # would have crashed float("TBD")
    assert _coerce_money(None) == 0.0
    assert _coerce_money("high") == 0.0
