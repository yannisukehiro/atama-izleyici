@echo off
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set USE_EDGE=1
set /p NTFY_TOPIC=<topic.txt
py -3 monitor.py >> log.txt 2>&1
