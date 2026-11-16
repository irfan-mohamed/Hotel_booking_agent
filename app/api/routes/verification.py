import hashlib

from fastapi import APIRouter, HTTPException

# Adjust the import according to your project structure
from app.repositories import guest_repository

router = APIRouter()


@router.get("/verify-email")
def verify_email(token: str):
    """
    Verify a guest's email address using a verification token.
    """
    # Hash the incoming token using SHA‑256
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    # Retrieve the guest by the hashed token
    guest = guest_repository.get_by_verification_token(token_hash)

    if guest:
        # Mark the guest as verified
        guest_repository.verify_email(guest)
        return {"detail": "Email verified"}

    # Token not found or expired
    raise HTTPException(
        status_code=400,
        detail="Invalid or expired verification token",
    )

# Verification route import
from .routes.verification import router as verification_router
api_router.include_router(verification_router)