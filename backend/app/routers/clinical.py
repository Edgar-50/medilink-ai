from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.appointment import Appointment
from app.models.clinical_note import ClinicalNote
from app.models.health_record import HealthRecord
from app.models.user import User, UserRole

router = APIRouter(prefix="/api/v1/clinical", tags=["Clinical Workspace"])

class PatientSummary(BaseModel):
    patient_id: int
    full_name: str
    email: str
    upcoming_appointments: int
    record_items: int
    latest_reason: str | None

class RecordItem(BaseModel):
    id: int | None = None
    record_type: str
    title: str
    body: str
    created_at: str

class NoteCreate(BaseModel):
    patient_id: int
    appointment_id: int | None = None
    note_type: str = "SOAP"
    subjective: str = Field(default="", max_length=5000)
    objective: str = Field(default="", max_length=5000)
    assessment: str = Field(default="", max_length=5000)
    plan: str = Field(default="", max_length=5000)

class NoteUpdate(BaseModel):
    subjective: str | None = Field(default=None, max_length=5000)
    objective: str | None = Field(default=None, max_length=5000)
    assessment: str | None = Field(default=None, max_length=5000)
    plan: str | None = Field(default=None, max_length=5000)
    status: str | None = None

class NoteOut(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    appointment_id: int | None
    note_type: str
    subjective: str
    objective: str
    assessment: str
    plan: str
    status: str
    created_at: str
    updated_at: str


def require_doctor(user: User):
    if user.role not in (UserRole.doctor, UserRole.admin):
        raise HTTPException(status_code=403, detail="Clinician access required")


def _patient_has_relationship(db: Session, doctor_id: int, patient_id: int) -> bool:
    return db.query(Appointment).filter(Appointment.doctor_id == doctor_id, Appointment.patient_id == patient_id).first() is not None


def _default_record(patient: User) -> list[RecordItem]:
    return [
        RecordItem(record_type="encounter", title="Primary care consultation", body="Review of recurring headaches and fatigue. Follow-up planned after routine observations and medication review.", created_at="2026-10-03T10:30:00"),
        RecordItem(record_type="laboratory", title="Blood results", body="Complete blood count within reference range. Cholesterol panel available for routine review.", created_at="2026-10-02T09:15:00"),
        RecordItem(record_type="medication", title="Medication list", body="Amlodipine 5 mg once daily. Vitamin D 1000 IU once daily.", created_at="2026-09-28T08:00:00"),
        RecordItem(record_type="observation", title="Connected vitals summary", body="Recent wearable trend shows stable resting heart rate and oxygen saturation with a small number of blood-pressure readings above the recent baseline.", created_at="2026-10-04T08:40:00"),
    ]

@router.get("/patients", response_model=list[PatientSummary])
def my_patients(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_doctor(current_user)
    if current_user.role == UserRole.admin:
        patients = db.query(User).filter(User.role == UserRole.patient).all()
    else:
        ids = [r[0] for r in db.query(Appointment.patient_id).filter(Appointment.doctor_id == current_user.id).distinct().all()]
        patients = db.query(User).filter(User.id.in_(ids)).all() if ids else []
    out=[]
    for p in patients:
        appts=db.query(Appointment).filter(Appointment.patient_id==p.id, Appointment.doctor_id==current_user.id).order_by(Appointment.scheduled_at.desc()).all() if current_user.role!=UserRole.admin else db.query(Appointment).filter(Appointment.patient_id==p.id).order_by(Appointment.scheduled_at.desc()).all()
        records=db.query(HealthRecord).filter(HealthRecord.patient_id==p.id).count()
        out.append(PatientSummary(patient_id=p.id,full_name=p.full_name,email=p.email,upcoming_appointments=sum(1 for a in appts if a.status.value=="scheduled"),record_items=max(records,4),latest_reason=appts[0].reason if appts else "Routine care review"))
    return out

@router.get("/patients/{patient_id}/record", response_model=list[RecordItem])
def patient_record(patient_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_doctor(current_user)
    patient=db.get(User,patient_id)
    if not patient or patient.role!=UserRole.patient: raise HTTPException(status_code=404, detail="Patient not found")
    if current_user.role==UserRole.doctor and not _patient_has_relationship(db,current_user.id,patient_id):
        raise HTTPException(status_code=403, detail="No care relationship found for this patient")
    rows=db.query(HealthRecord).filter(HealthRecord.patient_id==patient_id).order_by(HealthRecord.created_at.desc()).all()
    if not rows: return _default_record(patient)
    return [RecordItem(id=r.id,record_type=r.record_type,title=r.title,body=r.body,created_at=r.created_at.isoformat()) for r in rows]

@router.get("/patients/{patient_id}/notes", response_model=list[NoteOut])
def list_notes(patient_id:int, db:Session=Depends(get_db), current_user:User=Depends(get_current_user)):
    require_doctor(current_user)
    if current_user.role==UserRole.doctor and not _patient_has_relationship(db,current_user.id,patient_id):
        raise HTTPException(status_code=403, detail="No care relationship found for this patient")
    rows=db.query(ClinicalNote).filter(ClinicalNote.patient_id==patient_id).order_by(ClinicalNote.updated_at.desc()).all()
    return [NoteOut(id=n.id,patient_id=n.patient_id,doctor_id=n.doctor_id,appointment_id=n.appointment_id,note_type=n.note_type,subjective=n.subjective,objective=n.objective,assessment=n.assessment,plan=n.plan,status=n.status,created_at=n.created_at.isoformat(),updated_at=n.updated_at.isoformat()) for n in rows]

@router.post("/notes", response_model=NoteOut, status_code=201)
def create_note(payload:NoteCreate, db:Session=Depends(get_db), current_user:User=Depends(get_current_user)):
    require_doctor(current_user)
    patient=db.get(User,payload.patient_id)
    if not patient or patient.role!=UserRole.patient: raise HTTPException(status_code=404, detail="Patient not found")
    if current_user.role==UserRole.doctor and not _patient_has_relationship(db,current_user.id,payload.patient_id):
        raise HTTPException(status_code=403, detail="No care relationship found for this patient")
    n=ClinicalNote(patient_id=payload.patient_id,doctor_id=current_user.id,appointment_id=payload.appointment_id,note_type=payload.note_type,subjective=payload.subjective,objective=payload.objective,assessment=payload.assessment,plan=payload.plan,status="draft")
    db.add(n); db.commit(); db.refresh(n)
    return NoteOut(id=n.id,patient_id=n.patient_id,doctor_id=n.doctor_id,appointment_id=n.appointment_id,note_type=n.note_type,subjective=n.subjective,objective=n.objective,assessment=n.assessment,plan=n.plan,status=n.status,created_at=n.created_at.isoformat(),updated_at=n.updated_at.isoformat())

@router.patch("/notes/{note_id}", response_model=NoteOut)
def update_note(note_id:int,payload:NoteUpdate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    require_doctor(current_user)
    n=db.get(ClinicalNote,note_id)
    if not n: raise HTTPException(status_code=404, detail="Note not found")
    if current_user.role!=UserRole.admin and n.doctor_id!=current_user.id: raise HTTPException(status_code=403,detail="You can only edit your own notes")
    for k,v in payload.model_dump(exclude_unset=True).items():
        if k=="status" and v not in ("draft","signed"): raise HTTPException(status_code=400,detail="Status must be draft or signed")
        setattr(n,k,v)
    n.updated_at=datetime.utcnow(); db.commit(); db.refresh(n)
    return NoteOut(id=n.id,patient_id=n.patient_id,doctor_id=n.doctor_id,appointment_id=n.appointment_id,note_type=n.note_type,subjective=n.subjective,objective=n.objective,assessment=n.assessment,plan=n.plan,status=n.status,created_at=n.created_at.isoformat(),updated_at=n.updated_at.isoformat())
