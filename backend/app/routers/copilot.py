import json
import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, UserRole
from app.models.health_record import HealthRecord
from app.models.appointment import Appointment
from app.models.care import MedicationOrder, LabOrder, Referral, CareDocument, CopilotConversation, CopilotMessage
from app.models.doctor import DoctorProfile, AvailabilitySlot
from app.ml.specialty_model import predict_specialties
from app.services.llm import generate_answer, llm_status

router = APIRouter(prefix="/api/v1/copilot", tags=["MediLink Copilot"])

SPECIALTY_TERMS = {
    "General Medicine": ("fever", "fatigue", "tired", "dizzy", "dizziness", "headache", "weakness", "unwell", "checkup", "general"),
    "Cardiology": ("palpitation", "palpitations", "heart racing", "irregular heartbeat", "blood pressure", "hypertension", "ankle swelling", "heart", "cardiac"),
    "Neurology": ("migraine", "headache", "numbness", "tingling", "tremor", "seizure", "memory", "balance", "vertigo", "nerve"),
    "Dermatology": ("rash", "skin", "acne", "eczema", "itch", "itching", "mole", "lesion", "hair loss"),
    "Gastroenterology": ("stomach", "abdominal", "abdomen", "nausea", "vomiting", "diarrhea", "diarrhoea", "constipation", "reflux", "heartburn", "bloating", "bowel"),
    "Respiratory Medicine": ("cough", "wheeze", "wheezing", "breathless", "shortness of breath", "asthma", "lung", "chest infection"),
    "Orthopaedics": ("joint pain", "knee", "shoulder", "hip", "back pain", "fracture", "sprain", "bone", "sports injury", "muscle injury"),
    "ENT": ("ear", "hearing", "sinus", "throat", "tonsil", "nose", "nasal", "voice", "swallowing"),
    "Mental Health": ("anxiety", "panic", "depression", "low mood", "stress", "insomnia", "sleep", "mental health"),
    "Women's Health": ("period", "menstrual", "pelvic", "pregnancy", "contraception", "gynaecology", "gynecology"),
}

URGENT_PATTERNS = (
    ("severe chest pain", "severe chest pain"),
    ("crushing chest pain", "crushing chest pain"),
    ("can't breathe", "severe breathing difficulty"),
    ("cannot breathe", "severe breathing difficulty"),
    ("struggling to breathe", "severe breathing difficulty"),
    ("face drooping", "possible stroke symptom"),
    ("slurred speech", "possible stroke symptom"),
    ("unconscious", "loss of consciousness"),
    ("heavy bleeding", "heavy bleeding"),
    ("severe bleeding", "severe bleeding"),
    ("overdose", "possible overdose"),
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=4000)
    conversation_id: int | None = None


class Source(BaseModel):
    title: str
    kind: str
    excerpt: str
    relevance: float


class SuggestedDoctor(BaseModel):
    doctor_id: int
    full_name: str
    specialty: str
    clinic: str
    consultation_type: str
    years_experience: int
    open_slots: int
    next_available_at: datetime | None
    match_score: float
    reason: str


class ChatResponse(BaseModel):
    conversation_id: int
    answer: str
    highlights: list[str]
    sources: list[Source]
    next_steps: list[str]
    safety_note: str
    intent: str = "record_question"
    suggested_specialties: list[str] = Field(default_factory=list)
    suggested_doctors: list[SuggestedDoctor] = Field(default_factory=list)
    urgent: bool = False
    engine: str = "record_grounded"
    model: str | None = None


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _urgent_signal(text: str):
    n = _normalise(text)
    for phrase, reason in URGENT_PATTERNS:
        if phrase in n:
            return True, reason
    return False, None


