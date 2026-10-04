from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.appointment import Appointment
from app.models.doctor import AvailabilitySlot
from app.models.user import User, UserRole
from app.schemas.appointment import AppointmentCreate, AppointmentDetail, AppointmentResponse

router = APIRouter(prefix="/api/v1/appointments", tags=["Appointments"])

def detail_payload(appointment: Appointment):
    return {
        "id": appointment.id,
        "patient_id": appointment.patient_id,
        "doctor_id": appointment.doctor_id,
        "scheduled_at": appointment.scheduled_at,
        "reason": appointment.reason,
        "notes": appointment.notes,
        "status": appointment.status,
        "patient_name": appointment.patient.full_name,
        "doctor_name": appointment.doctor.full_name,
    }

@router.post("", response_model=AppointmentResponse, status_code=201)
def create_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.patient:
        raise HTTPException(status_code=403, detail="Only patients can book appointments")

    doctor = db.get(User, payload.doctor_id)
    if not doctor or doctor.role != UserRole.doctor or not doctor.is_active:
        raise HTTPException(status_code=400, detail="Invalid doctor")

    slot = db.query(AvailabilitySlot).filter(
        AvailabilitySlot.doctor_id == payload.doctor_id,
        AvailabilitySlot.start_at == payload.scheduled_at,
        AvailabilitySlot.is_booked.is_(False),
    ).first()
    if not slot:
        raise HTTPException(status_code=409, detail="That appointment slot is no longer available")

    appointment = Appointment(
        patient_id=current_user.id,
        doctor_id=payload.doctor_id,
        scheduled_at=payload.scheduled_at,
        reason=payload.reason,
    )
    slot.is_booked = True
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment

@router.get("/mine", response_model=list[AppointmentDetail])
def my_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Appointment)
    if current_user.role == UserRole.patient:
        query = query.filter(Appointment.patient_id == current_user.id)
    elif current_user.role == UserRole.doctor:
        query = query.filter(Appointment.doctor_id == current_user.id)
    elif current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Access denied")

    appointments = query.order_by(Appointment.scheduled_at.asc()).all()
    return [detail_payload(item) for item in appointments]

@router.get("", response_model=list[AppointmentDetail])
def list_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    appointments = db.query(Appointment).order_by(Appointment.scheduled_at.asc()).all()
    return [detail_payload(item) for item in appointments]
