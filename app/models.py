"""SQLAlchemy models for Smart Inventory."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from .database import Base


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="available")
    qrcode_path = Column(String, nullable=True)

    histories = relationship(
        "History", back_populates="equipment", cascade="all, delete-orphan"
    )


class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    action = Column(String, nullable=False)
    user = Column(String, nullable=True)

    equipment = relationship("Equipment", back_populates="histories")
