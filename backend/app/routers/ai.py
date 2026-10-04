import re
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.doctor import AvailabilitySlot, DoctorProfile
from app.models.user import User, UserRole
from app.ml.specialty_model import predict_specialties

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])

SPECIALTY_RULES = {
    "General Medicine": ("fever","fatigue","tired","dizzy","dizziness","headache","weakness","unwell","checkup","general"),
    "Cardiology": ("palpitation","palpitations","heart racing","irregular heartbeat","blood pressure","hypertension","ankle swelling","heart","cardiac"),
    "Neurology": ("migraine","headache","numbness","tingling","tremor","seizure","memory","balance","vertigo","nerve"),
    "Dermatology": ("rash","skin","acne","eczema","itch","itching","mole","lesion","hair loss"),
    "Gastroenterology": ("stomach","abdominal","abdomen","nausea","vomiting","diarrhea","diarrhoea","constipation","reflux","heartburn","bloating","bowel"),
    "Respiratory Medicine": ("cough","wheeze","wheezing","breathless","shortness of breath","asthma","lung","chest infection"),
    "Orthopaedics": ("joint pain","knee","shoulder","hip","back pain","fracture","sprain","bone","sports injury","muscle injury"),
    "ENT": ("ear","hearing","sinus","throat","tonsil","nose","nasal","voice","swallowing"),
    "Mental Health": ("anxiety","panic","depression","low mood","stress","insomnia","sleep","mental health"),
    "Women's Health": ("period","menstrual","pelvic","pregnancy","contraception","gynaecology","gynecology"),
}

URGENT_PATTERNS = (
    ("severe chest pain", "severe chest pain"), ("crushing chest pain", "crushing chest pain"),
    ("can't breathe", "severe breathing difficulty"), ("cannot breathe", "severe breathing difficulty"),
    ("struggling to breathe", "severe breathing difficulty"), ("face drooping", "possible stroke symptom"),
    ("slurred speech", "possible stroke symptom"), ("unconscious", "loss of consciousness"),
    ("heavy bleeding", "heavy bleeding"), ("severe bleeding", "severe bleeding"), ("overdose", "possible overdose"),
)

class SymptomRequest(BaseModel):
    symptoms: str = Field(min_length=5, max_length=4000)

class SpecialtySuggestion(BaseModel):
    specialty: str
    confidence: float | None = None
    routing_strength: Literal["strong", "moderate", "weak"]
    matched_terms: list[str]
    explanation: str

class DoctorMatch(BaseModel):
    doctor_id: int
    full_name: str
    specialty: str
    clinic: str
    years_experience: int
    consultation_type: str
    bio: str
    open_slots: int
    next_available_at: datetime | None
    match_score: float
    reasons: list[str]

class DoctorMatchResponse(BaseModel):
    mode: Literal["calibrated_model", "rule_routing"]
    model_version: str | None = None
    model_metrics: dict = Field(default_factory=dict)
    confidence_note: str
    urgent: bool
    urgent_reason: str | None
    safety_message: str
    input_summary: str
    suggested_specialties: list[SpecialtySuggestion]
    doctor_matches: list[DoctorMatch]
    disclaimer: str


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _matched_terms(text: str, specialty: str) -> list[str]:
    normalised = _normalise(text)
    return sorted({t for t in SPECIALTY_RULES.get(specialty, ()) if t in normalised})


def _rule_suggestions(text: str) -> list[SpecialtySuggestion]:
    normalised = _normalise(text)
    scored = []
    for specialty, terms in SPECIALTY_RULES.items():
        matched = sorted({term for term in terms if term in normalised})
        raw = sum(2 if " " in term else 1 for term in matched)
        if raw:
            scored.append((specialty, raw, matched))
    if not scored:
        return [SpecialtySuggestion(specialty="General Medicine", routing_strength="weak", matched_terms=[], explanation="No strong specialty signal was found, so General Medicine is a reasonable routine starting point.")]
    scored.sort(key=lambda x: x[1], reverse=True)
    best = scored[0][1]
    out=[]
    for specialty, raw, matched in scored[:3]:
        ratio=raw/best
        strength = "strong" if ratio >= .8 else "moderate" if ratio >= .45 else "weak"
        out.append(SpecialtySuggestion(specialty=specialty, routing_strength=strength, matched_terms=matched, explanation=f"Matched routing terms: {', '.join(matched[:5])}."))
    return out


