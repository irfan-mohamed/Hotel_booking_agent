from sqlalchemy import Column, Integer, String, DateTime, Boolean
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    # Indicates whether the guest's email address has been verified
    is_email_verified = Column(Boolean, nullable=False, default=False)
    def __repr__(self):
        return (f"<Guest id={self.id} name={self.name} email={self.email} "
                f"is_email_verified={self.is_email_verified}>")
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_email_verified": self.is_email_verified,
        }