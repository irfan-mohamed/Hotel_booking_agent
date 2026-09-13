from datetime import date, timedelta
from decimal import Decimal
from urllib.parse import urlparse, urlunparse

import psycopg
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.connection import Base
from app.models import Booking, Guest, Reservation, Room
from app.repositories.booking_repository import BookingRepository
from app.repositories.guest_repository import GuestRepository
from app.repositories.room_repository import RoomRepository
from app.services.alternative_service import AlternativeService
from app.services.availability_service import AvailabilityService
from app.services.booking_service import BookingService


TEST_DATABASE_URL = (
    "postgresql+psycopg://"
    "hotel_user:hotel_password"
    "@postgres:5432/"
    "hotel_booking_test"
)


def _maintenance_database_url() -> str:
    """
    Build a connection URL pointing to PostgreSQL's default
    maintenance database instead of the application database.
    """

    parsed = urlparse(TEST_DATABASE_URL)

    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            "/postgres",
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )


def _ensure_test_database_exists() -> None:
    """
    Create the test database if it does not already exist.
    """

    parsed = urlparse(TEST_DATABASE_URL)

    host = parsed.hostname
    port = parsed.port or 5432
    user = parsed.username
    password = parsed.password

    with psycopg.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname="postgres",
        autocommit=True,
    ) as connection:

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                ("hotel_booking_test",),
            )

            exists = cursor.fetchone()

            if not exists:
                cursor.execute(
                    "CREATE DATABASE hotel_booking_test "
                    "OWNER hotel_user"
                )


@pytest.fixture(scope="session")
def test_engine():
    """
    Create the SQLAlchemy engine for the test database.
    """

    _ensure_test_database_exists()

    engine = create_engine(
        TEST_DATABASE_URL,
        pool_pre_ping=True,
    )

    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)

    engine.dispose()


@pytest.fixture()
def db(test_engine):
    """
    Provide a clean database session for every test.

    All records created during a test are rolled back afterward.
    """

    connection = test_engine.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(
        bind=connection,
        class_=Session,
        expire_on_commit=False,
    )

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def room_repository(db):
    return RoomRepository(db)


@pytest.fixture()
def guest_repository(db):
    return GuestRepository(db)


@pytest.fixture()
def booking_repository(db):
    return BookingRepository(db)


@pytest.fixture()
def alternative_service(room_repository):
    return AlternativeService(
        room_repository=room_repository,
    )


@pytest.fixture()
def availability_service(
    room_repository,
    alternative_service,
):
    return AvailabilityService(
        room_repository=room_repository,
        alternative_service=alternative_service,
    )


@pytest.fixture()
def booking_service(
    db,
    room_repository,
    guest_repository,
    booking_repository,
):
    return BookingService(
        db=db,
        room_repository=room_repository,
        guest_repository=guest_repository,
        booking_repository=booking_repository,
    )


@pytest.fixture()
def test_rooms(db):
    """
    Create deterministic rooms for testing.
    """

    rooms = [
        Room(
            room_no=101,
            room_type="Standard",
            bed_type="single",
            breakfast=False,
            price_per_night=Decimal("2200.00"),
            floor=1,
            max_guests=1,
        ),
        Room(
            room_no=102,
            room_type="Standard",
            bed_type="single",
            breakfast=True,
            price_per_night=Decimal("2600.00"),
            floor=1,
            max_guests=1,
        ),
        Room(
            room_no=103,
            room_type="Standard",
            bed_type="double",
            breakfast=False,
            price_per_night=Decimal("3000.00"),
            floor=1,
            max_guests=2,
        ),
        Room(
            room_no=104,
            room_type="Standard",
            bed_type="double",
            breakfast=True,
            price_per_night=Decimal("3400.00"),
            floor=1,
            max_guests=2,
        ),
        Room(
            room_no=201,
            room_type="Deluxe",
            bed_type="double",
            breakfast=True,
            price_per_night=Decimal("4500.00"),
            floor=2,
            max_guests=2,
        ),
        Room(
            room_no=202,
            room_type="Deluxe",
            bed_type="double",
            breakfast=False,
            price_per_night=Decimal("4100.00"),
            floor=2,
            max_guests=2,
        ),
        Room(
            room_no=203,
            room_type="Deluxe",
            bed_type="single",
            breakfast=True,
            price_per_night=Decimal("3800.00"),
            floor=2,
            max_guests=1,
        ),
        Room(
            room_no=301,
            room_type="Suite",
            bed_type="double",
            breakfast=True,
            price_per_night=Decimal("6500.00"),
            floor=3,
            max_guests=4,
        ),
    ]

    db.add_all(rooms)
    db.flush()

    return rooms


@pytest.fixture()
def future_dates():
    """
    Return a deterministic future stay.
    """

    check_in = date.today() + timedelta(days=30)
    check_out = check_in + timedelta(days=3)

    return check_in, check_out