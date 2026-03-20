# PowerShell script to run backend on Windows
if (-Not (Test-Path -Path "venv")) {
    python -m venv venv
}
# Activate virtual environment
& .\venv\Scripts\Activate.ps1
# Install dependencies
pip install -r requirements.txt
# Run FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000