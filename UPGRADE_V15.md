# Upgrade to MediLink v15

1. Copy this patch over the existing v11.1 project. Preserve `.env`, `.venv`, `medilink.db`, `.env.local` and `node_modules`.
2. Backend: `python -m pip install -r requirements.txt`.
3. Start API: `.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --reload-dir app`.
4. Frontend: `npm.cmd install` then `npm.cmd run dev`.
5. New admin routes: `/platform`, `/intelligence`, `/network`.
6. New connected-care route: `/connected-care`.
7. API version is `1.5.0`.

For the optional platform stack use `docker compose -f docker-compose.platform.yml up -d`. SQLite/local fallbacks remain supported.
