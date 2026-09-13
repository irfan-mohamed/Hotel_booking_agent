from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Guest


class GuestRepository:
    """
    Handles database operations related to guests.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, guest_id: int) -> Guest | None:
        """
        Retrieve a guest by ID.
        """
        statement = select(Guest).where(Guest.id == guest_id)

        return self.db.execute(statement).scalar_one_or_none()

    def get_by_email(self, email: str) -> Guest | None:
        """
        Retrieve a guest by email address.
        """

        statement = select(Guest).where(
            Guest.email == email
        )

        return self.db.execute(statement).scalar_one_or_none()

    def create(
        self,
        name: str,
        email: str,
    ) -> Guest:
        """
        Create a new guest.
        """

        guest = Guest(
            name=name,
            email=email,
        )

        self.db.add(guest)
        self.db.flush()

        return guest

    def get_or_create(
        self,
        name: str,
        email: str,
    ) -> Guest:
        """
        Return an existing guest if the email exists.
        Otherwise create a new guest.
        """

        guest = self.get_by_email(email)

        if guest:
            return guest

        return self.create(
            name=name,
            email=email,
        )