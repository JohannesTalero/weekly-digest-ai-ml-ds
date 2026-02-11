"""Puerto para envío de email (RF-01, RF-14, RF-15)."""

from typing import Protocol


class EmailPort(Protocol):
    """Contrato para enviar el digest por email."""

    def send(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: str | None = None,
    ) -> None:
        """Envía un email al destinatario con el asunto y cuerpo indicados."""
        ...