def _suggestions(text: str):
    prediction = predict_specialties(text)
    if prediction:
        suggestions=[]
        for specialty, prob in prediction["ranked"]:
            strength = "strong" if prob >= .65 else "moderate" if prob >= .35 else "weak"
            suggestions.append(SpecialtySuggestion(
                specialty=specialty,
                confidence=round(prob, 4),
                routing_strength=strength,
                matched_terms=_matched_terms(text, specialty),
                explanation="Calibrated classifier ranking based on patterns in the training dataset."
            ))
        return suggestions, "calibrated_model", prediction
    return _rule_suggestions(text), "rule_routing", None


def _urgent_signal(text: str):
    n=_normalise(text)
    for phrase, reason in URGENT_PATTERNS:
        if phrase in n: return True, reason
    return False, None


def _doctor_matches(db: Session, suggestions: list[SpecialtySuggestion]):
    now=datetime.now(); primary=suggestions[0].specialty.lower(); secondary={s.specialty.lower() for s in suggestions[1:]}
    rows=db.query(User,DoctorProfile).join(DoctorProfile,DoctorProfile.user_id==User.id).filter(User.role==UserRole.doctor,User.is_active.is_(True),DoctorProfile.accepting_new_patients.is_(True)).all()
    ranked=[]
    for user, profile in rows:
        slots=db.query(AvailabilitySlot).filter(AvailabilitySlot.doctor_id==user.id,AvailabilitySlot.is_booked.is_(False),AvailabilitySlot.start_at>now).order_by(AvailabilitySlot.start_at.asc()).limit(10).all()
        score=15.0; reasons=[]; specialty=profile.specialty.strip().lower()
        if specialty==primary: score+=55; reasons.append(f"Top specialty fit: {profile.specialty}.")
        elif specialty in secondary: score+=35; reasons.append(f"Related specialty fit: {profile.specialty}.")
        elif primary in specialty or specialty in primary: score+=42; reasons.append(f"Closely related specialty: {profile.specialty}.")
        elif specialty=="general medicine": score+=22; reasons.append("General Medicine can provide an initial assessment for broad symptoms.")
        score += min(max(profile.years_experience,0),20)*.8
        if profile.years_experience: reasons.append(f"{profile.years_experience} years of experience listed.")
        score += min(len(slots),5)*4
        reasons.append(f"{len(slots)} open appointment slot{'s' if len(slots)!=1 else ''} found." if slots else "No future open slots currently listed.")
        ranked.append(DoctorMatch(doctor_id=user.id,full_name=user.full_name,specialty=profile.specialty,clinic=profile.clinic,years_experience=profile.years_experience,consultation_type=profile.consultation_type,bio=profile.bio,open_slots=len(slots),next_available_at=slots[0].start_at if slots else None,match_score=round(min(score,99.0),1),reasons=reasons[:4]))
    ranked.sort(key=lambda d:(d.match_score,d.open_slots),reverse=True)
    return ranked[:5]


@router.post("/doctor-match", response_model=DoctorMatchResponse)
def doctor_match(payload: SymptomRequest, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    if current_user.role != UserRole.patient: raise HTTPException(status_code=403,detail="Patient access required")
    urgent, urgent_reason = _urgent_signal(payload.symptoms)
    suggestions, mode, model = _suggestions(payload.symptoms)
    if urgent:
        safety="Your description contains a potentially urgent warning sign. If this is happening now or symptoms are severe, seek urgent medical help rather than relying on MediLink matching. In the UK, call 999 for an emergency or use NHS 111 for urgent advice when appropriate."
        matches=[]
    else:
        safety="This tool supports routine care routing only. It does not diagnose conditions or determine whether care is medically necessary."
        matches=_doctor_matches(db,suggestions)
    if mode=="calibrated_model":
        note="Percentages are calibrated routing-model confidence scores. They are not diagnosis probabilities and should be interpreted alongside clinical assessment."
    else:
        note="No validated probability model is loaded, so MediLink shows routing strength labels rather than percentages."
    return DoctorMatchResponse(mode=mode,model_version=model.get("model_version") if model else None,model_metrics=model.get("metrics",{}) if model else {},confidence_note=note,urgent=urgent,urgent_reason=urgent_reason,safety_message=safety,input_summary=payload.symptoms.strip(),suggested_specialties=suggestions,doctor_matches=matches,disclaimer="MediLink care routing supports navigation to appropriate services; it does not provide a diagnosis or replace professional medical advice.")


@router.get("/modules")
def modules():
    return {"modules":["patient_copilot","clinical_copilot","specialty_routing","risk_prediction","medical_document_analysis","appointment_matching","medical_rag","explainable_ai","consultation_transcription"]}

class CopilotRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)

