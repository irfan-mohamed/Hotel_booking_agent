from collections.abc import Generator

from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.repositories.booking_repository import BookingRepository
from app.repositories.guest_repository import GuestRepository
from app.repositories.room_repository import RoomRepository
from app.services.alternative_service import AlternativeService
from app.services.availability_service import AvailabilityService
from app.services.booking_service import BookingService
from app.tools.availability_tool import AvailabilityTool
from app.tools.booking_tool import BookingTool


def get_db() -> Generator[Session, None, None]:
    """
    Provide a database session for one API request.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def get_room_repository(
    db: Session,
) -> RoomRepository:
    """
    Create a RoomRepository using the current DB session.
    """

    return RoomRepository(db)


def get_booking_repository(
    db: Session,
) -> BookingRepository:
    """
    Create a BookingRepository using the current DB session.
    """

    return BookingRepository(db)


def get_guest_repository(
    db: Session,
) -> GuestRepository:
    """
    Create a GuestRepository using the current DB session.
    """

    return GuestRepository(db)


def get_availability_service(
    db: Session,
) -> AvailabilityService:
    """
    Build the AvailabilityService dependency chain.
    """

    room_repository = RoomRepository(db)

    alternative_service = AlternativeService(
        room_repository=room_repository,
    )

    return AvailabilityService(
        room_repository=room_repository,
        alternative_service=alternative_service,
    )


def get_booking_service(
    db: Session,
) -> BookingService:
    """
    Build the BookingService dependency chain.
    """

    room_repository = RoomRepository(db)

    guest_repository = GuestRepository(db)

    booking_repository = BookingRepository(db)

    return BookingService(
        db=db,
        room_repository=room_repository,
        guest_repository=guest_repository,
        booking_repository=booking_repository,
    )


def get_availability_tool(
    db: Session,
) -> AvailabilityTool:
    """
    Create the availability tool.
    """

    availability_service = get_availability_service(db)

    return AvailabilityTool(
        availability_service=availability_service,
    )


def get_booking_tool(
    db: Session,
) -> BookingTool:
    """
    Create the booking tool.
    """

    booking_service = get_booking_service(db)

    return BookingTool(
        booking_service=booking_service,
    )