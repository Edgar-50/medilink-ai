# MediLink v11 — Clinical Intelligence & Operations

Version 1.1.0 focuses on completing the clinician-to-operations workflow rather than adding disconnected showcase screens.

## Added

- Unified clinician **Care Actions** workspace.
- Electronic prescription creation backed by the medication database.
- Medication-interaction review rules with severity and explanation.
- Laboratory request composer.
- Specialist referral composer.
- Care-coordination risk scoring with explainable contributing factors.
- Persisted clinical letters with sign workflow.
- Server-generated clinical-letter PDF export.
- Advanced patient context endpoint combining medicines, labs, referrals and documents.
- Real-time notification unread-count WebSocket.
- Administrator audit-history interface.
- Hospital command-centre patient-flow visualisation.
- Stronger clinician navigation and app launcher.
- Additional light-theme contrast fixes.

## Install

From the backend folder:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --reload-dir app
```

Then restart the frontend:

```powershell
npm.cmd install
npm.cmd run dev
```

The API should report version `1.1.0`.

## New clinician route

`/clinical-actions`

The selected patient remains in context while the clinician moves between prescription, laboratory, referral, risk and correspondence workflows.

## New administrator route

`/audit`

Administrators can review persisted sensitive-action history generated across the platform.

## Clinical PDF export

Signed letters are exported by the backend with ReportLab. The public repository does not include real patient data.

## Risk and medication checks

The v11 risk score is an explainable care-coordination aid and the interaction checker is a small rules engine. Neither is a validated medical-device decision system. They are intentionally presented as clinician-support features rather than autonomous prescribing or diagnostic systems.
