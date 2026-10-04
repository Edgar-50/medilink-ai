from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

import httpx

from app.core.config import settings


@dataclass
class LLMResult:
    text: str
    engine: str
    model: str | None = None


def _system_instructions() -> str:
    return """You are MediLink Copilot, a healthcare navigation and health-record explanation assistant.

Rules:
- Do not claim to diagnose a condition or replace a clinician.
- Personal facts must come only from the supplied MediLink context. Never invent a result, medication, appointment, referral, doctor, diagnosis, or observation.
- You may give general educational health information when it helps, but explicitly distinguish it from facts in the patient's record.
- Do not tell a patient to start, stop, increase, decrease, or substitute a prescribed medication. You may help them prepare questions for their prescriber.
- For lab results, explain the recorded value/reference/interpretation and relevant general concepts, while noting that ranges and clinical meaning depend on context.
- For clinician navigation, only mention clinicians supplied in the available-clinicians section. Do not invent clinicians or availability.
- Prefer useful next actions: what to monitor, what information to bring, what question to ask, which MediLink feature to open, or which listed clinician pathway fits.
- If information is missing, say exactly what is missing rather than guessing.
- The application performs urgent-symptom screening before calling you. If the user's text still sounds immediately dangerous, advise urgent emergency assessment rather than routine chat.
- Use clear, calm language. Avoid excessive disclaimers. Answer the user's actual question first.
"""


def _openai_answer(prompt: str) -> LLMResult:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key, timeout=settings.llm_timeout_seconds)
    response = client.responses.create(
        model=settings.openai_model,
        instructions=_system_instructions(),
        input=prompt,
    )
    text = (getattr(response, "output_text", "") or "").strip()
    if not text:
        raise RuntimeError("LLM returned an empty response")
    return LLMResult(text=text, engine="openai", model=settings.openai_model)


def _ollama_answer(prompt: str) -> LLMResult:
    url = settings.ollama_base_url.rstrip("/") + "/api/chat"
    payload = {
        "model": settings.ollama_model,
        "stream": False,
        "messages": [
            {"role": "system", "content": _system_instructions()},
            {"role": "user", "content": prompt},
        ],
        "options": {"temperature": 0.25},
    }
    with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
    text = str((data.get("message") or {}).get("content") or "").strip()
    if not text:
        raise RuntimeError("Local LLM returned an empty response")
    return LLMResult(text=text, engine="ollama", model=settings.ollama_model)


def llm_status() -> dict[str, Any]:
    provider = settings.llm_provider.lower().strip()
    if provider == "auto":
        if settings.openai_api_key:
            provider = "openai"
        elif settings.ollama_enabled:
            provider = "ollama"
        else:
            provider = "local"
    configured = (
        provider == "local"
        or (provider == "openai" and bool(settings.openai_api_key))
        or (provider == "ollama" and settings.ollama_enabled)
    )
    model = settings.openai_model if provider == "openai" else settings.ollama_model if provider == "ollama" else None
    return {
        "provider": provider,
        "configured": configured,
        "model": model,
        "record_context_enabled": bool(settings.llm_allow_record_context),
    }


def generate_answer(
    *,
    user_message: str,
    intent: str,
    conversation_context: str,
    record_context: str,
    deterministic_answer: str,
    specialties: list[str],
    doctors: list[dict[str, Any]],
    contains_personal_record_context: bool,
) -> LLMResult | None:
    status = llm_status()
    provider = status["provider"]
    if provider == "local" or not status["configured"]:
        return None

    # External model calls must not receive patient-record content unless the
    # operator has deliberately enabled it. Symptom/care-navigation questions
    # can still benefit from an LLM without transmitting stored records.
    include_record = settings.llm_allow_record_context
    if contains_personal_record_context and not include_record:
        return None

    doctor_text = "\n".join(
        f"- {d.get('full_name')}: {d.get('specialty')}; {d.get('clinic')}; "
        f"match {d.get('match_score')}/100; open slots {d.get('open_slots')}; {d.get('reason')}"
        for d in doctors[:5]
    ) or "No clinician matches were supplied."

    prompt = f"""CURRENT USER MESSAGE
{user_message}

DETECTED INTENT
{intent}

RECENT CONVERSATION CONTEXT
{conversation_context or 'No earlier context.'}

MEDILINK RECORD CONTEXT
{record_context if include_record else 'Patient record context is not being sent to this model.'}

ROUTING PATHWAYS
{', '.join(specialties) if specialties else 'No specialty pathway was computed.'}

AVAILABLE CLINICIANS
{doctor_text}

STRUCTURED MEDILINK RESPONSE
{deterministic_answer if include_record or not contains_personal_record_context else 'Not supplied because it contains patient-record content.'}

Write the best final reply to the user. Preserve any exact record values that are supplied; never invent missing values. If listed clinicians are relevant, explain why one or two are suitable while keeping the app's match score distinct from diagnostic probability. Keep the answer conversational and useful, usually 2-6 short paragraphs or concise bullets when appropriate.
"""

    try:
        if provider == "openai":
            return _openai_answer(prompt)
        if provider == "ollama":
            return _ollama_answer(prompt)
    except Exception:
        # Copilot must remain usable if an external provider is unavailable.
        return None
    return None
