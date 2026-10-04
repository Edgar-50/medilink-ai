from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False, index=True)
    specialty: Mapped[str] = mapped_column(String(120), nullable=False)
    clinic: Mapped[str] = mapped_column(String(180), nullable=False)
    years_experience: Mapped[int] = mapped_column(Integer, default=0)
    consultation_type: Mapped[str] = mapped_column(String(80), default="Video & in-person")
    bio: Mapped[str] = mapped_column(Text, default="")
    accepting_new_patients: Mapped[bool] = mapped_column(Boolean, default=True)

    user = relationship("User", back_populates="doctor_profile")

class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    start_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    end_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False)

    doctor = relationship("User", back_populates="availability_slots")
