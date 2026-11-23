"""
Application configuration module.

Provides a ``settings`` instance that can be imported throughout the project.
The implementation uses Pydantic's ``BaseSettings`` to allow environment variable
overrides while supplying sensible defaults for the test environment.
"""

from __future__ import annotations

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """
    Configuration settings for the application.

    Only a minimal subset of settings required for the test suite is defined
    here. Additional settings can be added as the application grows.
    """

    # Database connection URL. Default to an in‑memory SQLite database which works
    # for unit tests without requiring external services.
    DATABASE_URL: str = Field(
        default="sqlite:///./test.db",
        description="SQLAlchemy database URL",
    )

    # Example placeholder for other possible settings (e.g., API keys). They are
    # optional and default to empty strings so that imports succeed even if the
    # environment does not provide them.
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Export a singleton instance that can be imported as ``from app.config import settings``.
settings = Settings()

"""
Utility for validating email addresses.

The ``validate_email`` function attempts to use the third‑party ``email_validator``
package when it is available. If the package is not installed, it falls back to a
simple regular‑expression based validation. The function returns ``True`` for a
valid email address and ``False`` otherwise.
"""

from __future__ import annotations

import re
from typing import Any


def _simple_validate(email: str) -> bool:
    """
    Very basic email validation using a regular expression.

    This regex checks for the presence of exactly one ``@`` symbol and at least
    one ``.`` in the domain part, while disallowing whitespace characters.
    It is not exhaustive but sufficient as a fallback when the external
    ``email_validator`` library is unavailable.
    """
    pattern = r"^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$"
    return re.match(pattern, email) is not None


def validate_email(email: str) -> bool:
    """
    Validate an email address.

    Parameters
    ----------
    email: str
        The email address to validate.

    Returns
    -------
    bool
        ``True`` if the email address is considered valid, ``False`` otherwise.
    """
    try:
        # Attempt to use the robust third‑party validator if it is installed.
        from email_validator import EmailNotValidError, validate_email as ev_validate

        ev_validate(email)  # Will raise EmailNotValidError if invalid.
        return True
    except ImportError:
        # ``email_validator`` is not installed; fall back to simple regex.
        return _simple_validate(email)
    except EmailNotValidError:
        # The email failed validation according to ``email_validator``.
        return False
    except Exception:
        # Guard against any unexpected errors from the validator.
        return False