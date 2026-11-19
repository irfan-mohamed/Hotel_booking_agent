from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Adjust imports according to your project layout
from app.api.dependencies import get_db
from app.api.schemas.verification import EmailVerificationRequest, EmailVerificationResponse
from app.models import Booking

router = APIRouter(prefix="/verification", tags=["Verification"])


@router.post(
    "/verify-email",
    response_model=EmailVerificationResponse,
    status_code=status.HTTP_200_OK,
)
def verify_email(
    request: EmailVerificationRequest,
    db: Session = Depends(get_db),
):
    """
    Verify a booking's email address using a token.
    """
    booking = db.query(Booking).filter(Booking.id == request.booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Validate token presence
    if not booking.email_verification_token or not request.token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token is required",
        )

    # Check token match
    if booking.email_verification_token != request.token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )

    # Check expiration
    if (
        booking.email_verification_token_expires_at
        and booking.email_verification_token_expires_at < datetime.utcnow()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired",
        )

    # Mark as verified and clear token fields
    booking.is_verified = True
    booking.email_verification_token = None
    booking.email_verification_token_expires_at = None

    db.commit()
    db.refresh(booking)

    return EmailVerificationResponse(success=True)