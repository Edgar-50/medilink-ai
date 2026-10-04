# MediLink v15.2 — Copilot Intelligence Upgrade

This patch upgrades Patient Copilot from basic record retrieval into a care-navigation assistant.

## New behaviour

- Detects conversational intent across follow-up messages.
- Explains the latest laboratory entries using the recorded result, reference range and clinician interpretation.
- Reviews the active medication list without instructing the patient to independently change prescribed treatment.
- Prepares the patient for the next actual appointment.
- Suggests suitable specialties from symptom descriptions using the existing specialty model/routing rules.
- Ranks real MediLink doctor profiles and their current open slots.
- Shows clinician match reasons and links patients into the booking workflow.
- Handles referral-status questions.
- Detects urgent warning phrases and routes away from routine Copilot advice.
- Continues to ground answers in MediLink record sources.
- Uses recent conversation turns so follow-ups such as “which doctor should I see?” retain context.

## Apply

Copy the `backend` and `frontend` folders over the existing MediLink v15 project and allow replacement of matching files.

Restart the backend:

```powershell
cd C:\Users\charl\OneDrive\Desktop\medilink-ai-starter\medilink-ai\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --reload-dir app
```

Restart the frontend:

```powershell
cd C:\Users\charl\OneDrive\Desktop\medilink-ai-starter\medilink-ai\frontend
npm.cmd run dev
```

## Useful Copilot tests

- `Explain my latest blood results in simple language.`
- `Which doctor should I see for recurring headaches and dizziness?`
- `I have a rash that keeps itching. Who should I book?`
- `Prepare me for my next appointment.`
- `What medicines am I currently taking?`
- `Do I have any referrals?`
- Follow-up: `Which of those doctors has availability?`

The Copilot is designed for record explanation, care preparation and navigation. It does not diagnose illness or independently change prescribed treatment.
