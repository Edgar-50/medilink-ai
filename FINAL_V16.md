# MediLink v16 — Final Integration Pass

v16 consolidates v15, the React navigation hotfix and the v15.2 Copilot upgrade, then adds an optional LLM layer without making the rest of MediLink dependent on an external model.

## Copilot architecture

1. urgent-symptom screening runs first;
2. MediLink retrieves the authenticated patient's relevant records;
3. specialty routing and clinician ranking run inside MediLink;
4. a deterministic grounded answer is produced;
5. an optional LLM rewrites/expands that answer using the supplied context;
6. if the LLM is unavailable, the grounded answer is returned unchanged.

This prevents an API outage from disabling the care assistant and prevents the LLM from inventing clinicians or availability.

## Enable OpenAI

Add to `backend/.env`:

```env
LLM_PROVIDER=auto
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-6-luna
LLM_ALLOW_RECORD_CONTEXT=false
```

Restart FastAPI. For personal-record explanations using the external LLM, explicitly set `LLM_ALLOW_RECORD_CONTEXT=true` only when your data-governance arrangements permit sending that context to the configured provider. The local record-grounded engine continues to handle record questions when this is false.

## Optional local LLM

```env
LLM_PROVIDER=ollama
OLLAMA_ENABLED=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
LLM_ALLOW_RECORD_CONTEXT=true
```

## Final checks

- `GET /health` -> 1.6.0
- `GET /api/v1/copilot/status` while authenticated as a patient
- Google login
- patient/doctor/admin RBAC
- Copilot lab/result question
- Copilot symptom -> specialty -> doctor question
- medication page
- messages persistence
- document upload
- WebRTC room creation/join
- Watch vitals
- clinician care actions
- admin network/platform/audit pages

The project still requires production validation, deployment hardening and regulated-healthcare governance before use with real clinical workflows.
