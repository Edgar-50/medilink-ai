from __future__ import annotations

from datetime import datetime
import io
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.appointment import Appointment
from app.models.care import AuditEvent, CareDocument, LabOrder, MedicationOrder, Notification, Referral
from app.models.advanced import ClinicalLetter, RiskAssessment
from app.models.user import User, UserRole

router = APIRouter(prefix="/api/v1/advanced", tags=["Advanced Clinical Operations"])


def require_clinician(user: User):
    if user.role not in (UserRole.doctor, UserRole.admin):
        raise HTTPException(status_code=403, detail="Clinician access required")


def can_access_patient(db: Session, user: User, patient_id: int):
    if user.role == UserRole.admin:
        return
    if user.role == UserRole.doctor:
        related = db.query(Appointment).filter(
            Appointment.doctor_id == user.id,
            Appointment.patient_id == patient_id,
        ).first()
        if related:
            return
    raise HTTPException(status_code=403, detail="No care relationship found for this patient")


def audit(db: Session, actor: User, action: str, resource_type: str, resource_id: str = "", detail: str = ""):
    db.add(AuditEvent(actor_id=actor.id, action=action, resource_type=resource_type, resource_id=str(resource_id), detail=detail))


class PrescriptionCreate(BaseModel):
    patient_id: int
    name: str = Field(min_length=2, max_length=180)
    dose: str = Field(default="", max_length=120)
    schedule: str = Field(default="", max_length=180)
    instructions: str = Field(default="", max_length=1500)
    next_due: str = Field(default="", max_length=80)


class LabRequestCreate(BaseModel):
    patient_id: int
    test_name: str = Field(min_length=2, max_length=180)


class ReferralRequestCreate(BaseModel):
    patient_id: int
    specialty: str = Field(min_length=2, max_length=120)
    destination: str = Field(default="MediLink specialist network", max_length=180)
    reason: str = Field(min_length=3, max_length=3000)
    urgency: str = Field(default="routine", max_length=32)


class LetterCreate(BaseModel):
    patient_id: int
    title: str = Field(default="Clinical care letter", max_length=180)
    recipient: str = Field(default="Care team", max_length=180)
    body: str = Field(min_length=10, max_length=12000)


class RiskInput(BaseModel):
    patient_id: int
    symptom_burden: int = Field(default=1, ge=0, le=3)
    recent_unplanned_care: int = Field(default=0, ge=0, le=3)
    medication_complexity: int = Field(default=1, ge=0, le=3)
    monitoring_alerts: int = Field(default=0, ge=0, le=3)
    missed_followups: int = Field(default=0, ge=0, le=3)


INTERACTIONS = {
    frozenset(("warfarin", "ibuprofen")): ("high", "Bleeding risk may increase when warfarin and ibuprofen are used together."),
    frozenset(("warfarin", "aspirin")): ("high", "Concurrent antithrombotic effect can increase bleeding risk."),
    frozenset(("lisinopril", "spironolactone")): ("moderate", "Combination can increase potassium and requires monitoring."),
    frozenset(("amlodipine", "simvastatin")): ("moderate", "Simvastatin dose limitations may apply with amlodipine."),
    frozenset(("metformin", "contrast media")): ("moderate", "Renal function and temporary metformin interruption may need review around iodinated contrast."),
}


