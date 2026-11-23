"""
Configuration module for the application.

Provides a ``settings`` instance that can be imported throughout the project.
The settings are based on ``pydantic.BaseSettings`` which reads values from
environment variables and an optional ``.env`` file. Default values are
provided to ensure the test suite can run without external configuration.
"""

from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    # Database connection string – default to an in‑memory SQLite database for tests.
    DATABASE_URL: str = "sqlite:///./test.db"

    # Email service configuration – sensible defaults for a local testing SMTP server.
    EMAIL_HOST: str = "localhost"
    EMAIL_PORT: int = 1025
    EMAIL_FROM: str = "noreply@example.com"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Export a singleton ``settings`` object that can be imported elsewhere.
settings = Settings()

__all__ = ["settings", "Settings"]
from app.repositories.booking_repository import BookingRepository
from app.exceptions import InvalidEmailError
from app.utils.email_validator import validate_email
from app.services.email_service import EmailService
from app.models.booking import Booking
class BookingTool:
    def __init__(self, repository: BookingRepository, email_service: EmailService):
        """
        Initialise the BookingTool with its required dependencies.

        :param repository: Repository handling persistence of bookings.
        :param email_service: Service responsible for sending email notifications.
        """
        self.repository = repository
        self.email_service = email_service
    def book(self, user_email: str, *args, **kwargs):
        """
        Create a new booking after validating the user's email address.

        :param user_email: Email address of the user making the booking.
        :return: The created ``Booking`` instance.
        :raises InvalidEmailError: If the provided email address is not valid.
        """
        if not validate_email(user_email):
            raise InvalidEmailError(f\"Invalid email: {user_email}\")
        booking: Booking = self.repository.create(user_email, *args, **kwargs)
        self.send_booking_confirmation(booking)
        return booking
    def send_booking_confirmation(self, booking: Booking) -> None:
        """
        Send a booking confirmation email using the injected ``EmailService``.

        :param booking: The ``Booking`` instance for which to send confirmation.
        """
        # The EmailService is expected to provide a ``send`` method that accepts
        # the recipient address, subject and body. Adjust as needed for the actual
        # service implementation.
        recipient = booking.user_email  # type: ignore[attr-defined]
        subject = "Your booking confirmation"
        body = f"Dear customer,\\n\\nYour booking (ID: {booking.id}) has been confirmed."
        self.email_service.send(to=recipient, subject=subject, body=body)