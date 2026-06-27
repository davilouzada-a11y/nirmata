"""Seed the database with the model version and a first radiologist user.

Run: ``python -m app.seed``
"""
from app.core.config import get_settings
from app.core.db import SessionLocal, init_db
from app.core.security import hash_password
from app.models.user import User
from app.services.study_service import get_or_create_model_version

settings = get_settings()


def seed():
    init_db()
    db = SessionLocal()
    try:
        get_or_create_model_version(db)

        existing = db.query(User).filter_by(email=settings.seed_admin_email).first()
        if not existing:
            db.add(User(
                name="Radiologista Responsável",
                email=settings.seed_admin_email,
                role="radiologist",
                hashed_password=hash_password(settings.seed_admin_password),
                active=True,
            ))
            print(f"Created radiologist user: {settings.seed_admin_email}")
        else:
            print("Radiologist user already exists.")
        db.commit()
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