@router.get("/patients/{patient_id}/summary")
def patient_summary(patient_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_clinician(current_user)
    can_access_patient(db, current_user, patient_id)
    patient = db.get(User, patient_id)
    if not patient or patient.role != UserRole.patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    meds = db.query(MedicationOrder).filter(MedicationOrder.patient_id == patient_id, MedicationOrder.status == "active").all()
    labs = db.query(LabOrder).filter(LabOrder.patient_id == patient_id).order_by(LabOrder.ordered_at.desc()).limit(8).all()
    refs = db.query(Referral).filter(Referral.patient_id == patient_id).order_by(Referral.created_at.desc()).limit(6).all()
    docs = db.query(CareDocument).filter(CareDocument.patient_id == patient_id).order_by(CareDocument.created_at.desc()).limit(6).all()
    return {
        "patient": {"id": patient.id, "full_name": patient.full_name, "email": patient.email},
        "medications": meds,
        "labs": labs,
        "referrals": refs,
        "documents": [{"id": d.id, "filename": d.filename, "summary": d.summary, "created_at": d.created_at} for d in docs],
    }


@router.post("/prescriptions", status_code=201)
def create_prescription(payload: PrescriptionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_clinician(current_user)
    can_access_patient(db, current_user, payload.patient_id)
    row = MedicationOrder(patient_id=payload.patient_id, prescriber_id=current_user.id, name=payload.name, dose=payload.dose, schedule=payload.schedule, instructions=payload.instructions, next_due=payload.next_due, status="active")
    db.add(row)
    db.add(Notification(user_id=payload.patient_id, title="Prescription updated", body=f"{payload.name} has been added to your medication plan.", kind="medication"))
    audit(db, current_user, "prescription.create", "MedicationOrder", detail=payload.name)
    db.commit(); db.refresh(row)
    return row


@router.post("/labs", status_code=201)
def create_lab_request(payload: LabRequestCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_clinician(current_user)
    can_access_patient(db, current_user, payload.patient_id)
    row = LabOrder(patient_id=payload.patient_id, clinician_id=current_user.id, test_name=payload.test_name, status="ordered")
    db.add(row)
    db.add(Notification(user_id=payload.patient_id, title="Laboratory request", body=f"{payload.test_name} has been requested by your care team.", kind="lab"))
    audit(db, current_user, "lab.order", "LabOrder", detail=payload.test_name)
    db.commit(); db.refresh(row)
    return row


@router.post("/referrals", status_code=201)
def create_referral(payload: ReferralRequestCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_clinician(current_user)
    can_access_patient(db, current_user, payload.patient_id)
    row = Referral(patient_id=payload.patient_id, referring_clinician_id=current_user.id, specialty=payload.specialty, destination=payload.destination, reason=payload.reason, urgency=payload.urgency, status="sent")
    db.add(row)
    db.add(Notification(user_id=payload.patient_id, title="Referral sent", body=f"A referral to {payload.specialty} has been created.", kind="referral"))
    audit(db, current_user, "referral.create", "Referral", detail=payload.specialty)
    db.commit(); db.refresh(row)
    return row


@router.post("/medication-interactions")
def medication_interactions(payload: dict, current_user: User = Depends(get_current_user)):
    names = [str(x).strip().lower() for x in payload.get("medications", []) if str(x).strip()]
    findings = []
    for i, a in enumerate(names):
        for b in names[i+1:]:
            item = INTERACTIONS.get(frozenset((a, b)))
            if item:
                severity, detail = item
                findings.append({"medications": [a.title(), b.title()], "severity": severity, "detail": detail})
    return {"reviewed": len(names), "findings": findings, "status": "review_needed" if findings else "no_known_demo_rules_triggered", "note": "Interaction checks support clinician review and do not replace pharmacy references or prescribing judgement."}


@router.post("/risk", status_code=201)
def create_risk_assessment(payload: RiskInput, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_clinician(current_user)
    can_access_patient(db, current_user, payload.patient_id)
    weights = {"symptom_burden": 24, "recent_unplanned_care": 24, "medication_complexity": 16, "monitoring_alerts": 22, "missed_followups": 14}
    vals = payload.model_dump(exclude={"patient_id"})
    score = round(sum((vals[k] / 3) * w for k, w in weights.items()), 1)
    band = "high" if score >= 66 else "moderate" if score >= 34 else "low"
    factors = [{"factor": k.replace("_", " ").title(), "level": v, "contribution": round((v/3)*weights[k], 1)} for k, v in vals.items() if v > 0]
    rationale = f"{band.title()} coordination risk based on current symptom burden, recent care use, medication complexity, monitoring alerts and follow-up reliability."
    row = RiskAssessment(patient_id=payload.patient_id, clinician_id=current_user.id, score=score, band=band, factors_json=json.dumps(factors), rationale=rationale)
    db.add(row); audit(db, current_user, "risk.assess", "RiskAssessment", detail=f"{score}/{band}"); db.commit(); db.refresh(row)
    return {"id": row.id, "score": score, "band": band, "factors": factors, "rationale": rationale, "note": "This score is a care-coordination aid, not a diagnosis or validated emergency prediction."}


@router.get("/patients/{patient_id}/risk/latest")
def latest_risk(patient_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_clinician(current_user); can_access_patient(db, current_user, patient_id)
    row = db.query(RiskAssessment).filter(RiskAssessment.patient_id == patient_id).order_by(RiskAssessment.created_at.desc()).first()
    if not row:
        return {"score": 18, "band": "low", "factors": [{"factor": "Medication Complexity", "level": 1, "contribution": 5.3}], "rationale": "No recent high-risk coordination signals are recorded."}
    return {"id": row.id, "score": row.score, "band": row.band, "factors": json.loads(row.factors_json or "[]"), "rationale": row.rationale, "created_at": row.created_at}


@router.post("/letters", status_code=201)
def create_letter(payload: LetterCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_clinician(current_user); can_access_patient(db, current_user, payload.patient_id)
    row = ClinicalLetter(patient_id=payload.patient_id, doctor_id=current_user.id, title=payload.title, recipient=payload.recipient, body=payload.body, status="draft")
    db.add(row); audit(db, current_user, "letter.create", "ClinicalLetter", detail=payload.title); db.commit(); db.refresh(row)
    return row


@router.post("/letters/{letter_id}/sign")
def sign_letter(letter_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_clinician(current_user)
    row = db.get(ClinicalLetter, letter_id)
    if not row or (current_user.role != UserRole.admin and row.doctor_id != current_user.id):
        raise HTTPException(status_code=404, detail="Letter not found")
    row.status = "signed"; row.signed_at = datetime.utcnow(); audit(db, current_user, "letter.sign", "ClinicalLetter", letter_id, row.title); db.commit(); db.refresh(row)
    return row


@router.get("/letters/{letter_id}/pdf")
def letter_pdf(letter_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_clinician(current_user)
    row = db.get(ClinicalLetter, letter_id)
    if not row or (current_user.role != UserRole.admin and row.doctor_id != current_user.id):
        raise HTTPException(status_code=404, detail="Letter not found")
    patient = db.get(User, row.patient_id); doctor = db.get(User, row.doctor_id)
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except Exception as exc:
        raise HTTPException(status_code=500, detail="PDF support is not installed") from exc
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=A4); width, height = A4
    c.setFont("Helvetica-Bold", 17); c.drawString(54, height-65, "MediLink Clinical Letter")
    c.setFont("Helvetica", 10); c.drawString(54, height-88, f"Patient: {patient.full_name if patient else row.patient_id}")
    c.drawString(54, height-104, f"Clinician: {doctor.full_name if doctor else row.doctor_id}")
    c.drawString(54, height-120, f"Recipient: {row.recipient}")
    c.setFont("Helvetica-Bold", 13); c.drawString(54, height-150, row.title)
    text = c.beginText(54, height-178); text.setFont("Helvetica", 10); text.setLeading(15)
    for paragraph in row.body.splitlines() or [row.body]:
        words = paragraph.split(); line = ""
        for word in words:
            test = (line + " " + word).strip()
            if len(test) > 92:
                text.textLine(line); line = word
                if text.getY() < 70:
                    c.drawText(text); c.showPage(); text = c.beginText(54, height-70); text.setFont("Helvetica",10); text.setLeading(15)
            else: line = test
        text.textLine(line); text.textLine("")
    c.drawText(text); c.save(); buf.seek(0)
    audit(db, current_user, "letter.export", "ClinicalLetter", letter_id, row.title); db.commit()
    return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="medilink-letter-{letter_id}.pdf"'})
