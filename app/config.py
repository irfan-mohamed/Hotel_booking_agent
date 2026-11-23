"""
Configuration module for the application.

The tests import ``settings`` from this module, expecting a ``Settings`` instance
that provides configuration values such as database connection strings and an
``EMAIL`` dictionary.  The original implementation was missing the ``settings``
object, causing import errors throughout the codebase.

This file now defines a ``Settings`` class using **pydantic**'s ``BaseSettings``
so that values can be overridden via environment variables while providing
reasonable defaults that allow the application to start without any external
services (e.g., an SMTP server).  An instance named ``settings`` is exported for
convenient import elsewhere in the project.
"""

from __future__ import annotations

from typing import Dict, Any

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """
    Application settings with sensible defaults.

    The fields defined here cover the minimal configuration required by the
    existing codebase and tests.  Additional settings can be added as the
    application evolves.
    """

    # --------------------------------------------------------------------- #
    # Core application settings
    # --------------------------------------------------------------------- #
    # Database URL – defaults to a local SQLite file suitable for testing.
    DATABASE_URL: str = Field(
        "sqlite:///./test.db",
        description="SQLAlchemy database URL. Override via env var DATABASE_URL.",
    )

    # --------------------------------------------------------------------- #
    # Email configuration – defaults are empty/disabled so the app can start
    # without a real SMTP server.
    # --------------------------------------------------------------------- #
    EMAIL: Dict[str, Any] = Field(
        default_factory=lambda: {
            "HOST": "",
            "PORT": 0,
            "USERNAME": "",
            "PASSWORD": "",
            "USE_TLS": False,
        },
        description="Email server configuration dictionary.",
    )

    # --------------------------------------------------------------------- #
    # Optional additional common settings (provide safe defaults)
    # --------------------------------------------------------------------- #
    SECRET_KEY: str = Field(
        "change-me-in-production",
        description="Secret key for cryptographic operations.",
    )
    ALGORITHM: str = Field(
        "HS256",
        description="JWT signing algorithm.",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        30,
        description="Default JWT expiration time in minutes.",
    )

    class Config:
        # Load variables from a .env file if present; this mirrors typical FastAPI
        # projects and keeps the behaviour flexible for developers.
        env_file = ".env"
        env_file_encoding = "utf-8"


# Export a singleton instance that can be imported throughout the project.
settings = Settings()