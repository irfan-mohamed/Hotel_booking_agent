from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Index
    # Verification fields
    verification_token = Column(String, nullable=True, comment="Token used for email/phone verification")
    verification_expires_at = Column(DateTime, nullable=True, comment="Expiration datetime for the verification token")
    is_verified = Column(Boolean, nullable=False, default=False, server_default='false', comment="Flag indicating if the booking has been verified")
        {},
        Index('ix_booking_verification_token', 'verification_token')