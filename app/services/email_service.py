# Existing configuration code (if any) might be present here.

# The tests expect a ``settings`` object to be importable from ``app.config``.
# We provide a simple Pydantic ``BaseSettings`` implementation that reads
# environment variables (or falls back to sensible defaults) for the SMTP
# configuration used by ``EmailService`` and any other components that rely
# on configuration values.

from __future__ import annotations

import os
from typing import Any, Dict

try:
    # Pydantic is commonly used in FastAPI projects; if it is available we use it.
    from pydantic import BaseSettings, Field
except Exception:  # pragma: no cover
    # Fallback minimal implementation if pydantic is not installed.
    class BaseSettings:  # type: ignore[misc]
        def __init__(self, **kwargs: Any) -> None:
            for key, value in kwargs.items():
                setattr(self, key, value)

        @classmethod
        def __get_validators__(cls):
            return []

        @classmethod
        def parse_obj(cls, obj: Dict[str, Any]):  # pragma: no cover
            return cls(**obj)

        class Config:  # pragma: no cover
            env_prefix = ""
            case_sensitive = False

    # ``Field`` is a no‑op placeholder.
    def Field(default: Any = None, **kwargs: Any) -> Any:  # pragma: no cover
        return default


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Only the SMTP related settings are required for the EmailService
    implementation, but additional settings can be added here as the
    application grows.
    """

    smtp_host: str = Field(default=os.getenv("SMTP_HOST", ""), description="SMTP server hostname")
    smtp_port: int = Field(default=int(os.getenv("SMTP_PORT", "587")), description="SMTP server port")
    smtp_username: str = Field(default=os.getenv("SMTP_USERNAME", ""), description="SMTP authentication username")
    smtp_password: str = Field(default=os.getenv("SMTP_PASSWORD", ""), description="SMTP authentication password")
    smtp_use_tls: bool = Field(default=os.getenv("SMTP_USE_TLS", "true").lower() in {"true", "1", "yes"}, description="Whether to use STARTTLS")

    # Example placeholder for other configuration values that may exist in the
    # original project (e.g., database URLs). They are kept optional to avoid
    # breaking imports that might reference them elsewhere.
    database_url: str = Field(default=os.getenv("DATABASE_URL", ""), description="Database connection URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Export a singleton instance that can be imported throughout the project.
settings = Settings()

"""
Email service implementation.

Provides a simple ``EmailService`` class that can send a booking confirmation
email using SMTP configuration defined in ``app.config.settings``. In test
environments where SMTP settings are not provided, the service logs the email
content instead of attempting to send it.
"""

from __future__ import annotations

import logging
import smtplib
from datetime import date
from email.message import EmailMessage
from typing import Optional

from app.config import settings


class EmailService:
    """
    Service responsible for sending emails related to bookings.
    """

    def __init__(self) -> None:
        # Load SMTP configuration from the global ``settings`` instance.
        self.host: str = getattr(settings, "smtp_host", "")
        self.port: int = getattr(settings, "smtp_port", 0)
        self.username: str = getattr(settings, "smtp_username", "")
        self.password: str = getattr(settings, "smtp_password", "")
        self.use_tls: bool = getattr(settings, "smtp_use_tls", True)

    def _compose_message(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
    ) -> EmailMessage:
        """
        Helper to build an :class:`email.message.EmailMessage` instance.
        """
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["To"] = to_email
        msg["From"] = from_email or self.username or "no-reply@example.com"
        msg.set_content(body)
        return msg

    def send_booking_confirmation(
        self,
        to_email: str,
        booking_reference: str,
        guest_name: str,
        check_in: date,
        check_out: date,
    ) -> None:
        """
        Sends a plain‑text booking confirmation email.

        If SMTP configuration is missing (i.e., ``self.host`` is falsy), the
        email content is logged at INFO level instead of being sent.
        """
        subject = "Booking Confirmation"
        body = (
            f"Dear {guest_name},\n\n"
            f"Your booking (reference: {booking_reference}) has been confirmed.\n"
            f"Check‑in: {check_in.isoformat()}\n"
            f"Check‑out: {check_out.isoformat()}\n\n"
            "Thank you for choosing our service.\n"
        )

        # If SMTP host is not configured, fall back to logging.
        if not self.host:
            logging.info(
                "SMTP configuration missing – email not sent. "
                "To: %s | Subject: %s | Body: %s",
                to_email,
                subject,
                body,
            )
            return

        message = self._compose_message(to_email, subject, body)

        try:
            with smtplib.SMTP(self.host, self.port) as smtp:
                if self.use_tls:
                    smtp.starttls()
                if self.username and self.password:
                    smtp.login(self.username, self.password)
                smtp.send_message(message)
        except Exception as exc:  # pragma: no cover
            # Log the exception and re‑raise so that calling code can handle it.
            logging.error("Failed to send booking confirmation email: %s", exc)
            raise
