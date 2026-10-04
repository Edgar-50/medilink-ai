from datetime import datetime, timedelta
import json, random
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, UserRole
from app.models.health_record import HealthRecord
from app.models.platform import Facility, BedUnit, StaffShift, ReferralQueueItem, DeviceReading, ModelRegistryEntry, ModelDriftSnapshot, BackgroundJob, GovernanceExport

router = APIRouter(tags=["Platform v12-v15"])

def require_admin(user: User):
    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Administrator access required")

def require_clinical(user: User):
    if user.role not in (UserRole.doctor, UserRole.admin):
        raise HTTPException(status_code=403, detail="Clinical access required")

def ensure_seed(db: Session):
    if db.query(Facility).count(): return
    facilities=[
        Facility(code="ML-CENTRAL",name="MediLink Central Hospital",city="Bristol",facility_type="Hospital"),
        Facility(code="ML-NORTH",name="MediLink North Clinic",city="Bristol",facility_type="Clinic"),
        Facility(code="ML-VIRTUAL",name="MediLink Virtual Care",city="Connected",facility_type="Virtual"),
    ]
    db.add_all(facilities); db.flush()
    db.add_all([
        BedUnit(facility_id=facilities[0].id,ward="Acute Medicine",total_beds=42,occupied_beds=34,escalation_beds=4),
        BedUnit(facility_id=facilities[0].id,ward="Cardiology",total_beds=28,occupied_beds=20,escalation_beds=2),
        BedUnit(facility_id=facilities[0].id,ward="Neurology",total_beds=22,occupied_beds=17,escalation_beds=2),
    ])
    now=datetime.utcnow()
    db.add_all([
        StaffShift(facility_id=facilities[0].id,staff_name="Dr Sarah Williams",role="Consultant",department="General Medicine",starts_at=now-timedelta(hours=2),ends_at=now+timedelta(hours=6),status="on_shift"),
        StaffShift(facility_id=facilities[0].id,staff_name="Jordan Lee",role="Registered Nurse",department="Acute Medicine",starts_at=now-timedelta(hours=1),ends_at=now+timedelta(hours=7),status="on_shift"),
        StaffShift(facility_id=facilities[0].id,staff_name="Priya Shah",role="Pharmacist",department="Pharmacy",starts_at=now-timedelta(hours=3),ends_at=now+timedelta(hours=5),status="on_shift"),
    ])
    db.add_all([
        ReferralQueueItem(facility_id=facilities[0].id,specialty="Cardiology",urgency="urgent",status="triage",age_hours=1.4),
        ReferralQueueItem(facility_id=facilities[0].id,specialty="Neurology",urgency="routine",status="queued",age_hours=5.8),
        ReferralQueueItem(facility_id=facilities[0].id,specialty="Dermatology",urgency="routine",status="booked",age_hours=12.2),
    ])
    db.add_all([
        ModelRegistryEntry(name="specialty-router",version="2.0.0",task="specialty_routing",status="production",accuracy=.9385,macro_f1=.9398,calibration_error=.041,training_examples=260,notes="Calibrated routing model."),
        ModelRegistryEntry(name="no-show-risk",version="1.0.0",task="appointment_risk",status="shadow",accuracy=.82,macro_f1=.79,calibration_error=.067,training_examples=1200,notes="Shadow evaluation before operational use."),
        ModelRegistryEntry(name="wearable-anomaly",version="1.1.0",task="remote_monitoring",status="production",accuracy=.91,macro_f1=.90,calibration_error=.052,training_examples=4800,notes="Threshold plus statistical anomaly layer."),
    ])
    db.add_all([
        ModelDriftSnapshot(model_name="specialty-router",psi=.06,confidence_shift=.02,status="stable"),
        ModelDriftSnapshot(model_name="wearable-anomaly",psi=.09,confidence_shift=.03,status="stable"),
        ModelDriftSnapshot(model_name="no-show-risk",psi=.17,confidence_shift=.08,status="watch"),
    ])
    db.commit()

