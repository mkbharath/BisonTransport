"""Agent runner — starts all 6 agents as concurrent asyncio tasks.

Each agent runs in its own asyncio task. Blocking boto3 calls are
handled via asyncio.to_thread() in the queue adapter to prevent
one agent from blocking the event loop for others.

Usage: python -m order_agents.runner
"""

import asyncio
import signal
import sys
import traceback

from order_shared.adapters import create_adapters
from order_shared.utils.logger import get_logger

logger = get_logger("agent.runner")


async def run_agent_safe(agent) -> None:
    """Run an agent with automatic restart on crash."""
    while True:
        try:
            await agent.run()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(
                f"Agent {agent.agent_type} crashed: {e}\n{traceback.format_exc()}"
            )
            logger.info(f"Restarting {agent.agent_type} in 5 seconds...")
            await asyncio.sleep(5)


async def main() -> None:
    """Start all agents and run until interrupted."""
    logger.info("Initializing adapters...")
    create_adapters()

    # Import agents after adapter initialization
    from order_agents.email_intake.agent import EmailIntakeAgent
    from order_agents.document_understanding.agent import DocumentUnderstandingAgent
    from order_agents.order_extraction.agent import OrderExtractionAgent
    from order_agents.validation.agent import ValidationAgent
    from order_agents.communication.agent import CommunicationAgent
    from order_agents.order_creation.agent import OrderCreationAgent

    # Create agent instances
    agents = [
        EmailIntakeAgent(),
        DocumentUnderstandingAgent(),
        OrderExtractionAgent(),
        ValidationAgent(),
        CommunicationAgent(),
        OrderCreationAgent(),
    ]

    logger.info(f"Starting {len(agents)} agents...")

    # Create tasks with auto-restart wrapper
    tasks = [asyncio.create_task(run_agent_safe(agent)) for agent in agents]

    # Handle shutdown gracefully
    loop = asyncio.get_event_loop()

    def shutdown_handler() -> None:
        logger.info("Shutdown signal received, stopping agents...")
        for agent in agents:
            agent.stop()
        for task in tasks:
            task.cancel()

    loop.add_signal_handler(signal.SIGINT, shutdown_handler)
    loop.add_signal_handler(signal.SIGTERM, shutdown_handler)

    logger.info("All agents running. Press Ctrl+C to stop.")

    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logger.error(f"Agent runner error: {e}")
    finally:
        logger.info("Agent runner stopped.")


if __name__ == "__main__":
    asyncio.run(main())
