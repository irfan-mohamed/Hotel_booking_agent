"""
Application configuration module.

Provides a ``settings`` object that can be imported throughout the project.
The tests expect ``from app.config import settings`` to succeed.

Only a minimal set of configuration values required for the test suite are
implemented.  Additional settings can be added later without affecting the
current functionality.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os

@dataclass
class Settings:
    """
    Simple settings container.

    The project primarily uses a database URL.  For the test environment we
    default to an in‑memory SQLite database, which requires no external
    services.
    """
    # Database connection URL.  Can be overridden via the ``DATABASE_URL``
    # environment variable.
    database_url: str = field(default_factory=lambda: os.getenv(
        "DATABASE_URL", "sqlite:///./test.db"
    ))

    # Additional configuration placeholders can be added here.
    # Example:
    # debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")

    def __post_init__(self) -> None:
        # Ensure the path for a SQLite file exists when using a file‑based DB.
        if self.database_url.startswith("sqlite:///"):
            # Extract the file path after the scheme.
            path_str = self.database_url.replace("sqlite:///", "", 1)
            path = Path(path_str)
            if not path.parent.exists():
                try:
                    path.parent.mkdir(parents=True, exist_ok=True)
                except Exception:
                    # Silently ignore errors; the database engine will raise
                    # appropriate exceptions if the path is invalid.
                    pass


# Export a singleton instance that can be imported elsewhere.
settings = Settings()

__all__ = ["settings", "Settings"]
"""
Custom exception definitions for the application.

The test suite requires an ``InvalidEmailError`` that is raised when a guest
email fails validation.  It should inherit from ``ValueError`` (or a project‑wide
base exception if one exists).  For simplicity and broad compatibility we
inherit directly from ``ValueError``.
"""

class InvalidEmailError(ValueError):
    """
    Raised when an email address does not meet validation criteria.
    """

    def __init__(self, email: str | None = None, message: str | None = None):
        default_msg = "Invalid email address provided."
        if email:
            default_msg = f"Invalid email address: {email}"
        super().__init__(message or default_msg)

    # No additional behaviour is required; the class exists primarily for
    # explicit exception handling in the codebase and tests.

# Export the exception for convenient imports.
__all__ = ["InvalidEmailError"]