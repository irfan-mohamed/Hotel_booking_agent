from app.models import Booking
from app.db import db
import re
def _validate_email(email: str) -> None:
    """
    Validate ``email`` using a simple regular expression.

    The regex checks for the presence of exactly one ``@`` symbol and at least one
    ``.`` after it. It is intentionally permissive – the goal is to catch obvious
    formatting mistakes before any database interaction.
    """
    if not re.fullmatch(r'[^@]+@[^@]+\.[^@]+', email):
        raise ValueError(f"Invalid email format: {email}")


def create_booking(guest_name, guest_email, room_id, start_date, end_date):
    # Validate email before any DB work
    _validate_email(guest_email)

    # existing implementation …
    booking = Booking(
        guest_name=guest_name,
        guest_email=guest_email,
        room_id=room_id,
        start_date=start_date,
        end_date=end_date,
    )
    db.session.add(booking)
    db.session.commit()
    return booking