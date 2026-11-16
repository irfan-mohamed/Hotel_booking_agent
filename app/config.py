    # Email SMTP configuration
    EMAIL_SMTP_HOST: str = os.getenv('EMAIL_SMTP_HOST')
    # Default SMTP port is 587 (TLS). Override via env if needed.
    EMAIL_SMTP_PORT: int = int(os.getenv('EMAIL_SMTP_PORT', '587'))
    EMAIL_USERNAME: str = os.getenv('EMAIL_USERNAME')
    EMAIL_PASSWORD: str = os.getenv('EMAIL_PASSWORD')
    EMAIL_FROM_ADDRESS: str = os.getenv('EMAIL_FROM_ADDRESS')

    # Token secret used for email verification links.
    # Falls back to the application's main secret key if not explicitly set.
    EMAIL_VERIFICATION_TOKEN_SECRET: str = os.getenv(
        'EMAIL_VERIFICATION_TOKEN_SECRET',
        getattr(Config, 'JWT_SECRET_KEY', None)  # type: ignore[attr-defined]
    )

    # Expiry time for email verification tokens (default: 24 hours).
    EMAIL_VERIFICATION_TOKEN_EXPIRY_SECONDS: int = int(
        os.getenv('EMAIL_VERIFICATION_TOKEN_EXPIRY_SECONDS', '86400')
    )

    @classmethod
    def validate_email_config(cls) -> None:
        """
        Validate that all required email configuration values are present.
        This method should be called by the email service before attempting
        to send any messages. It raises a RuntimeError with a clear message
        if any required setting is missing.
        """
        missing = []
        if not cls.EMAIL_SMTP_HOST:
            missing.append('EMAIL_SMTP_HOST')
        if not cls.EMAIL_USERNAME:
            missing.append('EMAIL_USERNAME')
        if not cls.EMAIL_PASSWORD:
            missing.append('EMAIL_PASSWORD')
        if not cls.EMAIL_FROM_ADDRESS:
            missing.append('EMAIL_FROM_ADDRESS')
        if missing:
            raise RuntimeError(
                f'Missing required email configuration variables: {', '.join(missing)}'
            )