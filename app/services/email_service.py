import smtplib
from email.mime.text import MIMEText

from app.config import Config
from app.models import Guest

    def send_verification_email(self, guest: Guest, token: str) -> None:
        """
        Sends an email to the guest containing a verification link.

        The verification URL is built using the ``/verify-email`` endpoint and the
        provided token. SMTP configuration is read from ``Config``.
        """
        # Build verification link
        base_url = getattr(Config, \"BASE_URL\", \"\")
        if base_url:
            verification_url = f\"{base_url.rstrip('/')}/verify-email?token={token}\"
        else:
            verification_url = f\"/verify-email?token={token}\"

        subject = \"Confirm your booking email\"
        body = (
            f\"Hello {guest.first_name or ''},\\n\\n\"  # type: ignore[attr-defined]\n"
            f\"Please verify your email address by clicking the link below:\\n\"\n+            f\"{verification_url}\\n\\n\"\n"
            f\"If you did not request this, please ignore this email.\"\n+        )\n+\n+        # Prepare MIME message\n+        msg = MIMEText(body)\n+        msg[\"Subject\"] = subject\n+        msg[\"From\"] = getattr(Config, \"EMAIL_FROM\", \"no-reply@example.com\")\n+        msg[\"To\"] = guest.email  # type: ignore[attr-defined]\n+\n+        # Send email via SMTP\n+        smtp_host = getattr(Config, \"SMTP_HOST\", \"localhost\")\n+        smtp_port = getattr(Config, \"SMTP_PORT\", 25)\n+        smtp_user = getattr(Config, \"SMTP_USER\", None)\n+        smtp_password = getattr(Config, \"SMTP_PASSWORD\", None)\n+        use_tls = getattr(Config, \"SMTP_TLS\", False)\n+\n+        with smtplib.SMTP(smtp_host, smtp_port) as server:\n+            if use_tls:\n+                server.starttls()\n+            if smtp_user and smtp_password:\n+                server.login(smtp_user, smtp_password)\n+            server.send_message(msg)\n+        # No return value; errors will raise exceptions which can be handled by callers.