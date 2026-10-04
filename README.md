# MediLink AI

MediLink AI is a healthcare coordination platform connecting patients, clinicians, administrators, appointments, health records and AI-assisted services.

> This repository is an engineering/portfolio project. It uses synthetic/demo data and is not a clinically validated medical device.

## Current v1 scope

- Patient / Doctor / Admin roles
- FastAPI backend
- PostgreSQL-ready SQLAlchemy models
- JWT authentication foundation
- User registration/login endpoints
- Appointment model and API foundation
- Health-record model foundation
- AI service boundary for future Clinical Copilot, Patient Copilot and risk models
- Next.js frontend shell
- Docker Compose for API + PostgreSQL

## Architecture

```text
Next.js / React
      |
      v
 FastAPI API
      |
  -----------
  |    |    |
Auth  Care  AI
  |    |    |
  PostgreSQL
```

## Quick start

### 1. Backend locally

```bash
cd backend
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Copy environment file:

```bash
cp .env.example .env
```

Run:

```bash
uvicorn app.main:app --reload
```

API docs:

```text
http://127.0.0.1:8000/docs
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

### 3. PostgreSQL with Docker

From the project root:

```bash
docker compose up --build
```

## Planned AI modules

1. Patient Copilot
2. Clinical Copilot
3. Appointment matching
4. Risk prediction
5. Medical-document extraction
6. Consultation transcription
7. Explainable AI
8. Medical RAG
