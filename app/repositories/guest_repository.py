from sqlalchemy.orm import Session
from app.models import Guest
from typing import Optional
from datetime import datetime

    def get_by_verification_token(self, token_hash: str) -> Optional[Guest]:
        """
        Retrieve a Guest whose email verification token matches ``token_hash`` and whose
        verification expiry timestamp is still in the future.
        """
        now = datetime.utcnow()
        return (
            self.session.query(Guest)
            .filter(
                Guest.email_verification_token == token_hash,
                Guest.email_verification_expires_at > now,
            )
            .first()
        )

    def verify_email(self, guest: Guest) -> None:
        """
        Mark the guest's email as verified and persist the change.
        """
        guest.mark_email_verified()
        self.session.commit()