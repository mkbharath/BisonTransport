"""Microsoft Graph API email sender adapter.

Sends outbound emails via Microsoft Graph API from iltransport@ideyalabs.com.
When in_reply_to is set, replies in the same thread with a custom subject.
"""

import logging
import time
from typing import Any

import httpx

from order_shared.adapters.base import EmailMessage, EmailSender

logger = logging.getLogger(__name__)

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"


class MSGraphEmailSender(EmailSender):
    """Sends emails via Microsoft Graph API, maintaining email threads."""

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        mailbox: str = "iltransport@ideyalabs.com",
    ) -> None:
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret
        self._mailbox = mailbox
        self._access_token: str | None = None
        self._token_expiry: float = 0

    async def _get_access_token(self) -> str:
        """Get or refresh OAuth2 access token."""
        if self._access_token and time.time() < self._token_expiry:
            return self._access_token

        token_url = f"https://login.microsoftonline.com/{self._tenant_id}/oauth2/v2.0/token"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "scope": "https://graph.microsoft.com/.default",
                    "grant_type": "client_credentials",
                },
            )
            response.raise_for_status()
            data = response.json()

        self._access_token = data["access_token"]
        self._token_expiry = time.time() + data.get("expires_in", 3600) - 300

        return self._access_token

    async def send_email(self, message: EmailMessage) -> str:
        """Send an email via Microsoft Graph API.

        If in_reply_to is set, replies in the same thread with custom subject.
        Otherwise sends a new email.
        """
        token = await self._get_access_token()

        # If replying to a message, use createReply → update subject → send
        if message.in_reply_to:
            result = await self._reply_in_thread(token, message)
            if result:
                return result

        # Fall back to sendMail (new email or reply failed)
        return await self._send_new(token, message)

    async def _reply_in_thread(self, token: str, message: EmailMessage) -> str | None:
        """Reply in the same thread with a custom subject.

        Uses createReply to get a draft, updates subject and body, then sends.
        """
        try:
            async with httpx.AsyncClient() as client:
                # Step 1: Find the original message by internetMessageId
                # Remove angle brackets for the filter if present
                search_msg_id = message.in_reply_to.strip("<>")
                search_url = (
                    f"{GRAPH_BASE_URL}/users/{self._mailbox}/messages"
                    f"?$filter=internetMessageId eq '<{search_msg_id}>'"
                    f"&$select=id,subject,conversationId"
                )

                logger.info(f"Searching for original message: {search_msg_id[:40]}...")

                response = await client.get(
                    search_url,
                    headers={"Authorization": f"Bearer {token}"},
                )

                if response.status_code != 200:
                    logger.warning(f"Search failed with status {response.status_code}: {response.text[:200]}")
                    return None

                data = response.json()
                messages = data.get("value", [])

                if not messages:
                    logger.warning(f"Original message not found in mailbox for: {search_msg_id[:40]}")
                    return None

                original_msg_id = messages[0]["id"]
                logger.info(f"Found original message: {original_msg_id[:20]}...")

                # Step 2: Create a reply draft
                create_reply_url = (
                    f"{GRAPH_BASE_URL}/users/{self._mailbox}/messages/{original_msg_id}/createReply"
                )

                response = await client.post(
                    create_reply_url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json={},
                )

                if response.status_code not in (200, 201):
                    logger.warning(f"createReply failed: {response.status_code}")
                    return None

                draft = response.json()
                draft_id = draft["id"]

                # Step 3: Update the draft with our custom subject and body
                # Keep the existing body (which contains quoted original) and prepend our content
                update_url = f"{GRAPH_BASE_URL}/users/{self._mailbox}/messages/{draft_id}"

                existing_body = draft.get("body", {}).get("content", "")
                our_content = message.body_html or message.body_text
                combined_body = f"{our_content}<br><hr>{existing_body}"

                # Don't change the subject — keep "Re: [original]" to maintain Outlook threading
                update_payload: dict[str, Any] = {
                    "body": {
                        "contentType": "HTML",
                        "content": combined_body,
                    },
                    "toRecipients": [
                        {"emailAddress": {"address": message.to}}
                    ],
                }

                response = await client.patch(
                    update_url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json=update_payload,
                )

                if response.status_code != 200:
                    logger.warning(f"Draft update failed: {response.status_code} {response.text[:200]}")
                    # Clean up draft
                    await client.delete(update_url, headers={"Authorization": f"Bearer {token}"})
                    return None

                # Step 4: Send the draft
                send_url = f"{GRAPH_BASE_URL}/users/{self._mailbox}/messages/{draft_id}/send"

                response = await client.post(
                    send_url,
                    headers={"Authorization": f"Bearer {token}"},
                )

                if response.status_code == 202:
                    logger.info(
                        f"Replied in thread to {message.to}: {message.subject} (original msg: {original_msg_id})"
                    )
                    return f"msgraph-reply-{message.to}"
                else:
                    logger.warning(f"Send draft failed: {response.status_code} {response.text[:200]}")
                    return None

        except Exception as e:
            logger.warning(f"Reply attempt failed: {e}, falling back to sendMail")
            return None

    async def _send_new(self, token: str, message: EmailMessage) -> str:
        """Send a new email via Graph sendMail endpoint."""
        graph_message: dict[str, Any] = {
            "subject": message.subject,
            "body": {
                "contentType": "HTML",
                "content": message.body_html or message.body_text,
            },
            "toRecipients": [
                {"emailAddress": {"address": message.to}}
            ],
        }

        if message.cc:
            graph_message["ccRecipients"] = [
                {"emailAddress": {"address": addr}} for addr in message.cc
            ]

        payload = {
            "message": graph_message,
            "saveToSentItems": "true",
        }

        url = f"{GRAPH_BASE_URL}/users/{self._mailbox}/sendMail"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

            if response.status_code == 401:
                self._access_token = None
                token = await self._get_access_token()
                response = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )

            if response.status_code not in (200, 202):
                logger.error(f"Graph sendMail failed: {response.status_code} {response.text}")
                response.raise_for_status()

        logger.info(f"Email sent via MS Graph to {message.to}: {message.subject}")
        return f"msgraph-sent-{message.to}"
