"""Repository for handling email verification tokens."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

# Adjust the import path according to the actual location of the model in the project.
# It is assumed that `EmailVerificationToken` is defined in `app.models.email_verification_token`.
from app.models.email_verification_token import EmailVerificationToken


class EmailVerificationRepository:
    """Encapsulates DB operations for :class:`EmailVerificationToken`."""

    def __init__(self, db_session: Session) -> None:
        """
        Initialise the repository with a SQLAlchemy session.

        Args:
            db_session: An active SQLAlchemy session/connection.
        """
        self._db = db_session

    def create_token(
        self,
        guest_id: int,
        token_hash: str,
        expires_at: datetime,
    ) -> EmailVerificationToken:
        """
        Create and persist a new email verification token.

        Args:
            guest_id: Identifier of the guest/user the token belongs to.
            token_hash: Hashed representation of the token.
            expires_at: Datetime when the token should expire.

        Returns:
            The newly created :class:`EmailVerificationToken` instance.
        """
        token = EmailVerificationToken(
            guest_id=guest_id,
            token_hash=token_hash,
            expires_at=expires_at,
            verified=False,
        )
        self._db.add(token)
        self._db.commit()
        self._db.refresh(token)
        return token

    def get_by_hash(self, token_hash: str) -> Optional[EmailVerificationToken]:
        """
        Retrieve a token by its hash.

        Args:
            token_hash: The hashed token string.

        Returns:
            The matching :class:`EmailVerificationToken` if found, otherwise ``None``.
        """
        return (
            self._db.query(EmailVerificationToken)
            .filter(EmailVerificationToken.token_hash == token_hash)
            .first()
        )

    def mark_verified(self, token: EmailVerificationToken) -> None:
        """
        Mark a token as verified and persist the change.

        Args:
            token: The token instance to mark as verified.
        """
        token.verified = True
        token.verified_at = datetime.utcnow()
        self._db.add(token)
        self._db.commit()
        # No return value; operation is performed in‑place.