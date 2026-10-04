from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.core.security import get_current_user
from app.models.user import User, UserRole

router = APIRouter(prefix="/api/v1/experience", tags=["Care Experience"])

class LabResult(BaseModel):
    name: str; date: str; value: str; status: str; reference: str
class Medication(BaseModel):
    name: str; dose: str; schedule: str; next_due: str
class Notification(BaseModel):
    id: int; title: str; body: str; when: str; kind: str
class PatientSnapshot(BaseModel):
    labs: list[LabResult]; medications: list[Medication]; notifications: list[Notification]; health_score: int; sleep: str; activity_steps: int; stress: str
class ClinicalAlert(BaseModel):
    patient: str; signal: str; severity: str; detail: str
class DoctorSnapshot(BaseModel):
    alerts: list[ClinicalAlert]; notes_to_review: int; results_to_review: int; messages: int

@router.get("/patient", response_model=PatientSnapshot)
def patient_snapshot(current_user: User = Depends(get_current_user)):
    return PatientSnapshot(
        labs=[
            LabResult(name="Complete Blood Count", date="2 Oct 2026", value="Within reference range", status="normal", reference="Reference range reviewed"),
            LabResult(name="Cholesterol panel", date="28 Sep 2026", value="LDL 3.4 mmol/L", status="review", reference="Routine review"),
            LabResult(name="Kidney function", date="28 Sep 2026", value="eGFR 96", status="normal", reference="Routine review"),
        ],
        medications=[
            Medication(name="Amlodipine", dose="5 mg", schedule="Once daily", next_due="20:00"),
            Medication(name="Vitamin D", dose="1000 IU", schedule="Once daily", next_due="Tomorrow 08:00"),
        ],
        notifications=[
            Notification(id=1,title="Lab results available",body="Your latest blood test results are ready to review.",when="2h",kind="lab"),
            Notification(id=2,title="Medication reminder",body="A scheduled dose is due this evening.",when="5h",kind="medication"),
            Notification(id=3,title="MediLink Watch synced",body="Your wearable uploaded a new vitals summary.",when="8m",kind="watch"),
        ],
        health_score=88, sleep="7h 24m", activity_steps=8425, stress="Low"
    )

@router.get("/doctor", response_model=DoctorSnapshot)
def doctor_snapshot(current_user: User = Depends(get_current_user)):
    return DoctorSnapshot(
        alerts=[
            ClinicalAlert(patient="Jordan Reed",signal="Blood pressure trend",severity="review",detail="Several recent readings are above the patient's recent baseline."),
            ClinicalAlert(patient="Alex Morgan",signal="Follow-up due",severity="info",detail="Care-plan review is due this week."),
            ClinicalAlert(patient="Jamie Patel",signal="New lab result",severity="info",detail="A cholesterol panel is ready for clinician review."),
        ],
        notes_to_review=3, results_to_review=4, messages=6
    )
