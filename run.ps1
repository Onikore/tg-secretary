# Start the secretary bot. Creates the venv and installs deps on first run.
$ErrorActionPreference = "Stop"

if (-not (Test-Path .venv)) {
    python -m venv .venv
    .venv\Scripts\python.exe -m pip install --upgrade pip
    .venv\Scripts\python.exe -m pip install -r requirements.txt
}

if (-not (Test-Path .env)) {
    Write-Host "Missing .env. Copy .env.example to .env and fill in BOT_TOKEN, GEMINI_API_KEY, OWNER_USER_ID."
    exit 1
}

.venv\Scripts\python.exe main.py
