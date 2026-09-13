# SatQuery AI - FastAPI Backend Launcher
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Starting SatQuery AI Backend Server (FastAPI + Uvicorn)" -ForegroundColor Cyan
Write-Host " Endpoint: http://localhost:8000" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan

& ".\venv\Scripts\python.exe" -m uvicorn src.satquery.api.server:app --host 127.0.0.1 --port 8000 --reload
