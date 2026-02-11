"""Adaptador de email vía SendGrid (RF-01, RF-14, RNF-08, RNF-09)."""

import os
from datetime import datetime

from digest.domain.llm_port import ItemWithSummary

from digest.adapters.email_templates import render_digest_html, render_digest_text


def _default_subject() -> str:
    return f"Digest AI/ML/DS – {datetime.utcnow().strftime('%Y-%m-%d')}"


class SendGridEmail:
    """Implementación del puerto de email usando SendGrid. API key desde SENDGRID_API_KEY."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        from_email: str | None = None,
    ) -> None:
        self._api_key = api_key or os.environ.get("SENDGRID_API_KEY")
        self._from_email = from_email or os.environ.get("DIGEST_EMAIL_FROM")
        if not self._api_key:
            raise ValueError("SENDGRID_API_KEY no está definida")
        if not self._from_email:
            raise ValueError("DIGEST_EMAIL_FROM no está definida (remitente del digest)")

    def send(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: str | None = None,
    ) -> None:
        """Envía el email vía API de SendGrid."""
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        message = Mail(
            from_email=self._from_email,
            to_emails=to,
            subject=subject,
            html_content=body_html,
            plain_text_content=body_text or body_html.replace("<br>", "\n").replace("</li>", "\n"),
        )
        client = SendGridAPIClient(self._api_key)
        client.send(message)


def build_and_send_digest(
    email_adapter: SendGridEmail,
    items: list[ItemWithSummary],
    to: str,
    subject: str | None = None,
) -> None:
    """Genera cuerpo HTML y texto, y envía el email con los ítems del digest."""
    body_html = render_digest_html(items)
    body_text = render_digest_text(items)
    email_adapter.send(
        to=to,
        subject=subject or _default_subject(),
        body_html=body_html,
        body_text=body_text,
    )
