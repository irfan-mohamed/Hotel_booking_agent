"""
Configuration module for the application.

The test suite expects a ``settings`` object to be importable from
``app.config``.  Previously the module defined a ``Settings`` class but did
not instantiate it, causing ``ImportError`` when the tests attempted
``from app.config import settings``.

To resolve this, we define a ``Settings`` class inheriting from
``pydantic.BaseSettings`` with sensible defaults for the test environment
and expose a module‑level ``settings`` instance.
"""

from __future__ import annotations

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.

    The defaults are chosen to work in the isolated test environment
    without requiring external services.
    """

    # Database URL – using an in‑memory SQLite database for tests.
    DATABASE_URL: str = Field(
        default="sqlite:///./test.db",
        env="DATABASE_URL",
    )

    # Email service configuration – a dummy API key for tests.
    EMAIL_API_KEY: str = Field(
        default="test-api-key",
        env="EMAIL_API_KEY",
    )

    # Any additional configuration values can be added here.

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Export a singleton instance that can be imported by the rest of the
# application and the test suite.
settings = Settings()

__all__ = ["Settings", "settings"]
"""
Test fixtures for the project.

This fixture automatically patches ``EmailService.send_booking_confirmation``
with a ``MagicMock`` to prevent real network calls during tests.  The mock
is applied globally (``autouse=True``) so individual tests do not need to
explicitly request it.
"""

import pytest
from unittest.mock import MagicMock

# Import the EmailService class from the application code.
# The import path may need to be adjusted if the service resides elsewhere.
try:
    from app.services.email_service import EmailService
except ImportError:
    # Fallback import path – adjust according to actual project layout.
    from app.email_service import EmailService  # type: ignore


@pytest.fixture(autouse=True)
def mock_email_service(monkeypatch):
    """
    Replace ``EmailService.send_booking_confirmation`` with a ``MagicMock``.

    The mock is returned so tests can make assertions about calls if they
    wish to.
    """
    mock = MagicMock(name="send_booking_confirmation")
    monkeypatch.setattr(EmailService, "send_booking_confirmation", mock)
    return mock