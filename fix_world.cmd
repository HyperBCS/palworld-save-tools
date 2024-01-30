@echo off
setlocal enabledelayedexpansion

:: Switch to script directory
cd /D "%~dp0"

:: Check if fix_save.py exists
if not exist "fix_save.py" (
    echo fix_save.py is missing.
    pause
    exit /B 1
)

:: Try every possible Python command until one works
for %%A in (python python3 py) do (
    echo Checking if Python is installed as %%A
    where %%A
    if !ERRORLEVEL! equ 0 (
        echo Found Python at %%A
        echo Python version:
        %%A --version
        %%A fix_save.py "%~1"
        goto :Found
    )
)

echo Python not found. Please install Python 3.9 or newer.
pause
exit /B 1

:Found
pause
