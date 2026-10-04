from datetime import datetime
from pathlib import Path
import re

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.care import MedicationOrder, LabOrder, Referral, CareDocument, UserPreference, Notification, AuditEvent
from app.models.user import User, UserRole
from app.models.appointment import Appointment

router = APIRouter(prefix="/api/v1/care", tags=["Care Management"])
UPLOAD_ROOT = Path("storage/uploads")
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)


def _relationship(db: Session, doctor_id: int, patient_id: int) -> bool:
    return db.query(Appointment).filter(Appointment.doctor_id==doctor_id, Appointment.patient_id==patient_id).first() is not None

def _can_access_patient(db: Session, user: User, patient_id: int):
    if user.role == UserRole.admin: return
    if user.role == UserRole.patient and user.id == patient_id: return
    if user.role == UserRole.doctor and _relationship(db,user.id,patient_id): return
    raise HTTPException(status_code=403, detail="Access to this patient record is not permitted")

def _notify(db: Session, user_id:int, title:str, body:str, kind:str="care"):
    db.add(Notification(user_id=user_id,title=title,body=body,kind=kind))

def _audit(db: Session, actor:User, action:str, resource_type:str, resource_id:str="", detail:str=""):
    db.add(AuditEvent(actor_id=actor.id,action=action,resource_type=resource_type,resource_id=str(resource_id),detail=detail))

def _seed_patient_data(db:Session, patient_id:int):
    if db.query(MedicationOrder).filter(MedicationOrder.patient_id==patient_id).count()==0:
        db.add_all([
            MedicationOrder(patient_id=patient_id,name="Amlodipine",dose="5 mg",schedule="Once daily",instructions="Take at the same time each day.",next_due="20:00"),
            MedicationOrder(patient_id=patient_id,name="Vitamin D",dose="1000 IU",schedule="Once daily",instructions="Take with food.",next_due="Tomorrow 08:00"),
        ])
    if db.query(LabOrder).filter(LabOrder.patient_id==patient_id).count()==0:
        now=datetime.utcnow()
        db.add_all([
            LabOrder(patient_id=patient_id,test_name="Complete Blood Count",status="resulted",result_value="Within reference range",reference_range="Laboratory reference range",interpretation="No flagged values reported.",ordered_at=now,resulted_at=now),
            LabOrder(patient_id=patient_id,test_name="Cholesterol panel",status="resulted",result_value="LDL 3.4 mmol/L",reference_range="Review against individual cardiovascular risk",interpretation="Routine clinician review recommended.",ordered_at=now,resulted_at=now),
        ])
    db.commit()

class MedicationCreate(BaseModel):
    patient_id:int; name:str=Field(min_length=2,max_length=180); dose:str=""; schedule:str=""; instructions:str=""; next_due:str=""
class LabCreate(BaseModel):
    patient_id:int; test_name:str=Field(min_length=2,max_length=180)
class LabResultUpdate(BaseModel):
    result_value:str; reference_range:str=""; interpretation:str=""; status:str="resulted"
class ReferralCreate(BaseModel):
    patient_id:int; specialty:str; destination:str="MediLink specialist network"; reason:str; urgency:str="routine"
class PreferenceUpdate(BaseModel):
    preferred_name:str=""; phone:str=""; language:str="English"; appointment_reminders:bool=True; medication_reminders:bool=True; watch_alerts:bool=True; email_updates:bool=True

@router.get("/medications")
def medications(db:Session=Depends(get_db), current_user:User=Depends(get_current_user)):
    if current_user.role!=UserRole.patient: raise HTTPException(status_code=403,detail="Patient access required")
    _seed_patient_data(db,current_user.id)
    return db.query(MedicationOrder).filter(MedicationOrder.patient_id==current_user.id).order_by(MedicationOrder.created_at.desc()).all()

