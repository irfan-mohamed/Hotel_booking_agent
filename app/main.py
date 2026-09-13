from sqlalchemy import text

from app.database.connection import SessionLocal
from app.database.seed import main as seed_database

def main():
    
    print("Starting Hotel Booking Agent...")

    with SessionLocal() as session:
        result = session.execute(text("SELECT version();"))
        version = result.scalar_one()

        print("Successfully connected to PostgreSQL.")
        print(f"PostgreSQL version: {version}")


if __name__ == "__main__":
    seed_database()