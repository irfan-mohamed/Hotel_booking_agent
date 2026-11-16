from sqlalchemy.orm import Session
from app.models import Guest, Booking, Reservation
from app.database import get_db
from app.config import Config
from app.services.email_service import EmailService
from app.exceptions import EmailNotVerifiedError
    # Obtain or create the guest
    guest = Guest.get_or_create(session, guest_data)

    # ------------------------------------------------------------------
    # Email verification enforcement
    # ------------------------------------------------------------------
    if not getattr(guest, "is_email_verified", False):
        # Generate a verification token
        token = guest.generate_email_verification_token(
            Config().EMAIL_VERIFICATION_TOKEN_SECRET,
            Config().EMAIL_VERIFICATION_TOKEN_EXPIRY_SECONDS,
        )
        # Send verification email
        EmailService().send_verification_email(guest, token)
        # Abort the booking flow – the transaction will be rolled back
        raise EmailNotVerifiedError(
            f"Email address for guest '{guest.email}' is not verified. "
            "A verification email has been sent."
        )


class EmailNotVerifiedError(Exception):
    """Raised when a guest attempts to make a booking without a verified email."""

    def __init__(self, message: str = "Guest email is not verified."):
        super().__init__(message)