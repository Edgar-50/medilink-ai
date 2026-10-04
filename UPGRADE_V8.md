# MediLink Premium v8

MediLink v8 turns the existing authenticated care platform into a fuller connected-health product demo.

## New experience layer

- Rod of Asclepius MediLink identity
- Persistent light/dark theme toggle
- Care-image carousel
- Redesigned patient command centre
- Redesigned clinician command centre
- Notifications popover and richer navigation
- Responsive mobile/tablet layouts

## Connected health / IoT

New API endpoints:

- `GET /api/v1/iot/devices`
- `GET /api/v1/iot/vitals/live`

The current stream is **synthetic**. It intentionally behaves like a connected MediLink Watch so the UI and API contract can be developed before physical hardware is connected.

## Patient experience

- Live wearable dashboard
- Health insights
- Medication list
- Lab result summaries
- Longitudinal timeline
- MediLink Copilot
- Secure-message demo
- Video consultation room
- Emergency SOS flow

## Clinician experience

- Patient queue
- Remote vitals panel
- Clinical alerts
- AI clinical brief
- Worklist
- Secure video-room access
- Clinical Copilot

## Telehealth

`POST /api/v1/telehealth/rooms` creates authenticated development-room metadata.

The browser consultation page can request local camera/microphone access. Production remote calling still needs signalling plus STUN/TURN infrastructure. Do not describe the local demo as a production telemedicine deployment.

## AI specialty model

The v8 demo model was actually trained before packaging on **260 synthetic examples** across 10 specialty classes.

Held-out synthetic test metrics:

- Accuracy: **0.9385**
- Macro F1: **0.9398**
- Weighted F1: **0.9392**
- Top-2 accuracy: **0.9538**
- Log loss: **0.5805**
- Test examples: **65**

These numbers are **not clinical accuracy** and must not be presented as real-world medical performance. The data is deliberately synthetic and contains clearer class signals than real patient language.

Artifact:

`backend/ml/artifacts/specialty_router.joblib`

Metrics:

`backend/ml/artifacts/metrics.json`

Retrain at any time:

```powershell
.\.venv\Scripts\python.exe ml\train_specialty_model.py
```

## AI Copilot

`POST /api/v1/ai/copilot` now demonstrates context-aware responses grounded in MediLink's synthetic appointments, labs, medication and IoT concepts. It returns source labels and an explicit safety note.

It is intentionally not presented as a clinical diagnostic model.

## Emergency support

The emergency workflow uses deliberate confirmation and can open the device dialler using `tel:999`. MediLink does not automatically call emergency services and AI is not used to decide whether to call.

## Run

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --reload-dir app
```

Frontend:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Open `http://localhost:3000`.
