from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ----------------------------------------------------------------
    # PostgreSQL
    # ----------------------------------------------------------------
    postgres_db: str = "hotel_booking"
    postgres_user: str = "hotel_user"
    postgres_password: str = "hotel_password"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    # ----------------------------------------------------------------
    # Database URL
    # Defaults to PostgreSQL built from individual POSTGRES_* vars.
    # Override by setting DATABASE_URL explicitly in .env.
    # ----------------------------------------------------------------
    database_url: str = ""

    # ----------------------------------------------------------------
    # Test database
    # ----------------------------------------------------------------
    test_database_url: str = ""

    # ----------------------------------------------------------------
    # LLM
    # ----------------------------------------------------------------
    groq_api_key: str = ""
    groq_model: str = ""

    # ----------------------------------------------------------------
    # Application
    # ----------------------------------------------------------------
    app_env: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_database_url(self) -> str:
        """Return DATABASE_URL if set, otherwise build from POSTGRES_* vars."""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    def get_test_database_url(self) -> str:
        """Return TEST_DATABASE_URL if set, otherwise derive from main DB with _test suffix."""
        if self.test_database_url:
            return self.test_database_url
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}_test"
        )


settings = Settings()