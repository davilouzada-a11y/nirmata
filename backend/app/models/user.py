from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime

from app.core.db import Base, GUID, new_uuid


class User(Base):
    __tablename__ = "users"

    id = Column(GUID, primary_key=True, default=new_uuid)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    # Roles: "radiologist" (can review), "technician" (upload only), "admin".
    role = Column(String, nullable=False, default="radiologist")
    hashed_password = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
