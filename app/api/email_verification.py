from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Assuming EmailVerificationService is defined elsewhere in the project
try:
    from app.services.email_verification import EmailVerificationService
except ImportError:
    # Placeholder for the service if the import path differs
    EmailVerificationService = None

router = APIRouter()


class VerifyEmailRequest(BaseModel):
    token: str


@router.post("/verify-email")
async def verify_email(request: VerifyEmailRequest):
    """
    Verify an email using the provided token.
    Returns a success message on valid token, otherwise raises a 400 error.
    """
    if EmailVerificationService is None:
        raise HTTPException(status_code=500, detail="EmailVerificationService not configured")

    try:
        EmailVerificationService.verify_token(request.token)
    except Exception as exc:
        # The service should raise a specific exception for invalid/expired tokens;
        # we treat any exception as a bad request for simplicity.
        raise HTTPException(status_code=400, detail=str(exc))

    return {"detail": "Email verified successfully"}
from app.api.email_verification import router as email_verification_router

# Email verification endpoint
app.include_router(email_verification_router)