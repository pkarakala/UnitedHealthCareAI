import uuid
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone

import anthropic
import structlog
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.agent_execution import AgentExecution

logger = structlog.get_logger()


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

    async def call_claude(
        self,
        messages: list[dict],
        system: str | None = None,
        tools: list[dict] | None = None,
        max_tokens: int | None = None,
    ) -> anthropic.types.Message:
        """
        Standardized Claude API call with retry logic.
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
    ) -> tuple[dict, int, int]:
        """
        Claude call expecting JSON output. Parses the response.
        Returns (parsed_dict, input_tokens, output_tokens).
        """
        import json

        prompt = system or self.get_system_prompt()
        prompt += "\n\nRespond ONLY with valid JSON. No markdown, no explanation."

        response = await self.call_claude(
            messages=[{"role": "user", "content": user_message}],
            system=prompt,
        )
        text = response.content[0].text

        # Handle potential markdown wrapping
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]

        parsed = json.loads(text)
        return parsed, response.usage.input_tokens, response.usage.output_tokens
