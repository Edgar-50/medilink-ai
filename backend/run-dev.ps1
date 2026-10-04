$ErrorActionPreference = "Stop"
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
  Write-Error "Virtual environment not found. Create it with: py -3.12 -m venv .venv"
}
& $python -m uvicorn app.main:app --reload --reload-dir app
