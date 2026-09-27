@echo off
chcp 65001 >nul
rem voice.bat - push-to-talk voice mode for mistake-finder.
rem
rem   .\voice.bat                              interactive mic loop
rem   .\voice.bat --text "find demo math"      no mic, type a command
rem   .\voice.bat --file tests\pandas.test.py  analyse one file now
rem   .\voice.bat --pin tests\pandas.test.py   pin the file you have open
rem   .\voice.bat --list-mics                  show available microphones
rem   .\voice.bat --no-speak                   print box, stay silent
rem   .\voice.bat --once                       one turn then exit
rem
rem   At the > prompt, type  help  to see all commands.
.venv\Scripts\python.exe voice_agent.py %*
