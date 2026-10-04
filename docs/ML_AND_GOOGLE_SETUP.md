# MediLink v5 — ML Confidence and Google Sign-In

## 1. What changed in AI routing

MediLink no longer invents probability-like percentages from keyword scores.

- If no trained artifact exists, the API uses `rule_routing` and returns **strong / moderate / weak** routing signals.
- If a calibrated classifier artifact exists, the API returns `calibrated_demo_model` and exposes model probabilities.
- Doctor suitability remains a transparent **match score out of 100**, not a probability.

The included dataset is synthetic and exists only to demonstrate the ML pipeline. Its reported accuracy and calibrated confidence are **not clinical validation**.

## 2. Train the demo calibrated model

From `backend` with the venv active/directly addressed:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe ml\train_specialty_model.py
```

The patch intentionally does not ship a pre-trained model artifact. Training the demo pipeline creates:

```text
backend/ml/artifacts/specialty_router.joblib
```

Restart FastAPI after training. The AI matching page will automatically switch from rule-routing labels to calibrated demo confidence.

For a serious validation study, replace `specialty_training.csv` with a sufficiently large, clinically reviewed, de-identified/lawfully usable labelled dataset and keep a fully held-out test set. Add external validation and safety analysis before making clinical claims.

## 3. Google sign-in

Create a Google OAuth 2.0 **Web application** client in Google Cloud Console.

Add your local origin:

```text
http://localhost:3000
```

Copy the client ID into both environment files.

Backend `.env`:

```text
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID.apps.googleusercontent.com
```

Frontend `.env.local`:

```text
NEXT_PUBLIC_GOOGLE_CLIENT_ID=YOUR_CLIENT_ID.apps.googleusercontent.com
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Restart both backend and frontend after changing environment variables.

The browser obtains a Google ID credential and the FastAPI backend verifies that credential against the configured Google client ID before creating or signing in the MediLink user. New Google users must choose Patient or Doctor during registration; Google login will then reuse the existing role.
