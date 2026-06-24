"""Local queue adapter using ElasticMQ (SQS-compatible).

All boto3 calls are wrapped in asyncio.to_thread() to prevent blocking
the event loop when multiple agents share the same loop.
"""

import asyncio
import json
import logging
from typing import Any

import boto3
from botocore.config import Config

from order_shared.adapters.base import QueueAdapter, QueueMessage

logger = logging.getLogger(__name__)


class ElasticMQAdapter(QueueAdapter):
    """Queue adapter backed by ElasticMQ (local SQS-compatible service)."""

    def __init__(self, endpoint_url: str, region: str = "us-east-1") -> None:
        self._client = boto3.client(
            "sqs",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id="local",
            aws_secret_access_key="local",
            config=Config(retries={"max_attempts": 3}),
        )
        self._queue_url_cache: dict[str, str] = {}

    def _get_queue_url(self, queue_name: str) -> str:
        if queue_name not in self._queue_url_cache:
            response = self._client.get_queue_url(QueueName=queue_name)
            self._queue_url_cache[queue_name] = response["QueueUrl"]
        return self._queue_url_cache[queue_name]

    async def publish_message(
        self,
        queue_name: str,
        body: dict[str, Any],
        delay_seconds: int = 0,
        message_attributes: dict[str, str] | None = None,
    ) -> str:
        def _send() -> str:
            queue_url = self._get_queue_url(queue_name)
            kwargs: dict[str, Any] = {
                "QueueUrl": queue_url,
                "MessageBody": json.dumps(body),
                "DelaySeconds": delay_seconds,
            }
            if message_attributes:
                kwargs["MessageAttributes"] = {
                    k: {"DataType": "String", "StringValue": v}
                    for k, v in message_attributes.items()
                }
            response = self._client.send_message(**kwargs)
            return response["MessageId"]

        message_id = await asyncio.to_thread(_send)
        logger.info(f"Published message to {queue_name}: {message_id}")
        return message_id

    async def consume_messages(
        self,
        queue_name: str,
        max_messages: int = 1,
        wait_time_seconds: int = 5,
    ) -> list[QueueMessage]:
        def _receive() -> list[QueueMessage]:
            queue_url = self._get_queue_url(queue_name)
            response = self._client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=min(max_messages, 10),
                WaitTimeSeconds=wait_time_seconds,
                AttributeNames=["All"],
            )
            messages = []
            for msg in response.get("Messages", []):
                messages.append(
                    QueueMessage(
                        body=json.loads(msg["Body"]),
                        message_id=msg["MessageId"],
                        receipt_handle=msg["ReceiptHandle"],
                        attributes=msg.get("Attributes", {}),
                    )
                )
            return messages

        return await asyncio.to_thread(_receive)

    async def delete_message(self, queue_name: str, receipt_handle: str) -> None:
        def _delete() -> None:
            queue_url = self._get_queue_url(queue_name)
            self._client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)

        await asyncio.to_thread(_delete)

    async def change_visibility(
        self, queue_name: str, receipt_handle: str, visibility_timeout: int
    ) -> None:
        def _change() -> None:
            queue_url = self._get_queue_url(queue_name)
            self._client.change_message_visibility(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle,
                VisibilityTimeout=visibility_timeout,
            )

        await asyncio.to_thread(_change)