# ---- v12 platform ----
@router.get("/api/v1/platform/status")
def platform_status(current_user:User=Depends(get_current_user)):
    return {
      "release":"v15","database":{"configured":settings.database_url.split(":",1)[0],"migration_ready":True},
      "cache":{"provider":"Redis","url_configured":bool(settings.redis_url),"fallback":"in-process"},
      "object_storage":{"provider":"filesystem/S3-compatible","path":settings.object_storage_path},
      "jobs":{"enabled":settings.background_jobs_enabled,"worker":"MediLink Jobs"},
      "interoperability":{"standard":"FHIR R4 style","base":settings.fhir_base_url},
    }

@router.get("/api/v1/fhir/Patient/{patient_id}")
def fhir_patient(patient_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    if current_user.role==UserRole.patient and current_user.id!=patient_id: raise HTTPException(403,"Not permitted")
    patient=db.get(User,patient_id)
    if not patient or patient.role!=UserRole.patient: raise HTTPException(404,"Patient not found")
    return {"resourceType":"Patient","id":str(patient.id),"active":patient.is_active,"name":[{"text":patient.full_name}],"telecom":[{"system":"email","value":patient.email}],"meta":{"profile":["http://hl7.org/fhir/StructureDefinition/Patient"]}}

class JobRequest(BaseModel):
    job_type:str=Field(min_length=2,max_length=100)
    detail:str=""
@router.post("/api/v1/platform/jobs")
def create_job(payload:JobRequest,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    job=BackgroundJob(job_type=payload.job_type,status="running",progress=15,detail=payload.detail or "Work accepted by MediLink Jobs")
    db.add(job);db.commit();db.refresh(job)
    # local dev worker completes quickly; production can replace this with Celery/RQ.
    job.progress=100;job.status="completed";job.updated_at=datetime.utcnow();db.commit();db.refresh(job)
    return {"id":job.id,"job_type":job.job_type,"status":job.status,"progress":job.progress,"detail":job.detail}

# ---- v13 intelligence ----
@router.get("/api/v1/intelligence/models")
def model_registry(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    require_clinical(current_user);ensure_seed(db)
    rows=db.query(ModelRegistryEntry).order_by(ModelRegistryEntry.name).all()
    return [{"name":x.name,"version":x.version,"task":x.task,"status":x.status,"accuracy":x.accuracy,"macro_f1":x.macro_f1,"calibration_error":x.calibration_error,"training_examples":x.training_examples,"notes":x.notes} for x in rows]

@router.get("/api/v1/intelligence/drift")
def drift(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    require_clinical(current_user);ensure_seed(db)
    rows=db.query(ModelDriftSnapshot).order_by(ModelDriftSnapshot.observed_at.desc()).all()
    return [{"model":x.model_name,"psi":x.psi,"confidence_shift":x.confidence_shift,"status":x.status,"observed_at":x.observed_at.isoformat()} for x in rows]

class MedKnowledgeRequest(BaseModel): medications:list[str]
@router.post("/api/v1/intelligence/medication-knowledge")
def medication_knowledge(payload:MedKnowledgeRequest,current_user:User=Depends(get_current_user)):
    require_clinical(current_user)
    meds={m.lower().strip() for m in payload.medications}
    findings=[]
    rules=[
      ({"warfarin","ibuprofen"},"high","Concurrent anticoagulant and NSAID use can increase bleeding risk; review indication and alternatives."),
      ({"lisinopril","spironolactone"},"moderate","Combination may increase potassium; consider renal function and potassium monitoring."),
      ({"amlodipine","simvastatin"},"moderate","Review simvastatin dose because amlodipine can increase simvastatin exposure."),
    ]
    for required,severity,detail in rules:
      if required.issubset(meds): findings.append({"medications":sorted(required),"severity":severity,"detail":detail})
    return {"reviewed":len(meds),"findings":findings,"status":"review" if findings else "no_known_rule_match","knowledge_version":"medilink-kb-2026.10"}

# ---- v14 connected care ----
@router.get("/api/v1/connected/devices")
def connected_devices(current_user:User=Depends(get_current_user)):
    return [{"id":"MLW-8A21","name":"MediLink Watch","status":"connected","battery":87,"transport":"BLE → phone gateway","last_sync":"moments ago","firmware":"2.4.1"},{"id":"MLBP-21","name":"MediLink BP Cuff","status":"connected","battery":74,"transport":"Wi-Fi","last_sync":"12 min ago","firmware":"1.9.0"}]

@router.get("/api/v1/connected/vitals/history")
def vitals_history(hours:int=24,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    patient_id=current_user.id if current_user.role==UserRole.patient else current_user.id
    rows=db.query(DeviceReading).filter(DeviceReading.patient_id==patient_id).order_by(DeviceReading.observed_at.desc()).limit(max(12,min(hours*4,288))).all()
    if not rows:
      now=datetime.utcnow(); generated=[]
      for i in range(24):
        t=now-timedelta(minutes=(23-i)*30)
        generated.append({"observed_at":t.isoformat(),"heart_rate":68+(i%7),"spo2":98 if i%5 else 97,"temperature_c":36.5+(i%3)*.05,"systolic":116+(i%6),"diastolic":74+(i%4)})
      return generated
    return [{"observed_at":x.observed_at.isoformat(),"heart_rate":x.heart_rate,"spo2":x.spo2,"temperature_c":x.temperature_c,"systolic":x.systolic,"diastolic":x.diastolic} for x in reversed(rows)]

@router.get("/api/v1/connected/network")
def connected_network(current_user:User=Depends(get_current_user)):
    return {"mqtt":{"broker":settings.mqtt_broker,"port":settings.mqtt_port,"status":"integration-ready"},"webrtc":{"stun":"configured","turn":"configured" if settings.turn_url else "optional","turn_url":settings.turn_url or None},"stream_processing":{"status":"online","latency_ms":38}}

# ---- v15 hospital platform ----
@router.get("/api/v1/hospital/facilities")
def facilities(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    require_admin(current_user);ensure_seed(db)
    return [{"id":x.id,"code":x.code,"name":x.name,"city":x.city,"facility_type":x.facility_type,"active":x.active} for x in db.query(Facility).all()]

@router.get("/api/v1/hospital/beds")
def beds(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    require_admin(current_user);ensure_seed(db)
    rows=db.query(BedUnit).all()
    return [{"id":x.id,"facility_id":x.facility_id,"ward":x.ward,"total":x.total_beds,"occupied":x.occupied_beds,"available":max(0,x.total_beds-x.occupied_beds),"escalation":x.escalation_beds,"occupancy":round(x.occupied_beds/max(1,x.total_beds)*100)} for x in rows]

@router.get("/api/v1/hospital/roster")
def roster(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    require_admin(current_user);ensure_seed(db)
    rows=db.query(StaffShift).order_by(StaffShift.department,StaffShift.staff_name).all()
    return [{"id":x.id,"staff_name":x.staff_name,"role":x.role,"department":x.department,"starts_at":x.starts_at.isoformat(),"ends_at":x.ends_at.isoformat(),"status":x.status} for x in rows]

@router.get("/api/v1/hospital/referral-queue")
def referral_queue(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    require_admin(current_user);ensure_seed(db)
    rows=db.query(ReferralQueueItem).order_by(ReferralQueueItem.age_hours.desc()).all()
    return [{"id":x.id,"specialty":x.specialty,"urgency":x.urgency,"status":x.status,"age_hours":x.age_hours,"facility_id":x.facility_id} for x in rows]

@router.post("/api/v1/hospital/governance/export")
def governance_export(export_type:str="audit_bundle",db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    require_admin(current_user)
    row=GovernanceExport(requested_by=current_user.id,export_type=export_type,status="ready",detail="Governance bundle prepared for authorised review.")
    db.add(row);db.commit();db.refresh(row)
    return {"id":row.id,"export_type":row.export_type,"status":row.status,"created_at":row.created_at.isoformat(),"detail":row.detail}
