from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Facility(Base):
    __tablename__ = "facilities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(180))
    city: Mapped[str] = mapped_column(String(120), default="Bristol")
    facility_type: Mapped[str] = mapped_column(String(80), default="Hospital")
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class BedUnit(Base):
    __tablename__ = "bed_units"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    facility_id: Mapped[int] = mapped_column(ForeignKey("facilities.id"), index=True)
    ward: Mapped[str] = mapped_column(String(120))
    total_beds: Mapped[int] = mapped_column(Integer, default=0)
    occupied_beds: Mapped[int] = mapped_column(Integer, default=0)
    escalation_beds: Mapped[int] = mapped_column(Integer, default=0)

class StaffShift(Base):
    __tablename__ = "staff_shifts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    facility_id: Mapped[int] = mapped_column(ForeignKey("facilities.id"), index=True)
    staff_name: Mapped[str] = mapped_column(String(140))
    role: Mapped[str] = mapped_column(String(100))
    department: Mapped[str] = mapped_column(String(100))
    starts_at: Mapped[datetime] = mapped_column(DateTime)
    ends_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(40), default="scheduled")

class ReferralQueueItem(Base):
    __tablename__ = "referral_queue_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    facility_id: Mapped[int] = mapped_column(ForeignKey("facilities.id"), index=True)
    patient_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    specialty: Mapped[str] = mapped_column(String(120))
    urgency: Mapped[str] = mapped_column(String(40), default="routine")
    status: Mapped[str] = mapped_column(String(40), default="queued")
    age_hours: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class DeviceReading(Base):
    __tablename__ = "device_readings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    device_id: Mapped[str] = mapped_column(String(100), default="medilink-watch")
    heart_rate: Mapped[int] = mapped_column(Integer)
    spo2: Mapped[int] = mapped_column(Integer)
    temperature_c: Mapped[float] = mapped_column(Float)
    systolic: Mapped[int] = mapped_column(Integer)
    diastolic: Mapped[int] = mapped_column(Integer)
    battery: Mapped[int] = mapped_column(Integer, default=90)
    source: Mapped[str] = mapped_column(String(50), default="watch")
    observed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class ModelRegistryEntry(Base):
    __tablename__ = "model_registry_entries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    version: Mapped[str] = mapped_column(String(60))
    task: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(40), default="candidate")
    accuracy: Mapped[float] = mapped_column(Float, default=0)
    macro_f1: Mapped[float] = mapped_column(Float, default=0)
    calibration_error: Mapped[float] = mapped_column(Float, default=0)
    training_examples: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ModelDriftSnapshot(Base):
    __tablename__ = "model_drift_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_name: Mapped[str] = mapped_column(String(120), index=True)
    psi: Mapped[float] = mapped_column(Float, default=0)
    confidence_shift: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(40), default="stable")
    observed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class BackgroundJob(Base):
    __tablename__ = "background_jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_type: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(40), default="queued")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class GovernanceExport(Base):
    __tablename__ = "governance_exports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requested_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    export_type: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(40), default="ready")
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
