from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.doctor import AvailabilitySlot, DoctorProfile
from app.models.user import User, UserRole
from app.schemas.doctor import (
    AvailabilityCreate,
    AvailabilityResponse,
    DoctorProfileResponse,
    DoctorProfileUpdate,
)

router = APIRouter(prefix="/api/v1/doctors", tags=["Doctors"])

def require_doctor(user: User):
    if user.role != UserRole.doctor:
        raise HTTPException(status_code=403, detail="Doctor access required")

def profile_payload(user: User, profile: DoctorProfile | None):
    return {
        "doctor_id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "specialty": profile.specialty if profile else "",
        "clinic": profile.clinic if profile else "",
        "years_experience": profile.years_experience if profile else 0,
        "consultation_type": profile.consultation_type if profile else "Video & in-person",
        "bio": profile.bio if profile else "",
        "accepting_new_patients": profile.accepting_new_patients if profile else True,
        "profile_complete": profile is not None,
    }

@router.get("", response_model=list[DoctorProfileResponse])
def list_doctors(
    specialty: str | None = Query(default=None),
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(User, DoctorProfile).join(
        DoctorProfile, DoctorProfile.user_id == User.id
    ).filter(
        User.role == UserRole.doctor,
        User.is_active.is_(True),
        DoctorProfile.accepting_new_patients.is_(True),
    )
    if specialty:
        query = query.filter(DoctorProfile.specialty.ilike(f"%{specialty.strip()}%"))
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(
            (User.full_name.ilike(term)) |
            (DoctorProfile.specialty.ilike(term)) |
            (DoctorProfile.clinic.ilike(term))
        )
    return [profile_payload(user, profile) for user, profile in query.order_by(User.full_name).all()]

@router.get("/me/profile", response_model=DoctorProfileResponse)
def my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_doctor(current_user)
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == current_user.id).first()
    return profile_payload(current_user, profile)

@router.put("/me/profile", response_model=DoctorProfileResponse)
def save_my_profile(
    payload: DoctorProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_doctor(current_user)
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == current_user.id).first()
    if not profile:
        profile = DoctorProfile(user_id=current_user.id, **payload.model_dump())
        db.add(profile)
    else:
        for key, value in payload.model_dump().items():
            setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile_payload(current_user, profile)

@router.post("/me/availability", response_model=AvailabilityResponse, status_code=201)
def add_availability(
    payload: AvailabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_doctor(current_user)
    if payload.end_at <= payload.start_at:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    if payload.start_at <= datetime.now():
        raise HTTPException(status_code=400, detail="Availability must be in the future")

    overlap = db.query(AvailabilitySlot).filter(
        AvailabilitySlot.doctor_id == current_user.id,
        AvailabilitySlot.start_at < payload.end_at,
        AvailabilitySlot.end_at > payload.start_at,
    ).first()
    if overlap:
        raise HTTPException(status_code=409, detail="This availability overlaps an existing slot")

    slot = AvailabilitySlot(doctor_id=current_user.id, **payload.model_dump())
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot

@router.get("/me/availability", response_model=list[AvailabilityResponse])
def my_availability(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_doctor(current_user)
    return db.query(AvailabilitySlot).filter(
        AvailabilitySlot.doctor_id == current_user.id
    ).order_by(AvailabilitySlot.start_at.asc()).all()

@router.get("/{doctor_id}", response_model=DoctorProfileResponse)
def doctor_detail(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.get(User, doctor_id)
    if not user or user.role != UserRole.doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == doctor_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Doctor profile is not complete")
    return profile_payload(user, profile)

@router.get("/{doctor_id}/availability", response_model=list[AvailabilityResponse])
def doctor_availability(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doctor = db.get(User, doctor_id)
    if not doctor or doctor.role != UserRole.doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return db.query(AvailabilitySlot).filter(
        AvailabilitySlot.doctor_id == doctor_id,
        AvailabilitySlot.is_booked.is_(False),
        AvailabilitySlot.start_at > datetime.now(),
    ).order_by(AvailabilitySlot.start_at.asc()).all()
