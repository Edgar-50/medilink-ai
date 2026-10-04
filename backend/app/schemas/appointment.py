from datetime import datetime
from pydantic import BaseModel, Field
from app.models.appointment import AppointmentStatus

class AppointmentCreate(BaseModel):
    doctor_id: int
    scheduled_at: datetime
    reason: str = Field(min_length=3, max_length=255)

class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    scheduled_at: datetime
    reason: str
    notes: str | None
    status: AppointmentStatus

    model_config = {"from_attributes": True}

class AppointmentDetail(AppointmentResponse):
    patient_name: str
    doctor_name: str
