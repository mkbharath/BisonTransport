"""Local email sender adapter using MailHog (SMTP capture)."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from order_shared.adapters.base import EmailMessage, EmailSender

logger = logging.getLogger(__name__)


class MailHogEmailSender(EmailSender):
    """Email sender that routes through MailHog SMTP for local development.

    Emails are captured and viewable at http://localhost:8025
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 1025,
        default_from: str = "orders@orderplatform.local",
    ) -> None:
        self._host = host
        self._port = port
        self._default_from = default_from

    async def send_email(self, message: EmailMessage) -> str:
        msg = MIMEMultipart("alternative")
        msg["From"] = message.from_address or self._default_from
        msg["To"] = message.to
        msg["Subject"] = message.subject

        if message.reply_to:
            msg["Reply-To"] = message.reply_to
        if message.in_reply_to:
            msg["In-Reply-To"] = message.in_reply_to
        if message.references:
            msg["References"] = " ".join(message.references)
        if message.cc:
            msg["Cc"] = ", ".join(message.cc)

        # Attach plain text and HTML parts
        msg.attach(MIMEText(message.body_text, "plain"))
        msg.attach(MIMEText(message.body_html, "html"))

        # Collect all recipients
        recipients = [message.to]
        recipients.extend(message.cc)
        recipients.extend(message.bcc)

        # Send via SMTP (MailHog doesn't require auth or TLS)
        with smtplib.SMTP(self._host, self._port) as server:
            server.sendmail(
                from_addr=msg["From"],
                to_addrs=recipients,
                msg=msg.as_string(),
            )

        message_id = msg.get("Message-ID", f"local-{id(msg)}")
        logger.info(f"Email sent to {message.to}: {message.subject} (via MailHog)")
        return str(message_id)
