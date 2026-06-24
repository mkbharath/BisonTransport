"""Pluggable infrastructure adapters for the Order Intelligence Platform.

Adapter selection is controlled by the ADAPTER_MODE environment variable:
- "local": uses ElasticMQ, MinIO, MailHog, Anthropic API, pytesseract
- "aws": uses SQS, S3, SES, Bedrock, Textract
"""

from order_shared.adapters.base import (
    EmailSender,
    EventBusAdapter,
    LLMAdapter,
    OCRAdapter,
    QueueAdapter,
    StorageAdapter,
)
from order_shared.adapters.factory import create_adapters, get_adapters

__all__ = [
    "EmailSender",
    "EventBusAdapter",
    "LLMAdapter",
    "OCRAdapter",
    "QueueAdapter",
    "StorageAdapter",
    "create_adapters",
    "get_adapters",
]
