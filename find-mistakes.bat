@echo off
chcp 65001 >nul
.venv\Scripts\python.exe find_mistakes.py %~f1
