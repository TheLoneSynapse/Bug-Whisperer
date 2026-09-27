@echo off
if "%1"=="" (
    .venv\Scripts\mistake-box.exe --file mycode.py
) else (
    .venv\Scripts\mistake-box.exe --file %1
)
