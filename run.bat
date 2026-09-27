@echo off
chcp 65001 >nul
if "%1"=="" (
    .venv\Scripts\python.exe smart_run.py mycode.py
) else (
    .venv\Scripts\python.exe smart_run.py %1
)
