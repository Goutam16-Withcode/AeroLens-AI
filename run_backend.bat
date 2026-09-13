@echo off
echo ============================================================
echo  Starting SatQuery AI Backend Server (FastAPI + Uvicorn)
echo  Endpoint: http://localhost:8000
echo ============================================================
.\venv\Scripts\python.exe -m uvicorn src.satquery.api.server:app --host 127.0.0.1 --port 8000 --reload
pause
