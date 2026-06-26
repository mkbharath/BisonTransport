"""Microsoft 365 Graph API email poller.

Polls the iltransport@ideyalabs.com mailbox via Microsoft Graph API
using OAuth 2.0 client credentials flow (app-only authentication).

Prerequisites:
1. Register an app in Azure AD (Entra ID)
2. Grant Mail.Read and Mail.ReadWrite application permissions
3. Admin consent granted
4. Set env vars: MSGRAPH_TENANT_ID, MSGRAPH_CLIENT_ID, MSGRAPH_CLIENT_SECRET
"""

import asyncio
import base64
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"


class MSGraphEmailPoller:
    """Polls a Microsoft 365 mailbox via Graph API."""

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
        self._token_expiry: datetime | None = None

    async def get_access_token(self) -> str:
        """Get or refresh OAuth2 access token using client credentials flow."""
        if self._access_token and self._token_expiry and datetime.now(timezone.utc) < self._token_expiry:
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
        # Token typically valid for 3600 seconds; refresh 5 min before expiry
        expires_in = data.get("expires_in", 3600)
        from datetime import timedelta
        self._token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 300)

        logger.info("MS Graph access token obtained")
        return self._access_token

    async def get_unread_emails(self, max_count: int = 10) -> list[dict[str, Any]]:
        """Fetch unread emails from the mailbox.

        Returns list of email dicts with: id, subject, from, receivedDateTime,
        body, hasAttachments, internetMessageId, conversationId
        """
        token = await self.get_access_token()
        url = (
            f"{GRAPH_BASE_URL}/users/{self._mailbox}/messages"
            f"?$filter=isRead eq false"
            f"&$top={max_count}"
            f"&$orderby=receivedDateTime asc"
            f"&$select=id,subject,from,toRecipients,receivedDateTime,"
            f"body,hasAttachments,internetMessageId,conversationId,"
            f"internetMessageHeaders"
        )

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
            )
            if response.status_code == 401:
                # Token expired, refresh and retry
                self._access_token = None
                token = await self.get_access_token()
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {token}"},
                )
            response.raise_for_status()

        data = response.json()
        return data.get("value", [])

    async def get_attachments(self, message_id: str) -> list[dict[str, Any]]:
        """Fetch all attachments for a specific email message.

        Returns list of attachment dicts with: id, name, contentType, size, contentBytes
        """
        token = await self.get_access_token()
        url = f"{GRAPH_BASE_URL}/users/{self._mailbox}/messages/{message_id}/attachments"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()

        data = response.json()
        attachments = []
        for att in data.get("value", []):
            if att.get("@odata.type") == "#microsoft.graph.fileAttachment":
                attachments.append({
                    "id": att["id"],
                    "name": att["name"],
                    "content_type": att.get("contentType", "application/octet-stream"),
                    "size": att.get("size", 0),
                    "content_bytes": base64.b64decode(att["contentBytes"]) if att.get("contentBytes") else b"",
                })
        return attachments

    async def mark_as_read(self, message_id: str) -> None:
        """Mark an email as read to prevent reprocessing."""
        token = await self.get_access_token()
        url = f"{GRAPH_BASE_URL}/users/{self._mailbox}/messages/{message_id}"

        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={"isRead": True},
            )
            response.raise_for_status()

    async def move_to_folder(self, message_id: str, folder_name: str = "Processed") -> None:
        """Move a processed email to a specific folder (optional)."""
        token = await self.get_access_token()

        # First, find or create the target folder
        folders_url = f"{GRAPH_BASE_URL}/users/{self._mailbox}/mailFolders"
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{folders_url}?$filter=displayName eq '{folder_name}'",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            folders = response.json().get("value", [])

            if folders:
                folder_id = folders[0]["id"]
            else:
                # Create the folder
                response = await client.post(
                    folders_url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json={"displayName": folder_name},
                )
                response.raise_for_status()
                folder_id = response.json()["id"]

            # Move the message
            move_url = f"{GRAPH_BASE_URL}/users/{self._mailbox}/messages/{message_id}/move"
            response = await client.post(
                move_url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={"destinationId": folder_id},
            )
            response.raise_for_status()

    def parse_email_record(self, graph_message: dict[str, Any]) -> dict[str, Any]:
        """Convert a Graph API message to our internal email record format."""
        from_info = graph_message.get("from", {}).get("emailAddress", {})
        to_recipients = graph_message.get("toRecipients", [])
        to_address = to_recipients[0]["emailAddress"]["address"] if to_recipients else self._mailbox

        body = graph_message.get("body", {})
        body_content = body.get("content", "")
        body_type = body.get("contentType", "text")

        # Extract thread ID from internetMessageHeaders
        headers = graph_message.get("internetMessageHeaders", [])
        thread_id = None
        in_reply_to = None
        for header in headers:
            if header.get("name", "").lower() == "in-reply-to":
                in_reply_to = header.get("value")
                thread_id = header.get("value")
            elif header.get("name", "").lower() == "references":
                if not thread_id:
                    refs = header.get("value", "").split()
                    thread_id = refs[0] if refs else None

        return {
            "graph_message_id": graph_message["id"],
            "message_id": graph_message.get("internetMessageId", f"<graph-{graph_message['id']}>"),
            "thread_id": thread_id or in_reply_to or graph_message.get("conversationId"),
            "from_address": from_info.get("address", "unknown@unknown.com"),
            "to_address": to_address,
            "subject": graph_message.get("subject", ""),
            "body_text": body_content if body_type == "text" else "",
            "body_html": body_content if body_type == "html" else "",
            "received_at": graph_message.get("receivedDateTime"),
            "has_attachments": graph_message.get("hasAttachments", False),
        }
