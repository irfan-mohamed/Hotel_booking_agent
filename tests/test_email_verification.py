import pytest
from unittest.mock import patch
from datetime import datetime, timedelta

# Assuming the project uses Django ORM; adjust imports if using another ORM.
from app.models import Guest, EmailVerificationToken, Booking, EmailNotVerifiedError
from app.services.email_verification import (
    generate_email_verification_token,
    verify_email_token,
)
from app.services.booking import create_booking


@pytest.fixture
def guest(db):
    """Create a guest with an unverified email."""
    return Guest.objects.create(email="test@example.com", is_email_verified=False)


def test_token_generation_creates_record_and_sends_email(guest):
    """
    generate_email_verification_token should:
    - create a EmailVerificationToken DB record linked to the guest
    - trigger an email send (we mock the email sending function)
    """
    with patch("app.services.email_verification.send_verification_email") as mock_send:
        token_str = generate_email_verification_token(guest)

    # Verify a token record exists
    token_obj = EmailVerificationToken.objects.filter(guest=guest, token=token_str).first()
    assert token_obj is not None, "Token record was not created in the DB"
    # The token should not be expired immediately after creation
    assert token_obj.expires_at > datetime.utcnow()

    # Verify that the email sending function was called once with correct args
    mock_send.assert_called_once_with(guest.email, token_str)


def test_verifying_valid_token_updates_guest(guest):
    """
    verify_email_token should mark the guest as verified when a valid token is supplied.
    """
    token_str = generate_email_verification_token(guest)

    # Ensure guest is initially unverified
    guest.refresh_from_db()
    assert not guest.is_email_verified

    # Verify the token
    verified_guest = verify_email_token(token_str)

    # The returned guest should be the same instance and now verified
    assert verified_guest.id == guest.id
    verified_guest.refresh_from_db()
    assert verified_guest.is_email_verified

    # The token should be marked as used / deleted
    assert not EmailVerificationToken.objects.filter(token=token_str).exists()


def test_verifying_expired_or_wrong_token_raises_error(guest):
    """
    verify_email_token should raise a ValueError (or custom) when token is invalid or expired.
    """
    # Create a token and manually expire it
    token_str = generate_email_verification_token(guest)
    token_obj = EmailVerificationToken.objects.get(token=token_str)
    token_obj.expires_at = datetime.utcnow() - timedelta(hours=1)
    token_obj.save()

    # Wrong token
    with pytest.raises(ValueError):
        verify_email_token("nonexistent-token")

    # Expired token
    with pytest.raises(ValueError):
        verify_email_token(token_str)


def test_booking_with_unverified_email_raises_error(guest):
    """
    Creating a booking for a guest whose email is not verified should raise EmailNotVerifiedError.
    """
    # Ensure the guest is still unverified
    guest.refresh_from_db()
    assert not guest.is_email_verified

    with pytest.raises(EmailNotVerifiedError):
        create_booking(guest=guest, room_id=1, start_date=datetime.utcnow(), end_date=datetime.utcnow() + timedelta(days=1))

    # After verification, booking should succeed
    token_str = generate_email_verification_token(guest)
    verify_email_token(token_str)

    # No exception should be raised now
    booking = create_booking(guest=guest, room_id=1, start_date=datetime.utcnow(), end_date=datetime.utcnow() + timedelta(days=1))
    assert isinstance(booking, Booking)