def _chunks(db: Session, user: User):
    chunks = []
    if user.role == UserRole.patient:
        records = db.query(HealthRecord).filter(HealthRecord.patient_id == user.id).order_by(HealthRecord.created_at.desc()).limit(30).all()
        for r in records:
            chunks.append((r.title, r.record_type, r.body, r.created_at.isoformat()))

        meds = db.query(MedicationOrder).filter(MedicationOrder.patient_id == user.id, MedicationOrder.status == "active").order_by(MedicationOrder.created_at.desc()).all()
        for m in meds:
            chunks.append((f"Medication: {m.name}", "medication", f"{m.name} {m.dose}. {m.schedule}. {m.instructions}. Next due: {m.next_due}.", m.created_at.isoformat()))

        labs = db.query(LabOrder).filter(LabOrder.patient_id == user.id).order_by(LabOrder.ordered_at.desc()).limit(20).all()
        for l in labs:
            text = f"Status: {l.status}. Result: {l.result_value or 'not recorded'}. Reference: {l.reference_range or 'not recorded'}. Interpretation: {l.interpretation or 'none recorded'}."
            chunks.append((l.test_name, "laboratory", text, l.ordered_at.isoformat()))

        appts = db.query(Appointment).filter(Appointment.patient_id == user.id).order_by(Appointment.scheduled_at.desc()).limit(15).all()
        for a in appts:
            doctor = db.get(User, a.doctor_id)
            doctor_name = doctor.full_name if doctor else "your clinician"
            status = a.status.value if hasattr(a.status, "value") else str(a.status)
            chunks.append((f"Appointment with {doctor_name}", "appointment", f"Reason: {a.reason}. Status: {status}. Scheduled: {a.scheduled_at.isoformat()}.", a.scheduled_at.isoformat()))

        docs = db.query(CareDocument).filter(CareDocument.patient_id == user.id).order_by(CareDocument.created_at.desc()).limit(12).all()
        for d in docs:
            text = d.summary or (d.extracted_text or "")[:1600]
            chunks.append((d.filename, "document", text, d.created_at.isoformat()))

        refs = db.query(Referral).filter(Referral.patient_id == user.id).order_by(Referral.created_at.desc()).limit(12).all()
        for r in refs:
            chunks.append((f"{r.specialty} referral", "referral", f"Reason: {r.reason}. Destination: {r.destination}. Urgency: {r.urgency}. Status: {r.status}.", r.created_at.isoformat()))
    return chunks


def _retrieve(question: str, chunks: list[tuple], top_k: int = 6):
    if not chunks:
        return []
    docs = [c[2] for c in chunks]
    try:
        vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=5000)
        mat = vec.fit_transform(docs + [question])
        sims = cosine_similarity(mat[-1], mat[:-1]).ravel()
        order = sims.argsort()[::-1][:top_k]
        return [(chunks[i], float(sims[i])) for i in order if sims[i] > 0 or i == order[0]]
    except Exception:
        return [(c, 0.1) for c in chunks[:top_k]]


def _conversation_context(db: Session, conversation_id: int | None, user_id: int) -> str:
    if not conversation_id:
        return ""
    c = db.get(CopilotConversation, conversation_id)
    if not c or c.user_id != user_id:
        return ""
    rows = db.query(CopilotMessage).filter(CopilotMessage.conversation_id == conversation_id).order_by(CopilotMessage.created_at.desc()).limit(10).all()
    rows.reverse()
    parts = [f"{m.role}: {m.content}" for m in rows]
    return "\n".join(parts)[-5000:]


def _detect_intent(message: str, context: str) -> str:
    q = _normalise(f"{context} {message}")
    if any(x in q for x in ["which doctor", "what doctor", "which specialist", "what specialist", "who should i see", "recommend a doctor", "find me a doctor", "book a doctor", "see a doctor"]):
        return "doctor_recommendation"
    if any(x in q for x in ["lab", "blood result", "blood test", "result", "cholesterol", "egfr", "cbc", "haemoglobin", "hemoglobin"]):
        return "result_explanation"
    if any(x in q for x in ["medicine", "medication", "dose", "prescription", "taking"]):
        return "medication_review"
    if any(x in q for x in ["appointment", "prepare", "consultation", "visit"]):
        return "appointment_preparation"
    if any(x in q for x in ["referral", "specialist referral"]):
        return "referral_status"
    symptom_hits = sum(1 for terms in SPECIALTY_TERMS.values() for term in terms if term in q)
    if symptom_hits >= 1 or any(x in q for x in ["symptom", "pain", "feel unwell", "feeling unwell", "what should i do"]):
        return "symptom_guidance"
    return "record_question"


