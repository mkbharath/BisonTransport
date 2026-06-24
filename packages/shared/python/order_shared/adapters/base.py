"""Abstract base classes for all infrastructure adapters.

Agent code depends ONLY on these interfaces. Concrete implementations
are injected at startup based on ADAPTER_MODE environment variable.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


# --- Data Classes ---


@dataclass
class QueueMessage:
    """Envelope for messages consumed from or published to a queue."""

    body: dict[str, Any]
    message_id: str | None = None
    receipt_handle: str | None = None
    attributes: dict[str, str] = field(default_factory=dict)


@dataclass
class StorageFile:
    """Metadata about a file in object storage."""

    key: str
    bucket: str
    content_type: str | None = None
    size_bytes: int | None = None


@dataclass
class EmailMessage:
    """Outbound email message."""

    to: str
    subject: str
    body_html: str
    body_text: str
    from_address: str | None = None
    reply_to: str | None = None
    in_reply_to: str | None = None
    references: list[str] = field(default_factory=list)
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)


@dataclass
class LLMResponse:
    """Response from an LLM completion call."""

    content: str
    model: str
    input_tokens: int
    output_tokens: int
    stop_reason: str | None = None


@dataclass
class OCRResult:
    """Result from OCR text extraction."""

    text: str
    confidence: float  # 0-100
    pages: list[dict[str, Any]] = field(default_factory=list)
    tables: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Event:
    """Event to publish to the event bus."""

    source: str
    detail_type: str
    detail: dict[str, Any]


# --- Abstract Adapters ---


class QueueAdapter(ABC):
    """Abstract interface for message queue operations (SQS / ElasticMQ)."""

    @abstractmethod
    async def publish_message(
        self,
        queue_name: str,
        body: dict[str, Any],
        delay_seconds: int = 0,
        message_attributes: dict[str, str] | None = None,
    ) -> str:
        """Publish a message to a queue. Returns the message ID."""
        ...

    @abstractmethod
    async def consume_messages(
        self,
        queue_name: str,
        max_messages: int = 1,
        wait_time_seconds: int = 5,
    ) -> list[QueueMessage]:
        """Long-poll for messages from a queue."""
        ...

    @abstractmethod
    async def delete_message(self, queue_name: str, receipt_handle: str) -> None:
        """Delete a message after successful processing."""
        ...

    @abstractmethod
    async def change_visibility(
        self, queue_name: str, receipt_handle: str, visibility_timeout: int
    ) -> None:
        """Extend or reduce the visibility timeout of a message."""
        ...


class StorageAdapter(ABC):
    """Abstract interface for object storage operations (S3 / MinIO)."""

    @abstractmethod
    async def upload_file(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> StorageFile:
        """Upload a file to storage. Returns file metadata."""
        ...

    @abstractmethod
    async def download_file(self, bucket: str, key: str) -> bytes:
        """Download a file from storage. Returns file content as bytes."""
        ...

    @abstractmethod
    async def get_presigned_url(
        self, bucket: str, key: str, expires_in: int = 900
    ) -> str:
        """Generate a presigned download URL (default 15-minute expiry)."""
        ...

    @abstractmethod
    async def file_exists(self, bucket: str, key: str) -> bool:
        """Check if a file exists in storage."""
        ...

    @abstractmethod
    async def delete_file(self, bucket: str, key: str) -> None:
        """Delete a file from storage."""
        ...


class EmailSender(ABC):
    """Abstract interface for sending outbound emails (SES / MailHog SMTP)."""

    @abstractmethod
    async def send_email(self, message: EmailMessage) -> str:
        """Send an email. Returns the message ID."""
        ...


class LLMAdapter(ABC):
    """Abstract interface for LLM completions (Anthropic API / Bedrock / OpenAI)."""

    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        model: str | None = None,
        temperature: float = 0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send a completion request to the LLM. Returns structured response."""
        ...

    @abstractmethod
    async def classify(
        self,
        text: str,
        categories: list[str],
        system: str | None = None,
    ) -> tuple[str, float]:
        """Classify text into one of the given categories.
        Returns (category, confidence_score_0_to_100).
        """
        ...


class OCRAdapter(ABC):
    """Abstract interface for OCR / document text extraction (Textract / pytesseract)."""

    @abstractmethod
    async def extract_text(self, file_bytes: bytes, file_type: str) -> OCRResult:
        """Extract text from an image or scanned PDF.
        file_type: 'png' | 'jpg' | 'tiff' | 'bmp' | 'pdf'
        """
        ...

    @abstractmethod
    async def extract_tables(self, file_bytes: bytes, file_type: str) -> list[dict[str, Any]]:
        """Extract structured tables from a document.
        Returns a list of tables, each as a list of row dicts.
        """
        ...


class EventBusAdapter(ABC):
    """Abstract interface for event publishing (EventBridge / local pub/sub)."""

    @abstractmethod
    async def publish_event(self, event: Event) -> str:
        """Publish an event. Returns the event ID."""
        ...

    @abstractmethod
    async def subscribe(
        self, detail_type: str, callback: Any
    ) -> None:
        """Subscribe to events of a given type (local mode only; no-op in AWS)."""
        ...