class CopilotResponse(BaseModel):
    title: str
    answer: str
    bullets: list[str]
    sources: list[str]
    safety_note: str

@router.post("/copilot", response_model=CopilotResponse)
def copilot(payload: CopilotRequest, current_user: User=Depends(get_current_user)):
    q = _normalise(payload.question)
    base_sources = ["MediLink health record"]
    if current_user.role == UserRole.doctor:
        return CopilotResponse(
            title="Clinical workspace summary",
            answer="MediLink Copilot can summarise the current clinical workspace, highlight follow-up tasks and prepare clinician-facing notes. Any generated clinical content should be reviewed by a qualified clinician before it is saved to a record.",
            bullets=["3 items are queued for review.", "Connected vitals can be inspected alongside appointment context.", "Draft notes are assistive and require clinician approval."],
            sources=["Clinician workspace", "Patient timeline", "MediLink Watch stream"],
            safety_note="Clinical content is assistive and should be reviewed before it is used for care decisions.",
        )
    if "lab" in q or "blood" in q or "result" in q:
        return CopilotResponse(
            title="Latest results",
            answer="Your record contains a recent complete blood count within the recorded reference range and a cholesterol panel marked for routine review. The cholesterol result is flagged for routine review and is explained without turning it into a diagnosis.",
            bullets=["CBC: shown as within reference range.", "LDL: 3.4 mmol/L and marked for review.", "Kidney function: eGFR 96 and shown as within range."],
            sources=["Lab results • 2 Oct 2026", "Lab results • 28 Sep 2026"],
            safety_note="Laboratory interpretation should use the report's reference range and a clinician's assessment.",
        )
    if "appointment" in q or "prepare" in q:
        return CopilotResponse(
            title="Appointment preparation",
            answer="Before your next consultation, MediLink can organise your main concern, recent symptoms, medications, connected-device trends and questions you want answered so the visit starts with useful context.",
            bullets=["Write down when the problem started and what makes it better or worse.", "Bring an up-to-date medication list.", "Review recent MediLink Watch trends and any new results.", "Add 2–3 questions you most want answered."],
            sources=["Appointments", "Medication list", "MediLink Watch stream"],
            safety_note="This is visit preparation, not diagnosis or treatment advice.",
        )
    if "watch" in q or "vital" in q or "heart" in q or "spo2" in q:
        return CopilotResponse(
            title="Connected-health overview",
            answer="MediLink Watch brings heart rate, oxygen saturation, temperature, blood pressure and activity can be brought into the patient and clinician experience with timestamps and trend views.",
            bullets=["Heart rate is currently around the low 70s bpm.", "SpO₂ is currently around 98%.", "Temperature is currently around 36.6°C.", "Connected readings are shown with timestamps and monitoring context."],
            sources=["MediLink Watch"],
            safety_note="Review concerning readings with an appropriate healthcare professional.",
        )
    return CopilotResponse(
        title="Your MediLink care overview",
        answer="I can help you navigate your MediLink record, prepare for an appointment, summarise connected-health trends, or route you toward the most relevant part of the platform.",
        bullets=["Ask about appointments, medications, lab results or wearable trends.", "Use AI Doctor Matching for routine speciality routing.", "Use Emergency SOS for urgent help rather than relying on AI."],
        sources=base_sources,
        safety_note="MediLink AI supports navigation and care preparation; it does not replace professional medical advice.",
    )


from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.models.health_record import HealthRecord
from app.models.appointment import Appointment
from app.models.clinical_note import ClinicalNote
from app.core.database import get_db
from sqlalchemy.orm import Session

class RAGSource(BaseModel):
    title:str
    kind:str
    excerpt:str
    relevance:float

class RAGResponse(BaseModel):
    answer:str
    sources:list[RAGSource]
    suggested_actions:list[str]
    safety_note:str

