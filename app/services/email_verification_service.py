import hashlib
import logging
import secrets
from datetime import datetime, timedelta

# Placeholder email sender – in real code this would integrate with an email provider.
def send_email(to: str, subject: str, body: str) -> None:
    """
    Log the email contents. This function stands in for a real email‑sending implementation.
    """
    logging.info("Sending email to %s | Subject: %s | Body: %s", to, subject, body)


class EmailVerificationService:
    """
    Service responsible for generating email‑verification tokens, persisting them,
    sending verification emails and validating tokens supplied by users.
    """

    # Token validity period – 24 hours by default.
    TOKEN_TTL = timedelta(hours=24)

    def __init__(self, token_repository, guest_repository):
        """
        Initialise the service with the required repositories.

        Args:
            token_repository: An object providing ``create(hash, guest_id, expires_at)``,
                               ``get_by_hash(hash)`` and ``delete(record)`` methods.
            guest_repository: An object providing ``get_by_id(id)`` and ``save(guest)`` methods.
        """
        self.token_repository = token_repository
        self.guest_repository = guest_repository

    def _hash_token(self, token: str) -> str:
        """Return a SHA‑256 hex digest of the supplied token."""
        return hashlib.sha256(token.encode()).hexdigest()

    def generate_and_send(self, guest) -> str:
        """
        Generate a secure token for the given guest, store its hash, and send a verification email.

        Args:
            guest: An instance of the Guest model (must have ``id`` and ``email`` attributes).

        Returns:
            The raw token string (so the caller can embed it in the email body).
        """
        raw_token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(raw_token)
        expires_at = datetime.utcnow() + self.TOKEN_TTL

        # Persist the hashed token.
        self.token_repository.create(
            token_hash=token_hash,
            guest_id=guest.id,
            expires_at=expires_at
        )

        # Compose and send the verification email.
        subject = "Please verify your email address"
        verification_link = f"https://example.com/verify-email?token={raw_token}"
        body = (
            f"Hi {guest.name or ''},\\n\\n"
            "Thank you for registering. Please verify your email address by clicking the link below:\\n"
            f"{verification_link}\\n\\n"
            "If you did not sign up, you can ignore this email.\\n\\n"
            "Best regards,\\nThe Team"
        )
        send_email(to=guest.email, subject=subject, body=body)\n+\n+        return raw_token\n+\n+    def verify_token(self, raw_token: str):\n+        \"\"\"Validate a token and mark the associated guest as email‑verified.\n+\n+        Args:\n+            raw_token: The token string supplied by the user (e.g., from a query parameter).\n+\n+        Returns:\n+            The Guest instance whose email has been verified.\n+\n+        Raises:\n+            ValueError: If the token is invalid, not found, or expired.\n+        \"\"\"\n+        token_hash = self._hash_token(raw_token)\n+        record = self.token_repository.get_by_hash(token_hash)\n+        if not record:\n+            raise ValueError(\"Invalid verification token.\")\n+\n+        # Check expiry.\n+        if record.expires_at < datetime.utcnow():\n+            # Clean up the stale token.\n+            self.token_repository.delete(record)\n+            raise ValueError(\"Verification token has expired.\")\n+\n+        # Retrieve the guest and mark as verified.\n+        guest = self.guest_repository.get_by_id(record.guest_id)\n+        if not guest:\n+            raise ValueError(\"Guest associated with token not found.\")\n+\n+        guest.is_email_verified = True\n+        self.guest_repository.save(guest)\n+\n+        # Token is single‑use – remove it.\n+        self.token_repository.delete(record)\n+\n+        return guest\n+\n*** End of File ***