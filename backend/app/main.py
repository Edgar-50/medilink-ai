from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine
from app.routers import auth, appointments, health, ai, doctors, iot, experience, telehealth, clinical, admin, care, communications, copilot, advanced, realtime, platform
import app.models

Base.metadata.create_all(bind=engine)
app = FastAPI(title="MediLink API",version="1.6.0",description="Connected care, clinical workflows, remote monitoring, secure communication and record-grounded assistance.")
allowed_origins={settings.frontend_origin.rstrip("/"),"http://localhost:3000","http://127.0.0.1:3000"}
app.add_middleware(CORSMiddleware,allow_origins=sorted(allowed_origins),allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
for r in (auth.router,doctors.router,appointments.router,health.router,ai.router,iot.router,experience.router,telehealth.router,clinical.router,admin.router,care.router,communications.router,copilot.router,advanced.router,realtime.router,platform.router):app.include_router(r)

@app.get("/")
def root():
    return {"name":"MediLink","status":"online","version":"1.6.0","docs":"/docs","google_sign_in":"configured" if settings.google_client_id else "not_configured","capabilities":["patient_copilot","clinical_workspace","secure_messaging","telehealth","remote_monitoring","medications","laboratory_workflow","referrals","documents","audit_history","hospital_operations","electronic_prescribing","clinical_letters","risk_stratification","medication_interaction_review","fhir_interoperability","background_jobs","model_registry","drift_monitoring","connected_devices","historical_vitals","multi_facility_operations","bed_management","staff_roster","referral_queue","governance_exports","llm_copilot","provider_fallback","record_grounded_rag"]}
@app.get("/health")
def healthcheck():return {"status":"healthy","version":"1.6.0"}