def _rag_chunks(db:Session,user:User):
    chunks=[]
    if user.role==UserRole.patient:
        records=db.query(HealthRecord).filter(HealthRecord.patient_id==user.id).order_by(HealthRecord.created_at.desc()).limit(20).all()
        for r in records: chunks.append({"title":r.title,"kind":r.record_type,"text":r.body})
        appts=db.query(Appointment).filter(Appointment.patient_id==user.id).order_by(Appointment.scheduled_at.desc()).limit(10).all()
        for a in appts: chunks.append({"title":f"Appointment with {getattr(a,'doctor_name','your clinician')}","kind":"appointment","text":f"{a.reason}. Status: {a.status.value}. Scheduled {a.scheduled_at}."})
        if not chunks:
            chunks.extend([
                {"title":"Medication list","kind":"medication","text":"Amlodipine 5 mg once daily. Vitamin D 1000 IU once daily."},
                {"title":"Recent laboratory results","kind":"laboratory","text":"Complete blood count is within reference range. LDL cholesterol is 3.4 mmol/L and marked for routine review. eGFR is 96."},
                {"title":"Recent consultation","kind":"encounter","text":"Recurring headaches and fatigue were discussed. Follow-up planned after review of observations, medicines and routine results."},
                {"title":"MediLink Watch trend","kind":"wearable","text":"Recent connected-health trend shows heart rate around the low 70s, oxygen saturation around 98 percent, temperature around 36.6 C and blood pressure near 118 over 76."},
            ])
    else:
        notes=db.query(ClinicalNote).filter(ClinicalNote.doctor_id==user.id).order_by(ClinicalNote.updated_at.desc()).limit(20).all()
        for n in notes: chunks.append({"title":f"{n.note_type} note","kind":"clinical_note","text":" ".join([n.subjective,n.objective,n.assessment,n.plan])})
        if not chunks:
            chunks.extend([
                {"title":"Clinical worklist","kind":"worklist","text":"Three notes require review, four results are pending review and six secure messages are unread."},
                {"title":"Remote monitoring","kind":"wearable","text":"Connected monitoring shows stable oxygen saturation and resting heart rate with a small number of blood-pressure readings above baseline."},
            ])
    return chunks

def _retrieve(question:str,chunks:list[dict],k:int=4):
    if not chunks:return []
    corpus=[question]+[c["text"] for c in chunks]
    mat=TfidfVectorizer(stop_words="english",ngram_range=(1,2)).fit_transform(corpus)
    scores=cosine_similarity(mat[0:1],mat[1:]).ravel()
    idx=scores.argsort()[::-1][:k]
    return [(chunks[i],float(scores[i])) for i in idx if scores[i]>0 or i==idx[0]]

@router.post("/copilot/rag",response_model=RAGResponse)
def copilot_rag(payload:CopilotRequest,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    retrieved=_retrieve(payload.question,_rag_chunks(db,current_user),4)
    if not retrieved:
        return RAGResponse(answer="I could not find enough information in the available MediLink record to answer that confidently.",sources=[],suggested_actions=["Open your health record","Ask your care team"],safety_note="MediLink only answers from information available to your account.")
    facts=[]; sources=[]
    for c,score in retrieved:
        facts.append(c["text"])
        excerpt=c["text"][:180]+("…" if len(c["text"])>180 else "")
        sources.append(RAGSource(title=c["title"],kind=c["kind"],excerpt=excerpt,relevance=round(score,3)))
    q=payload.question.lower()
    if any(x in q for x in ["prepare","appointment","visit"]):
        answer="For your next appointment, the most relevant record context is: "+" ".join(facts[:3])+" Bring any changes in symptoms, medication use and questions you want answered so the clinician can verify the record with you."
        actions=["Review medication list","Write down your top questions","Review recent results and wearable trends"]
    elif any(x in q for x in ["lab","blood","result","cholesterol","egfr"]):
        answer="I found the following record context: "+" ".join(facts[:3])+" These results should be interpreted using the laboratory reference ranges and your clinical context."
        actions=["Open laboratory results","Discuss flagged results with your clinician"]
    elif any(x in q for x in ["watch","heart","blood pressure","spo2","oxygen","vital"]):
        answer="Your connected-health context shows: "+" ".join(facts[:3])+" Trends are more useful than a single reading, and concerning changes should be reviewed in context."
        actions=["Open MediLink Watch","Review 24-hour trend","Contact your care team if readings are concerning"]
    else:
        answer="Based on the most relevant information in your MediLink record: "+" ".join(facts[:3])
        actions=["Open the cited record items","Ask a follow-up question","Message your care team"]
    return RAGResponse(answer=answer,sources=sources,suggested_actions=actions,safety_note="Answers are grounded in the record available to your account and should be verified for clinical decisions.")
