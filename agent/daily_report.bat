@echo off
rem A job for Windows Task Scheduler (Lesson 6, Part 4): only claude -p, no Python program, no SDK.
rem It activates the venv itself, because a scheduled task has no prepared cmd window (Lesson 0).
call C:\pyenvsmy\claudeclioct26\Scripts\activate.bat
cd /d "%~dp0.."
if not exist reports mkdir reports
claude -p "Which region has the highest total amount in data/sales.xlsx? Answer in one sentence." --model haiku --allowedTools "Skill,Read,Bash(python *),PowerShell(python *)" --no-session-persistence > reports\daily_report.txt
type reports\daily_report.txt
