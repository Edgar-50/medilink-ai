# MediLink v0.6 Upgrade

This patch is intended to be copied over the existing MediLink project.

## Fixes

1. Google Auth backend now installs `requests` explicitly.
2. Development reload no longer needs to watch `.venv`.
3. Login-page Google sign-in supports first-time role selection.
4. Structured API errors improve frontend handling.
5. CORS supports localhost and 127.0.0.1 frontend development.
6. Environment files and local databases are protected by `.gitignore`.
7. Frontend includes a `typecheck` script.

## Apply

Copy `backend`, `frontend`, `docs`, and `.gitignore` over the existing project.
Do not delete your existing `backend/.venv`, `backend/medilink.db`, or `frontend/node_modules`.

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
npm.cmd run typecheck
npm.cmd run dev
```
