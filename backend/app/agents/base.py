import uuid
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone

import anthropic
import structlog
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings
from app.models.agent_execution import AgentExecution

logger = structlog.get_logger()

# Status codes worth retrying: 429 (rate limit) and 529 (overloaded). Anthropic
# 0.42 has a dedicated RateLimitError for 429 but surfaces 529 as a generic
# APIStatusError, so we key on the instance status_code rather than the class.
_RETRY_STATUS_CODES = {429, 529}


def _is_retryable_claude_error(exc: BaseException) -> bool:
    if isinstance(exc, (anthropic.APIConnectionError, anthropic.APITimeoutError)):
        return True
    if isinstance(exc, anthropic.APIStatusError):
        return getattr(exc, "status_code", None) in _RETRY_STATUS_CODES
    return False


def _log_claude_retry(retry_state) -> None:
    """tenacity before_sleep callback — structlog-friendly (before_sleep_log wants stdlib)."""
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    logger.warning(
        "claude.retry",
        attempt=retry_state.attempt_number,
        error=str(exc) if exc else None,
        status_code=getattr(exc, "status_code", None),
    )


class AgentContext(BaseModel):
    prior_auth_id: str
    patient_id: str
    prescription_id: str
    insurance_id: str | None = None
    metadata: dict = {}


class AgentResult(BaseModel):
    success: bool
    data: dict = {}
    next_agent: str | None = None
    condition: str | None = None
    error: str | None = None
    tokens_input: int = 0
    tokens_output: int = 0
    requires_human: bool = False
    message: str | None = None


class SimulationDisabledError(RuntimeError):
    """Raised when a simulating agent runs with simulation_mode=False."""


class ClaudeJSONError(ValueError):
    """Raised when Claude fails to return valid JSON after all parse attempts."""


def _strip_json_fence(text: str) -> str:
    """Remove a leading ```json / ``` code fence and trailing ``` if present."""
    text = text.strip()
    if not text.startswith("```"):
        return text
    # Drop the opening fence line (``` or ```json) and any trailing fence.
    without_open = text.split("\n", 1)[1] if "\n" in text else ""
    return without_open.rsplit("```", 1)[0].strip()


