@echo off
REM Windows Command Prompt virtual environment activation script

set SCRIPT_DIR=%~dp0
set VENV_DIR=%SCRIPT_DIR%.venv
set ACTIVATE_SCRIPT=%VENV_DIR%\Scripts\activate.bat

if not exist "%VENV_DIR%" (
    echo Error: Virtual environment not found at %VENV_DIR%
    echo Run 'python setup-venv.py' to create it.
    exit /b 1
)

if exist "%ACTIVATE_SCRIPT%" (
    call "%ACTIVATE_SCRIPT%"
    echo Virtual environment activated
) else (
    echo Error: Could not find activation script at %ACTIVATE_SCRIPT%
    exit /b 1
)

