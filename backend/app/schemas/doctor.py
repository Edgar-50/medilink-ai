from datetime import datetime
from pydantic import BaseModel, Field

class DoctorProfileUpdate(BaseModel):
    specialty: str = Field(min_length=2, max_length=120)
    clinic: str = Field(min_length=2, max_length=180)
    years_experience: int = Field(ge=0, le=70)
    consultation_type: str = Field(min_length=2, max_length=80)
    bio: str = Field(default="", max_length=3000)
    accepting_new_patients: bool = True

class DoctorProfileResponse(BaseModel):
    doctor_id: int
    full_name: str
    email: str
    specialty: str
    clinic: str
    years_experience: int
    consultation_type: str
    bio: str
    accepting_new_patients: bool
    profile_complete: bool

class AvailabilityCreate(BaseModel):
    start_at: datetime
    end_at: datetime

class AvailabilityResponse(BaseModel):
    id: int
    doctor_id: int
    start_at: datetime
    end_at: datetime
    is_booked: bool

    model_config = {"from_attributes": True}
