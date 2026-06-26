"""Adapter factory — creates and manages adapter instances based on ADAPTER_MODE."""

import os
import logging
from dataclasses import dataclass

from order_shared.adapters.base import (
    EmailSender,
    EventBusAdapter,
    LLMAdapter,
    OCRAdapter,
    QueueAdapter,
    StorageAdapter,
)

logger = logging.getLogger(__name__)

# Singleton instance
_adapters: "Adapters | None" = None


@dataclass
class Adapters:
    """Container holding all infrastructure adapter instances."""

    queue: QueueAdapter
    storage: StorageAdapter
    email: EmailSender
    llm: LLMAdapter
    ocr: OCRAdapter
    events: EventBusAdapter


def create_adapters(mode: str | None = None) -> Adapters:
    """Create adapter instances based on the given mode.

    Args:
        mode: 'local' or 'aws'. Defaults to ADAPTER_MODE env var.

    Returns:
        Adapters dataclass with all infrastructure adapters configured.
    """
    global _adapters

    if mode is None:
        mode = os.environ.get("ADAPTER_MODE", "local")

    logger.info(f"Creating adapters in mode: {mode}")

    if mode == "local":
        _adapters = _create_local_adapters()
    elif mode == "aws":
        _adapters = _create_aws_adapters()
    else:
        raise ValueError(f"Unknown ADAPTER_MODE: {mode}. Use 'local' or 'aws'.")

    return _adapters


def get_adapters() -> Adapters:
    """Get the current adapter instances. Must call create_adapters() first."""
    global _adapters
    if _adapters is None:
        raise RuntimeError(
            "Adapters not initialized. Call create_adapters() at application startup."
        )
    return _adapters


def _create_local_adapters() -> Adapters:
    """Create local development adapters (ElasticMQ, MinIO, MailHog, Anthropic, pytesseract)."""
    from order_shared.adapters.local_queue import ElasticMQAdapter
    from order_shared.adapters.local_storage import MinIOStorageAdapter
    from order_shared.adapters.local_email import MailHogEmailSender
    from order_shared.adapters.local_llm import AnthropicLLMAdapter
    from order_shared.adapters.local_ocr import LocalOCRAdapter
    from order_shared.adapters.local_events import LocalEventBusAdapter

    queue = ElasticMQAdapter(
        endpoint_url=os.environ.get("QUEUE_ENDPOINT_URL", "http://localhost:9324"),
        region=os.environ.get("QUEUE_REGION", "us-east-1"),
    )

    storage = MinIOStorageAdapter(
        endpoint_url=os.environ.get("STORAGE_ENDPOINT_URL", "http://localhost:9000"),
        access_key=os.environ.get("STORAGE_ACCESS_KEY", "minioadmin"),
        secret_key=os.environ.get("STORAGE_SECRET_KEY", "minioadmin"),
        region=os.environ.get("STORAGE_REGION", "us-east-1"),
    )

    email_mode = os.environ.get("EMAIL_INTAKE_MODE", "file_watcher")

    if email_mode == "msgraph":
        from order_shared.adapters.msgraph_email import MSGraphEmailSender

        msgraph_tenant = os.environ.get("MSGRAPH_TENANT_ID", "")
        msgraph_client = os.environ.get("MSGRAPH_CLIENT_ID", "")
        msgraph_secret = os.environ.get("MSGRAPH_CLIENT_SECRET", "")
        msgraph_mailbox = os.environ.get("MSGRAPH_MAILBOX", "iltransport@ideyalabs.com")

        email = MSGraphEmailSender(
            tenant_id=msgraph_tenant,
            client_id=msgraph_client,
            client_secret=msgraph_secret,
            mailbox=msgraph_mailbox,
        )
    else:
        email = MailHogEmailSender(
            host=os.environ.get("SMTP_HOST", "localhost"),
            port=int(os.environ.get("SMTP_PORT", "1025")),
            default_from=os.environ.get("EMAIL_FROM_ADDRESS", "orders@orderplatform.local"),
        )

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    llm_provider = os.environ.get("LLM_PROVIDER", "anthropic")

    if llm_provider == "openai":
        from order_shared.adapters.local_llm_openai import OpenAILLMAdapter

        if not openai_key:
            logger.warning("OPENAI_API_KEY not set — LLM calls will fail")
        llm = OpenAILLMAdapter(
            api_key=openai_key,
            default_model=os.environ.get("LLM_MODEL_EXTRACTION", "gpt-4o"),
            classification_model=os.environ.get("LLM_MODEL_CLASSIFICATION", "gpt-4o-mini"),
        )
    else:
        if not anthropic_key:
            logger.warning("ANTHROPIC_API_KEY not set — LLM calls will fail")
        llm = AnthropicLLMAdapter(
            api_key=anthropic_key,
            default_model=os.environ.get("LLM_MODEL_EXTRACTION", "claude-sonnet-4-20250514"),
            classification_model=os.environ.get("LLM_MODEL_CLASSIFICATION", "claude-3-haiku-20240307"),
        )

    ocr = LocalOCRAdapter()

    events = LocalEventBusAdapter()

    return Adapters(
        queue=queue,
        storage=storage,
        email=email,
        llm=llm,
        ocr=ocr,
        events=events,
    )


def _create_aws_adapters() -> Adapters:
    """Create AWS production adapters (SQS, S3, SES, Bedrock, Textract, EventBridge).

    These will be implemented in Phase 1 when moving to AWS.
    For now, raises NotImplementedError to make it clear AWS mode requires Phase 1 work.
    """
    raise NotImplementedError(
        "AWS adapters not yet implemented. Complete Phase 1 (AWS Infrastructure) first. "
        "Use ADAPTER_MODE=local for local development."
    )
