@echo off
setlocal
cd /d C:\AIWorld
C:\AIWorld\runtime\Python312\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8080 --log-level info >> C:\AIWorld\logs\api.log 2>&1
endlocal
