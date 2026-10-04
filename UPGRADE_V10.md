# MediLink v10 — Connected Care Platform

v10 turns MediLink into a broader longitudinal-care product rather than a dashboard collection.

## New in v10

- Persistent secure patient/clinician message threads
- Medication and prescription workflow
- Laboratory orders and result workflow
- Specialist referrals
- Health-document upload with PDF/TXT extraction
- Patient notification centre
- User profile and reminder preferences
- Hospital and clinic directory
- Audit-event persistence
- Persistent Patient Copilot conversations
- Record-grounded Copilot retrieval across records, medications, labs, appointments, referrals and documents
- Expanded patient and clinician navigation
- Product launcher in the global top bar
- Improved light-mode contrast, especially Sign out
- v10 visual polish for Copilot, results, documents, referrals and care network pages

## Product principles

MediLink keeps care-routing confidence separate from diagnosis. Clinical notes, results and care recommendations remain reviewable by clinicians, while emergency flows stay outside automated diagnosis logic.

## New routes

Frontend:

- `/copilot`
- `/medications`
- `/labs`
- `/documents`
- `/referrals`
- `/hospitals`
- `/notifications`
- `/settings`
- `/messages` now uses persistent backend conversations

Backend:

- `/api/v1/copilot/*`
- `/api/v1/care/*`
- `/api/v1/messages/*`

## Installation

Overlay this patch on top of your existing v9 project, keeping `.env`, `.env.local`, `.venv`, `node_modules` and your existing SQLite database.

Then run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --reload-dir app
```

In another terminal:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

FastAPI creates the new SQLite tables automatically on startup.
