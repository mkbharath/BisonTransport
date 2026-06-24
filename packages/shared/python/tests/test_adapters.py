"""Tests for adapter factory and base interfaces."""

import os
from unittest.mock import patch

import pytest

from order_shared.adapters.base import (
    EmailMessage,
    Event,
    LLMResponse,
    OCRResult,
    QueueMessage,
    StorageFile,
)
from order_shared.adapters.factory import create_adapters, _create_local_adapters


class TestDataClasses:
    """Test adapter data classes are properly structured."""

    def test_queue_message(self) -> None:
        msg = QueueMessage(body={"email_id": "123"}, message_id="msg-1")
        assert msg.body == {"email_id": "123"}
        assert msg.message_id == "msg-1"
        assert msg.receipt_handle is None
        assert msg.attributes == {}

    def test_storage_file(self) -> None:
        f = StorageFile(key="attachments/2026/06/file.pdf", bucket="attachments")
        assert f.key == "attachments/2026/06/file.pdf"
        assert f.bucket == "attachments"
        assert f.content_type is None

    def test_email_message(self) -> None:
        msg = EmailMessage(
            to="customer@example.com",
            subject="Missing Information",
            body_html="<p>Hello</p>",
            body_text="Hello",
            in_reply_to="<original-msg-id@example.com>",
            references=["<original-msg-id@example.com>"],
        )
        assert msg.to == "customer@example.com"
        assert msg.in_reply_to == "<original-msg-id@example.com>"
        assert len(msg.references) == 1

    def test_llm_response(self) -> None:
        resp = LLMResponse(
            content='{"order": "data"}',
            model="claude-sonnet-4-20250514",
            input_tokens=1000,
            output_tokens=500,
            stop_reason="end_turn",
        )
        assert resp.input_tokens == 1000
        assert resp.output_tokens == 500

    def test_ocr_result(self) -> None:
        result = OCRResult(text="Order details here", confidence=87.5)
        assert result.confidence == 87.5
        assert result.pages == []
        assert result.tables == []

    def test_event(self) -> None:
        event = Event(
            source="order-creation-agent",
            detail_type="order.created",
            detail={"order_id": "uuid-123", "order_number": "ORD-20260615-00001"},
        )
        assert event.detail_type == "order.created"


class TestAdapterFactory:
    """Test adapter factory mode selection."""

    def test_unknown_mode_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown ADAPTER_MODE"):
            create_adapters(mode="invalid")

    def test_aws_mode_raises_not_implemented(self) -> None:
        with pytest.raises(NotImplementedError, match="AWS adapters not yet implemented"):
            create_adapters(mode="aws")

    @patch.dict(os.environ, {
        "ADAPTER_MODE": "local",
        "QUEUE_ENDPOINT_URL": "http://localhost:9324",
        "STORAGE_ENDPOINT_URL": "http://localhost:9000",
        "STORAGE_ACCESS_KEY": "minioadmin",
        "STORAGE_SECRET_KEY": "minioadmin",
        "SMTP_HOST": "localhost",
        "SMTP_PORT": "1025",
        "ANTHROPIC_API_KEY": "sk-ant-test-key",
        "LLM_MODEL_EXTRACTION": "claude-sonnet-4-20250514",
        "LLM_MODEL_CLASSIFICATION": "claude-3-5-haiku-20241022",
    })
    def test_local_mode_creates_all_adapters(self) -> None:
        from order_shared.adapters.local_queue import ElasticMQAdapter
        from order_shared.adapters.local_storage import MinIOStorageAdapter
        from order_shared.adapters.local_email import MailHogEmailSender
        from order_shared.adapters.local_llm import AnthropicLLMAdapter
        from order_shared.adapters.local_ocr import LocalOCRAdapter
        from order_shared.adapters.local_events import LocalEventBusAdapter

        adapters = create_adapters(mode="local")

        assert isinstance(adapters.queue, ElasticMQAdapter)
        assert isinstance(adapters.storage, MinIOStorageAdapter)
        assert isinstance(adapters.email, MailHogEmailSender)
        assert isinstance(adapters.llm, AnthropicLLMAdapter)
        assert isinstance(adapters.ocr, LocalOCRAdapter)
        assert isinstance(adapters.events, LocalEventBusAdapter)


class TestLocalEventBus:
    """Test local event bus pub/sub."""

    @pytest.mark.asyncio
    async def test_publish_event(self) -> None:
        from order_shared.adapters.local_events import LocalEventBusAdapter

        bus = LocalEventBusAdapter()
        event = Event(
            source="test",
            detail_type="order.created",
            detail={"order_id": "123"},
        )
        event_id = await bus.publish_event(event)
        assert event_id is not None
        assert len(bus.get_event_log()) == 1

    @pytest.mark.asyncio
    async def test_subscribe_and_receive(self) -> None:
        from order_shared.adapters.local_events import LocalEventBusAdapter
        import asyncio

        bus = LocalEventBusAdapter()
        received_events: list[Event] = []

        async def handler(event: Event) -> None:
            received_events.append(event)

        await bus.subscribe("order.created", handler)

        event = Event(
            source="test",
            detail_type="order.created",
            detail={"order_id": "456"},
        )
        await bus.publish_event(event)

        # Give the task a moment to execute
        await asyncio.sleep(0.1)
        assert len(received_events) == 1
        assert received_events[0].detail["order_id"] == "456"