def _specialty_suggestions(text: str) -> list[str]:
    prediction = predict_specialties(text)
    if prediction and prediction.get("ranked"):
        return [name for name, _prob in prediction["ranked"][:3]]

    n = _normalise(text)
    scored = []
    for specialty, terms in SPECIALTY_TERMS.items():
        matched = [t for t in terms if t in n]
        if matched:
            score = sum(2 if " " in t else 1 for t in matched)
            scored.append((specialty, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [s for s, _ in scored[:3]] or ["General Medicine"]


def _doctor_suggestions(db: Session, specialties: list[str]) -> list[SuggestedDoctor]:
    now = datetime.now()
    primary = specialties[0].lower() if specialties else "general medicine"
    secondary = {s.lower() for s in specialties[1:]}
    rows = db.query(User, DoctorProfile).join(DoctorProfile, DoctorProfile.user_id == User.id).filter(
        User.role == UserRole.doctor,
        User.is_active.is_(True),
        DoctorProfile.accepting_new_patients.is_(True),
    ).all()

    result = []
    for user, profile in rows:
        slots = db.query(AvailabilitySlot).filter(
            AvailabilitySlot.doctor_id == user.id,
            AvailabilitySlot.is_booked.is_(False),
            AvailabilitySlot.start_at > now,
        ).order_by(AvailabilitySlot.start_at.asc()).limit(8).all()

        specialty = profile.specialty.strip().lower()
        score = 10.0
        reason_parts = []
        if specialty == primary:
            score += 60
            reason_parts.append(f"specialises in {profile.specialty}")
        elif specialty in secondary:
            score += 38
            reason_parts.append(f"matches a related pathway ({profile.specialty})")
        elif primary in specialty or specialty in primary:
            score += 45
            reason_parts.append(f"closely matches {profile.specialty}")
        elif specialty == "general medicine":
            score += 24
            reason_parts.append("can provide a broad first assessment")

        score += min(max(profile.years_experience, 0), 20) * 0.8
        score += min(len(slots), 5) * 4
        if profile.years_experience:
            reason_parts.append(f"{profile.years_experience} years' listed experience")
        if slots:
            reason_parts.append(f"next slot {slots[0].start_at.strftime('%d %b %H:%M')}")
        else:
            reason_parts.append("no open slot currently listed")

        result.append(SuggestedDoctor(
            doctor_id=user.id,
            full_name=user.full_name,
            specialty=profile.specialty,
            clinic=profile.clinic,
            consultation_type=profile.consultation_type,
            years_experience=profile.years_experience,
            open_slots=len(slots),
            next_available_at=slots[0].start_at if slots else None,
            match_score=round(min(score, 99.0), 1),
            reason="; ".join(reason_parts[:3]).capitalize() + ".",
        ))

    result.sort(key=lambda d: (d.match_score, d.open_slots), reverse=True)
    return result[:4]


def _latest_labs(db: Session, user_id: int):
    return db.query(LabOrder).filter(LabOrder.patient_id == user_id).order_by(LabOrder.ordered_at.desc()).limit(8).all()


def _lab_answer(labs: list[LabOrder]):
    if not labs:
        return (
            "I don't currently have a laboratory result in your MediLink record to interpret.",
            [],
            ["Open Lab Results", "Upload or add the relevant report", "Message your care team if a result is missing"],
        )

    lines = []
    highlights = []
    flagged = []
    for lab in labs[:5]:
        result = lab.result_value or "not recorded"
        reference = lab.reference_range or "reference range not recorded"
        interpretation = (lab.interpretation or "").strip()
        line = f"{lab.test_name}: {result} (reference: {reference})"
        if interpretation:
            line += f" — {interpretation}"
        lines.append(line)
        highlights.append(line)
        low = interpretation.lower()
        if any(word in low for word in ["high", "low", "abnormal", "review", "elevated", "reduced", "outside"]):
            flagged.append(lab.test_name)

    if flagged:
        intro = f"I found {len(labs)} recent laboratory entries. The record specifically flags {', '.join(flagged[:3])} for attention or review."
    else:
        intro = f"I found {len(labs)} recent laboratory entries. None of the recorded interpretations in the latest results are explicitly marked abnormal."

    answer = intro + " Here is what is recorded: " + " ".join(lines[:4]) + " I can explain the terminology and trends, but a result should be interpreted alongside your symptoms, history, medications and the laboratory's own reference range."
    next_steps = ["Open the full Lab Results page", "Ask me about one specific test by name", "Discuss any flagged result with your clinician"]
    return answer, highlights[:5], next_steps


def _medication_answer(db: Session, user_id: int):
    meds = db.query(MedicationOrder).filter(MedicationOrder.patient_id == user_id, MedicationOrder.status == "active").order_by(MedicationOrder.created_at.desc()).all()
    if not meds:
        return "I don't currently see an active medication in your MediLink record.", [], ["Open Medications", "Check whether your prescription list is up to date", "Message your care team about missing medicines"]
    highlights = [f"{m.name} {m.dose} — {m.schedule}. {m.instructions}".strip() for m in meds[:6]]
    answer = "Your active MediLink medication list currently contains: " + " ".join(highlights) + " I can help you review timing, recorded instructions and possible questions to raise with your prescriber, but I won't tell you to start, stop or change a prescription on my own."
    return answer, highlights, ["Open Medications", "Ask about one medicine by name", "Contact your prescriber before changing a prescribed medicine"]


def _appointment_answer(db: Session, user_id: int):
    now = datetime.now()
    appt = db.query(Appointment).filter(Appointment.patient_id == user_id, Appointment.scheduled_at >= now).order_by(Appointment.scheduled_at.asc()).first()
    if not appt:
        return "You don't currently have a future appointment recorded in MediLink.", [], ["Find a doctor", "Use AI Doctor Matching", "Review your recent records before booking"]
    doctor = db.get(User, appt.doctor_id)
    doctor_name = doctor.full_name if doctor else "your clinician"
    answer = f"Your next appointment is with {doctor_name} on {appt.scheduled_at.strftime('%d %B %Y at %H:%M')} for: {appt.reason}. To prepare, note any changes since you booked, confirm your medication list, review recent results and write down the two or three questions you most want answered."
    highlights = [f"Clinician: {doctor_name}", f"Time: {appt.scheduled_at.strftime('%d %b %Y %H:%M')}", f"Reason: {appt.reason}"]
    return answer, highlights, ["Review medications", "Review recent lab results", "Prepare your top questions"]


def _compose_general(question: str, retrieved):
    facts = [x[0][2] for x in retrieved]
    if not facts:
        return (
            "I couldn't find enough information in your MediLink record to answer that reliably.",
            [],
            ["Ask a more specific question", "Upload a relevant record", "Message your care team"],
        )
    answer = "I found the following record context that is most relevant to your question: " + " ".join(facts[:3])
    return answer, facts[:4], ["Open the cited record items", "Ask a follow-up question", "Message your care team if you need a clinical decision"]


@router.get("/status")
def status(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.patient:
        raise HTTPException(status_code=403, detail="Patient Copilot access required")
    status = llm_status()
    return {
        **status,
        "record_grounding": True,
        "doctor_routing": True,
        "urgent_screening": True,
    }


@router.get("/conversations")
def conversations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = db.query(CopilotConversation).filter(CopilotConversation.user_id == current_user.id).order_by(CopilotConversation.updated_at.desc()).limit(30).all()
    return [{"id": r.id, "title": r.title, "created_at": r.created_at, "updated_at": r.updated_at} for r in rows]


@router.get("/conversations/{conversation_id}")
def conversation(conversation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.get(CopilotConversation, conversation_id)
    if not c or c.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    rows = db.query(CopilotMessage).filter(CopilotMessage.conversation_id == c.id).order_by(CopilotMessage.created_at.asc()).all()
    return [{"id": m.id, "role": m.role, "content": m.content, "sources": json.loads(m.sources_json or "[]"), "created_at": m.created_at} for m in rows]


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.patient:
        raise HTTPException(status_code=403, detail="Patient Copilot access required")

    c = None
    if payload.conversation_id:
        c = db.get(CopilotConversation, payload.conversation_id)
        if not c or c.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Conversation not found")
    if not c:
        c = CopilotConversation(user_id=current_user.id, title=payload.message.strip()[:70] or "Care conversation")
        db.add(c)
        db.flush()

    context = _conversation_context(db, c.id, current_user.id)
    urgent, urgent_reason = _urgent_signal(f"{context} {payload.message}")
    intent = _detect_intent(payload.message, context)
    db.add(CopilotMessage(conversation_id=c.id, role="user", content=payload.message))

    chunks = _chunks(db, current_user)
    retrieved = _retrieve(f"{context} {payload.message}", chunks)
    sources = [Source(title=x[0][0], kind=x[0][1], excerpt=x[0][2][:340], relevance=round(score, 3)) for x, score in retrieved]

    specialties: list[str] = []
    doctors: list[SuggestedDoctor] = []

    if urgent:
        answer = f"Your message includes a potentially urgent warning sign ({urgent_reason}). Don't rely on MediLink Copilot or routine appointment matching for this. If this is happening now or symptoms are severe, seek urgent medical help. In the UK, call 999 for an emergency or use NHS 111 when urgent advice is appropriate."
        highlights = [f"Urgent signal detected: {urgent_reason}"]
        next_steps = ["Use Emergency SOS", "Call 999 if this is an emergency", "Use NHS 111 for urgent advice when appropriate"]
        intent = "urgent_care"
    elif intent == "result_explanation":
        answer, highlights, next_steps = _lab_answer(_latest_labs(db, current_user.id))
    elif intent == "medication_review":
        answer, highlights, next_steps = _medication_answer(db, current_user.id)
    elif intent == "appointment_preparation":
        answer, highlights, next_steps = _appointment_answer(db, current_user.id)
    elif intent in {"doctor_recommendation", "symptom_guidance"}:
        combined = f"{context} {payload.message}".strip()
        specialties = _specialty_suggestions(combined)
        doctors = _doctor_suggestions(db, specialties)
        top = specialties[0] if specialties else "General Medicine"
        if intent == "doctor_recommendation":
            answer = f"Based on the symptoms and care need you've described, {top} is the strongest routine care pathway I can identify from MediLink's routing model."
        else:
            answer = f"The symptoms you've described most closely route toward {top} for a routine assessment. I can't diagnose the cause from chat, but I can help you organise the information a clinician will need and find an appropriate doctor."
        if doctors:
            answer += f" I found {len(doctors)} clinician option{'s' if len(doctors) != 1 else ''} with relevant profiles or availability."
        else:
            answer += " I don't currently see an available clinician profile that matches closely enough, so use the full doctor search or start with General Medicine."
        highlights = [f"Suggested pathway: {s}" for s in specialties[:3]]
        next_steps = ["Review the suggested doctors below", "Use Find a Doctor to compare availability", "Tell me how long the symptoms have been present and whether they are worsening"]
    elif intent == "referral_status":
        refs = db.query(Referral).filter(Referral.patient_id == current_user.id).order_by(Referral.created_at.desc()).limit(5).all()
        if refs:
            highlights = [f"{r.specialty}: {r.status} — {r.destination} ({r.urgency})" for r in refs]
            answer = "Here are the latest referrals recorded in MediLink: " + " ".join(highlights[:4])
            next_steps = ["Open Referrals", "Ask about one referral by specialty", "Message your care team if a referral appears delayed"]
        else:
            answer = "I don't currently see a referral recorded in your MediLink account."
            highlights = []
            next_steps = ["Open Referrals", "Ask your clinician whether a referral is needed", "Use doctor matching for routine specialist navigation"]
    else:
        answer, highlights, next_steps = _compose_general(payload.message, retrieved)

    engine = "record_grounded"
    model = None
    if not urgent:
        record_context = "\n".join(
            f"[{src.kind}] {src.title}: {src.excerpt}" for src in sources[:6]
        )
        personal_intents = {"result_explanation", "medication_review", "appointment_preparation", "referral_status", "record_question"}
        llm = generate_answer(
            user_message=payload.message,
            intent=intent,
            conversation_context=context,
            record_context=record_context,
            deterministic_answer=answer,
            specialties=specialties,
            doctors=[d.model_dump(mode="json") for d in doctors],
            contains_personal_record_context=intent in personal_intents,
        )
        if llm is not None:
            answer = llm.text
            engine = llm.engine
            model = llm.model

    safety = "MediLink Copilot can explain your recorded information, help you prepare for care and route you to appropriate services. It does not diagnose conditions or replace emergency or clinician-led care."
    assistant_sources = [s.model_dump() for s in sources]
    db.add(CopilotMessage(conversation_id=c.id, role="assistant", content=answer, sources_json=json.dumps(assistant_sources)))
    c.updated_at = datetime.utcnow()
    db.commit()

    return ChatResponse(
        conversation_id=c.id,
        answer=answer,
        highlights=highlights,
        sources=sources,
        next_steps=next_steps,
        safety_note=safety,
        intent=intent,
        suggested_specialties=specialties,
        suggested_doctors=doctors,
        urgent=urgent,
        engine=engine,
        model=model,
    )