class BaseAgent(ABC):
    """
    Abstract base class for all 16 PA workflow agents.

    Each agent implements execute() with its specific logic and get_system_prompt()
    for its Claude instructions. The base run() method handles lifecycle management:
    DB logging, tracing, timing, error handling.

    Agents that fabricate external-world results (payer responses, EHR data,
    submission confirmations) must set simulates_external_calls = True. They are
    blocked from running when settings.simulation_mode is False, and any PA they
    touch is flagged is_simulated.
    """

    agent_name: str = "base"
    model: str = settings.default_model
    max_tokens: int = settings.max_tokens
    temperature: float = 0.1
    simulates_external_calls: bool = False

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        """Main execution logic. Must be implemented by each agent."""
        ...

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent's Claude calls."""
        ...

    def get_tools(self) -> list[dict]:
        """Override to provide tools for Claude tool_use. Default: no tools."""
        return []

    async def run(self, context: AgentContext) -> AgentResult:
        """
        Lifecycle wrapper called by the orchestrator.
        Handles: execution logging, timing, error recovery.
        """
        if self.simulates_external_calls and not settings.simulation_mode:
            logger.error(
                "agent.blocked_simulation_disabled",
                agent=self.agent_name,
                prior_auth_id=context.prior_auth_id,
            )
            return AgentResult(
                success=False,
                requires_human=True,
                error=(
                    f"Agent '{self.agent_name}' simulates external integrations and is "
                    "disabled in production (simulation_mode=False). A real integration "
                    "or manual handling is required."
                ),
            )

        execution_id = str(uuid.uuid4())
        start_time = time.time()

        execution = AgentExecution(
            id=execution_id,
            prior_auth_id=context.prior_auth_id,
            agent_name=self.agent_name,
            status="running",
            input_data=context.model_dump(),
            model_used=self.model,
        )
        self.db.add(execution)
        await self.db.flush()

        try:
            logger.info(
                "agent.started",
                agent=self.agent_name,
                prior_auth_id=context.prior_auth_id,
            )
            result = await self.execute(context)

            elapsed_ms = int((time.time() - start_time) * 1000)
            execution.status = "completed" if result.success else "failed"
            execution.completed_at = datetime.now(timezone.utc)
            execution.duration_ms = elapsed_ms
            execution.output_data = result.model_dump()
            execution.tokens_input = result.tokens_input
            execution.tokens_output = result.tokens_output
            execution.error_message = result.error

            logger.info(
                "agent.completed",
                agent=self.agent_name,
                success=result.success,
                duration_ms=elapsed_ms,
                tokens=result.tokens_input + result.tokens_output,
            )

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            execution.status = "error"
            execution.completed_at = datetime.now(timezone.utc)
            execution.duration_ms = elapsed_ms
            execution.error_message = str(e)

            logger.error(
                "agent.error",
                agent=self.agent_name,
                error=str(e),
                prior_auth_id=context.prior_auth_id,
            )
            result = AgentResult(success=False, error=str(e))

        await self.db.commit()
        return result

    async def mark_simulated(self, prior_auth_id: str) -> None:
        """Flag a PA as containing simulated data written by this agent."""
        from app.models.prior_auth import PriorAuth

        pa = await self.db.get(PriorAuth, prior_auth_id)
        if not pa:
            return
        pa.is_simulated = True
        agents = list(pa.simulated_agents or [])
        if self.agent_name not in agents:
            agents.append(self.agent_name)
        pa.simulated_agents = agents

    @retry(
        retry=retry_if_exception(_is_retryable_claude_error),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        stop=stop_after_attempt(4),
        before_sleep=_log_claude_retry,
        reraise=True,
    )
    async def call_claude(
        self,
        messages: list[dict],
        system: str | None = None,
        tools: list[dict] | None = None,
        max_tokens: int | None = None,
    ) -> anthropic.types.Message:
        """
        Standardized Claude API call. Retries on transient failures (429 rate
        limit, 529 overloaded, connection/timeout) with exponential backoff up
        to 4 attempts; other errors propagate immediately.
        Returns the raw Anthropic Message object.
        """
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens or self.max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools

        response = await self.client.messages.create(**kwargs)
        return response

    async def call_claude_text(
        self,
        user_message: str,
        system: str | None = None,
    ) -> tuple[str, int, int]:
        """
        Simple text-in, text-out Claude call.
        Returns (response_text, input_tokens, output_tokens).
        """
        response = await self.call_claude(
            messages=[{"role": "user", "content": user_message}],
            system=system or self.get_system_prompt(),
        )
        text = response.content[0].text
        return text, response.usage.input_tokens, response.usage.output_tokens

    async def call_claude_json(
        self,
        user_message: str,
        system: str | None = None,
        schema: type[BaseModel] | None = None,
        max_parse_attempts: int = 2,
    ) -> tuple[dict, int, int]:
        """
        Claude call expecting a JSON object.

        Retries up to max_parse_attempts times if the model returns something
        that isn't a valid JSON object (or, when schema is given, doesn't
        validate against it) — a separate concern from call_claude's transient
        network retries. Always returns a dict so callers' .get() is safe; when
        schema is provided the dict is the validated model's dump.

        Returns (parsed_dict, input_tokens, output_tokens) with token counts
        summed across attempts.
        """
        import json

        from pydantic import ValidationError

        prompt = system or self.get_system_prompt()
        prompt += "\n\nRespond ONLY with valid JSON. No markdown, no explanation."

        total_in = total_out = 0
        last_error: Exception | None = None

        for attempt in range(1, max_parse_attempts + 1):
            response = await self.call_claude(
                messages=[{"role": "user", "content": user_message}],
                system=prompt,
            )
            total_in += response.usage.input_tokens
            total_out += response.usage.output_tokens
            text = _strip_json_fence(response.content[0].text)

            try:
                parsed = json.loads(text)
            except (json.JSONDecodeError, ValueError) as e:
                last_error = e
                logger.warning(
                    "claude_json.parse_failed",
                    agent=self.agent_name,
                    attempt=attempt,
                    error=str(e),
                )
                continue

            if not isinstance(parsed, dict):
                last_error = ValueError(f"Expected JSON object, got {type(parsed).__name__}")
                logger.warning(
                    "claude_json.not_an_object",
                    agent=self.agent_name,
                    attempt=attempt,
                    got=type(parsed).__name__,
                )
                continue

            if schema is not None:
                try:
                    parsed = schema.model_validate(parsed).model_dump()
                except ValidationError as e:
                    last_error = e
                    logger.warning(
                        "claude_json.schema_invalid",
                        agent=self.agent_name,
                        attempt=attempt,
                        error=str(e),
                    )
                    continue

            return parsed, total_in, total_out

        raise ClaudeJSONError(
            f"Claude did not return valid JSON after {max_parse_attempts} attempts: {last_error}"
        )
