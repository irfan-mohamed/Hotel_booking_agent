from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.database.connection import Base, SessionLocal, engine
from app.models import Booking, Guest, Reservation, Room


ROOMS = [
    {
        "room_no": 101,
        "room_type": "Standard",
        "bed_type": "single",
        "breakfast": False,
        "price_per_night": Decimal("2200.00"),
        "floor": 1,
        "max_guests": 1,
    },
    {
        "room_no": 102,
        "room_type": "Standard",
        "bed_type": "single",
        "breakfast": True,
        "price_per_night": Decimal("2600.00"),
        "floor": 1,
        "max_guests": 1,
    },
    {
        "room_no": 103,
        "room_type": "Standard",
        "bed_type": "double",
        "breakfast": False,
        "price_per_night": Decimal("3000.00"),
        "floor": 1,
        "max_guests": 2,
    },
    {
        "room_no": 104,
        "room_type": "Standard",
        "bed_type": "double",
        "breakfast": True,
        "price_per_night": Decimal("3400.00"),
        "floor": 1,
        "max_guests": 2,
    },
    {
        "room_no": 201,
        "room_type": "Deluxe",
        "bed_type": "double",
        "breakfast": True,
        "price_per_night": Decimal("4500.00"),
        "floor": 2,
        "max_guests": 2,
    },
    {
        "room_no": 202,
        "room_type": "Deluxe",
        "bed_type": "double",
        "breakfast": False,
        "price_per_night": Decimal("4100.00"),
        "floor": 2,
        "max_guests": 2,
    },
    {
        "room_no": 203,
        "room_type": "Deluxe",
        "bed_type": "single",
        "breakfast": True,
        "price_per_night": Decimal("3800.00"),
        "floor": 2,
        "max_guests": 1,
    },
    {
        "room_no": 204,
        "room_type": "Deluxe",
        "bed_type": "single",
        "breakfast": False,
        "price_per_night": Decimal("3500.00"),
        "floor": 2,
        "max_guests": 1,
    },
    {
        "room_no": 301,
        "room_type": "Suite",
        "bed_type": "double",
        "breakfast": True,
        "price_per_night": Decimal("6500.00"),
        "floor": 3,
        "max_guests": 4,
    },
    {
        "room_no": 302,
        "room_type": "Suite",
        "bed_type": "double",
        "breakfast": False,
        "price_per_night": Decimal("6000.00"),
        "floor": 3,
        "max_guests": 4,
    },
]


def seed_rooms(session):
    existing_rooms = session.execute(
        select(Room)
    ).scalars().all()

    if existing_rooms:
        print("Rooms already exist. Skipping room seed.")
        return

    rooms = [Room(**room_data) for room_data in ROOMS]

    session.add_all(rooms)
    session.commit()

    print(f"Inserted {len(rooms)} rooms.")


def seed_reservations(session):
    existing_reservations = session.execute(
        select(Reservation)
    ).scalars().all()

    if existing_reservations:
        print("Reservations already exist. Skipping reservation seed.")
        return

    rooms = {
        room.room_no: room
        for room in session.execute(select(Room)).scalars().all()
    }

    today = date.today()

    reservations = [
        # Room 102 is unavailable for a period.
        Reservation(
            room_id=rooms[102].id,
            check_in=today + timedelta(days=5),
            check_out=today + timedelta(days=8),
            status="confirmed",
        ),

        # Room 104 is unavailable for a different period.
        Reservation(
            room_id=rooms[104].id,
            check_in=today + timedelta(days=10),
            check_out=today + timedelta(days=14),
            status="confirmed",
        ),

        # Room 201 is booked for a longer period.
        Reservation(
            room_id=rooms[201].id,
            check_in=today + timedelta(days=7),
            check_out=today + timedelta(days=15),
            status="confirmed",
        ),

        # Room 203 is booked.
        Reservation(
            room_id=rooms[203].id,
            check_in=today + timedelta(days=10),
            check_out=today + timedelta(days=13),
            status="confirmed",
        ),

        # Room 301 is booked for a longer period.
        Reservation(
            room_id=rooms[301].id,
            check_in=today + timedelta(days=3),
            check_out=today + timedelta(days=20),
            status="confirmed",
        ),
    ]

    session.add_all(reservations)
    session.commit()

    print(f"Inserted {len(reservations)} reservations.")


def main():
    print("Creating database tables...")

    Base.metadata.create_all(bind=engine)

    print("Database tables created.")

    with SessionLocal() as session:
        seed_rooms(session)
        seed_reservations(session)

    print("Database seeding completed.")


if __name__ == "__main__":
    main()