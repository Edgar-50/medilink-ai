# Google Sign-In — MediLink v0.6

## What changed

- Added the missing Python `requests` dependency required by `google-auth` transport.
- Added a safe Google configuration status endpoint: `GET /api/v1/auth/google/status`.
- Added structured Google auth errors so the UI can react intelligently.
- First-time Google users who start from the login screen now get an inline Patient/Doctor choice instead of a dead-end error.
- Google client secret is not required for the current browser ID-token flow and must never be placed in `NEXT_PUBLIC_*` variables.
- Added `FRONTEND_ORIGIN` for cleaner CORS configuration.
- Added a PowerShell backend dev launcher that watches only `backend/app`, preventing reload storms from `.venv`.
- Added root `.gitignore` rules to prevent accidental commits of `.env`, `.env.local`, databases and model artefacts.

## Frontend `.env.local`

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=YOUR_CLIENT_ID.apps.googleusercontent.com
```

## Backend `.env`

```env
DATABASE_URL=sqlite:///./medilink.db
SECRET_KEY=YOUR_LONG_RANDOM_SECRET
ACCESS_TOKEN_EXPIRE_MINUTES=60
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID.apps.googleusercontent.com
FRONTEND_ORIGIN=http://localhost:3000
```

## Run backend safely during development

From `backend`:

```powershell
.\run-dev.ps1
```

If PowerShell execution policy blocks the script, use:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --reload-dir app
```

## Google Cloud local origin

Add these authorized JavaScript origins to the Web OAuth client:

- `http://localhost`
- `http://localhost:3000`

## Security note

The Google client ID is public configuration. The Google client secret is sensitive. This MediLink implementation does not use the client secret for Google Identity Services ID-token verification.