@router.post("/medications",status_code=201)
def create_medication(payload:MedicationCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    if current_user.role not in (UserRole.doctor,UserRole.admin): raise HTTPException(status_code=403,detail="Clinician access required")
    _can_access_patient(db,current_user,payload.patient_id)
    row=MedicationOrder(patient_id=payload.patient_id,prescriber_id=current_user.id,**payload.model_dump(exclude={"patient_id"}))
    db.add(row); _notify(db,payload.patient_id,"Medication updated",f"{payload.name} was added to your medication list.","medication"); _audit(db,current_user,"medication.create","MedicationOrder",detail=payload.name); db.commit(); db.refresh(row); return row

@router.get("/labs")
def labs(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    if current_user.role!=UserRole.patient: raise HTTPException(status_code=403,detail="Patient access required")
    _seed_patient_data(db,current_user.id)
    return db.query(LabOrder).filter(LabOrder.patient_id==current_user.id).order_by(LabOrder.ordered_at.desc()).all()

@router.post("/labs",status_code=201)
def order_lab(payload:LabCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    if current_user.role not in (UserRole.doctor,UserRole.admin): raise HTTPException(status_code=403,detail="Clinician access required")
    _can_access_patient(db,current_user,payload.patient_id)
    row=LabOrder(patient_id=payload.patient_id,clinician_id=current_user.id,test_name=payload.test_name,status="ordered")
    db.add(row); _notify(db,payload.patient_id,"New laboratory request",f"{payload.test_name} has been requested.","lab"); _audit(db,current_user,"lab.order","LabOrder",detail=payload.test_name); db.commit(); db.refresh(row); return row

@router.patch("/labs/{lab_id}")
def update_lab(lab_id:int,payload:LabResultUpdate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    if current_user.role not in (UserRole.doctor,UserRole.admin): raise HTTPException(status_code=403,detail="Clinician access required")
    row=db.get(LabOrder,lab_id)
    if not row: raise HTTPException(status_code=404,detail="Lab order not found")
    _can_access_patient(db,current_user,row.patient_id)
    for k,v in payload.model_dump().items(): setattr(row,k,v)
    row.resulted_at=datetime.utcnow(); _notify(db,row.patient_id,"Lab result available",f"Your {row.test_name} result is ready.","lab"); _audit(db,current_user,"lab.result","LabOrder",lab_id,row.test_name); db.commit(); db.refresh(row); return row

@router.get("/referrals")
def referrals(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    if current_user.role==UserRole.patient:
        return db.query(Referral).filter(Referral.patient_id==current_user.id).order_by(Referral.created_at.desc()).all()
    if current_user.role==UserRole.doctor:
        return db.query(Referral).filter(Referral.referring_clinician_id==current_user.id).order_by(Referral.created_at.desc()).all()
    return db.query(Referral).order_by(Referral.created_at.desc()).limit(200).all()

@router.post("/referrals",status_code=201)
def create_referral(payload:ReferralCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    if current_user.role not in (UserRole.doctor,UserRole.admin): raise HTTPException(status_code=403,detail="Clinician access required")
    _can_access_patient(db,current_user,payload.patient_id)
    row=Referral(referring_clinician_id=current_user.id,**payload.model_dump())
    db.add(row); _notify(db,payload.patient_id,"Referral created",f"A {payload.specialty} referral has been created.","referral"); _audit(db,current_user,"referral.create","Referral",detail=payload.specialty); db.commit(); db.refresh(row); return row

@router.get("/documents")
def documents(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    q=db.query(CareDocument)
    if current_user.role==UserRole.patient: q=q.filter(CareDocument.patient_id==current_user.id)
    elif current_user.role==UserRole.doctor:
        ids=[x[0] for x in db.query(Appointment.patient_id).filter(Appointment.doctor_id==current_user.id).distinct().all()]
        q=q.filter(CareDocument.patient_id.in_(ids)) if ids else q.filter(False)
    return q.order_by(CareDocument.created_at.desc()).all()

@router.post("/documents",status_code=201)
async def upload_document(file:UploadFile=File(...), patient_id:int|None=Form(None), db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    target=current_user.id if current_user.role==UserRole.patient else patient_id
    if not target: raise HTTPException(status_code=400,detail="patient_id is required")
    _can_access_patient(db,current_user,target)
    ext=Path(file.filename or "document").suffix.lower()
    if ext not in {".pdf",".txt"}: raise HTTPException(status_code=400,detail="Only PDF and TXT documents are supported")
    data=await file.read()
    if len(data)>8*1024*1024: raise HTTPException(status_code=413,detail="Document exceeds 8 MB")
    safe=re.sub(r"[^A-Za-z0-9._-]+","_",Path(file.filename or "document").name)
    stored=f"{target}_{int(datetime.utcnow().timestamp())}_{safe}"
    path=UPLOAD_ROOT/stored; path.write_bytes(data)
    extracted=""
    if ext==".txt": extracted=data.decode("utf-8",errors="ignore")[:20000]
    else:
        try:
            from pypdf import PdfReader
            reader=PdfReader(str(path)); extracted="\n".join((p.extract_text() or "") for p in reader.pages)[:20000]
        except Exception: extracted=""
    summary=(extracted[:700].strip()+("…" if len(extracted)>700 else "")) if extracted else "Document securely stored and ready for clinical review."
    row=CareDocument(patient_id=target,uploaded_by_id=current_user.id,filename=safe,media_type=file.content_type or "application/octet-stream",storage_path=str(path),extracted_text=extracted,summary=summary)
    db.add(row); _notify(db,target,"Document added",f"{safe} is now available in your health record.","document"); _audit(db,current_user,"document.upload","CareDocument",detail=safe); db.commit(); db.refresh(row); return row

@router.get("/preferences")
def get_preferences(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    row=db.query(UserPreference).filter(UserPreference.user_id==current_user.id).first()
    if not row:
        row=UserPreference(user_id=current_user.id); db.add(row); db.commit(); db.refresh(row)
    return row

@router.put("/preferences")
def update_preferences(payload:PreferenceUpdate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    row=db.query(UserPreference).filter(UserPreference.user_id==current_user.id).first() or UserPreference(user_id=current_user.id)
    for k,v in payload.model_dump().items(): setattr(row,k,v)
    db.add(row); _audit(db,current_user,"preferences.update","UserPreference",current_user.id); db.commit(); db.refresh(row); return row

@router.get("/notifications")
def notifications(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    rows=db.query(Notification).filter(Notification.user_id==current_user.id).order_by(Notification.created_at.desc()).limit(50).all()
    if not rows:
        db.add_all([
            Notification(user_id=current_user.id,title="Welcome to MediLink",body="Your connected care workspace is ready.",kind="system"),
            Notification(user_id=current_user.id,title="MediLink Watch",body="Connect a compatible device to keep your vitals in one place.",kind="watch"),
        ]); db.commit(); rows=db.query(Notification).filter(Notification.user_id==current_user.id).order_by(Notification.created_at.desc()).all()
    return rows

@router.post("/notifications/{notification_id}/read")
def mark_notification(notification_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    row=db.get(Notification,notification_id)
    if not row or row.user_id!=current_user.id: raise HTTPException(status_code=404,detail="Notification not found")
    row.is_read=True; db.commit(); return {"ok":True}

@router.get("/audit")
def audit(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    q=db.query(AuditEvent)
    if current_user.role!=UserRole.admin: q=q.filter(AuditEvent.actor_id==current_user.id)
    return q.order_by(AuditEvent.created_at.desc()).limit(100).all()

@router.get("/hospitals")
def hospitals(current_user:User=Depends(get_current_user)):
    return [
      {"id":"bristol-central","name":"MediLink Central Hospital","city":"Bristol","services":["Emergency care","General Medicine","Cardiology","Diagnostics"],"open_24h":True,"wait_minutes":18,"beds_available":24},
      {"id":"north-clinic","name":"Northside Specialist Centre","city":"Bristol","services":["Neurology","Dermatology","Orthopaedics"],"open_24h":False,"wait_minutes":12,"beds_available":8},
      {"id":"virtual-care","name":"MediLink Virtual Care Centre","city":"Online","services":["Video consultations","Follow-up care","Care navigation"],"open_24h":True,"wait_minutes":6,"beds_available":0},
    ]
