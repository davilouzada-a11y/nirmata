from sqlalchemy import Column, String, Integer, Boolean

from app.core.db import Base, GUID, new_uuid


class Patient(Base):
    __tablename__ = "patients"

    id = Column(GUID, primary_key=True, default=new_uuid)
    external_code = Column(String, nullable=False, index=True)  # de-identified code
    sex = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    anonymized_flag = Column(Boolean, default=True)
