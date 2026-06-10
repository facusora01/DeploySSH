#!/usr/bin/env python3
"""
Seed script to populate initial test data.
DEVELOPMENT ONLY - Never use in production!
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.models.profesional import Profesional
from app.models.client import Client
from app.core.config import settings
from app.core.security import get_password_hash

# Read from env vars (for security), with dev defaults
PRO_EMAIL = os.getenv("SEED_PRO_EMAIL", "profesional@example.com")
PRO_PASSWORD = os.getenv("SEED_PRO_PASSWORD", "password123")
CLIENT_EMAIL = os.getenv("SEED_CLIENT_EMAIL", "cliente@example.com")
CLIENT_PASSWORD = os.getenv("SEED_CLIENT_PASSWORD", "password123")


def seed_database():
    """Populate database with initial test users."""
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Check if seed data already exists
        existing_pro = db.query(User).filter(User.email == PRO_EMAIL).first()
        existing_client = db.query(User).filter(User.email == CLIENT_EMAIL).first()

        if existing_pro and existing_client:
            print("✓ Seed data already exists, skipping...")
            return

        # Create professional user
        if not existing_pro:
            pro_user = User(
                email=PRO_EMAIL,
                password_hash=get_password_hash(PRO_PASSWORD),
                full_name="Dr. Juan Pérez",
                phone="+54 11 1234 5678",
                role="profesional",
                is_email_verified=True,
            )
            db.add(pro_user)
            db.flush()

            profesional = Profesional(
                user_id=pro_user.id,
                specialty="Dermatología",
                bio="Dermatólogo con 10 años de experiencia",
                public_link="dr-juan-perez",
                buffer_minutes=15,
                agenda_paused=False,
            )
            db.add(profesional)
            print(f"✓ Created professional user: {PRO_EMAIL}")

        # Create client user
        if not existing_client:
            client_user = User(
                email=CLIENT_EMAIL,
                password_hash=get_password_hash(CLIENT_PASSWORD),
                full_name="María González",
                phone="+54 11 9876 5432",
                role="client",
                is_email_verified=True,
            )
            db.add(client_user)
            db.flush()

            client = Client(
                user_id=client_user.id,
                dni="12345678A",
                date_of_birth="1990-05-15",
                address="Av. Siempreviva 742",
                city="Buenos Aires",
            )
            db.add(client)
            print(f"✓ Created client user: {CLIENT_EMAIL}")

        db.commit()
        print("\n✓ Seed data loaded successfully!")

    except Exception as e:
        db.rollback()
        print(f"✗ Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
