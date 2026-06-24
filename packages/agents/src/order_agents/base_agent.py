"""Base class for all AI agents in the pipeline."""

import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from typing import Any

from order_shared.adapters import get_adapters
from order_shared.adapters.base import QueueMessage
from order_shared.db.session import async_session_factory
from order_shared.models.enums import AgentType
from order_shared.utils.logger import get_logger, set_log_context, clear_log_context


class BaseAgent(ABC):
    """Base class providing queue consumption loop and common infrastructure."""

    agent_type: AgentType
    input_queue: str

    def __init__(self) -> None:
        self.logger = get_logger(f"agent.{self.agent_type}")
        self._running = False

    @abstractmethod
    async def process_message(self, message: QueueMessage) -> None:
        """Process a single queue message. Implemented by each agent."""
        ...

    async def run(self) -> None:
        """Main loop: poll queue, process messages, delete on success."""
        self._running = True
        adapters = get_adapters()
        self.logger.info(f"{self.agent_type} agent started, polling {self.input_queue}")

        while self._running:
            try:
                messages = await adapters.queue.consume_messages(
                    queue_name=self.input_queue,
                    max_messages=1,
                    wait_time_seconds=5,
                )

                for msg in messages:
                    run_id = uuid.uuid4()
                    start_time = time.time()

                    set_log_context(
                        run_id=run_id,
                        email_id=msg.body.get("email_id"),
                        order_id=msg.body.get("order_id"),
                        agent_type=self.agent_type,
                    )

                    try:
                        self.logger.info(f"Processing message {msg.message_id}")
                        await self.process_message(msg)

                        # Delete message on success
                        if msg.receipt_handle:
                            await adapters.queue.delete_message(
                                self.input_queue, msg.receipt_handle
                            )

                        duration_ms = int((time.time() - start_time) * 1000)
                        self.logger.info(
                            f"Message processed successfully",
                            extra={"duration_ms": duration_ms, "status": "success"},
                        )

                        # Log execution to DB
                        await self._log_execution(
                            run_id=run_id,
                            email_id=msg.body.get("email_id"),
                            order_id=msg.body.get("order_id"),
                            action="process_message",
                            status="success",
                            duration_ms=duration_ms,
                        )

                    except Exception as e:
                        duration_ms = int((time.time() - start_time) * 1000)
                        self.logger.error(
                            f"Error processing message: {e}",
                            extra={"duration_ms": duration_ms, "status": "failure"},
                            exc_info=True,
                        )
                        await self._log_execution(
                            run_id=run_id,
                            email_id=msg.body.get("email_id"),
                            order_id=msg.body.get("order_id"),
                            action="process_message",
                            status="failure",
                            duration_ms=duration_ms,
                            error_detail=str(e),
                        )
                    finally:
                        clear_log_context()

            except Exception as e:
                self.logger.error(f"Queue polling error: {e}", exc_info=True)
                await asyncio.sleep(5)

    async def _log_execution(
        self,
        run_id: uuid.UUID,
        email_id: str | None,
        order_id: str | None,
        action: str,
        status: str,
        duration_ms: int,
        error_detail: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        llm_model: str | None = None,
    ) -> None:
        """Log agent execution to the database."""
        try:
            from sqlalchemy import text

            async with async_session_factory() as session:
                await session.execute(
                    text("""
                        INSERT INTO agent_execution_logs
                        (id, agent_type, run_id, email_id, order_id, action, status,
                         duration_ms, input_tokens, output_tokens, llm_model, error_detail, created_at)
                        VALUES (:id, :agent_type, :run_id, :email_id, :order_id, :action, :status,
                                :duration_ms, :input_tokens, :output_tokens, :llm_model, :error_detail, NOW())
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "agent_type": self.agent_type,
                        "run_id": str(run_id),
                        "email_id": email_id,
                        "order_id": order_id,
                        "action": action,
                        "status": status,
                        "duration_ms": duration_ms,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "llm_model": llm_model,
                        "error_detail": error_detail,
                    },
                )
                await session.commit()
        except Exception as e:
            self.logger.warning(f"Failed to log execution: {e}")

    def stop(self) -> None:
        """Stop the agent's polling loop."""
        self._running = False
