@echo off
setlocal EnableExtensions EnableDelayedExpansion
title SPECTRA-X Environment Setup - NASA Space Apps Demo

echo ======================================================================
echo    SPECTRA-X DEMO ENVIRONMENT SETUP AND BOOTSTRAP WIZARD
echo    NASA Space Apps Challenge 2026 - F1 V2.1 Pipeline (l2b-v27-2026-222)
echo ======================================================================
echo.

:: 1. Resolve project root directory relative to this script
for %%I in ("%~dp0..") do set "PROJECT_ROOT=%%~fI"
set "VENV_DIR=%PROJECT_ROOT%\.venv_demo"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "REQ_FILE=%PROJECT_ROOT%\NASA_DEMO\requirements-demo.txt"
set "VERIFY_SCRIPT=%PROJECT_ROOT%\NASA_DEMO\verify_environment.py"

echo [SETUP] Project root:        %PROJECT_ROOT%
echo [SETUP] Target environment:  %VENV_DIR%
echo [SETUP] Requirements file:   %REQ_FILE%
echo.

:: 2. Detect Host Python (prefer Python 3.12.x)
echo [DETECT] Probing for installed Python 3.12 on this system...
set "BOOTSTRAP_PYTHON="

:: Check 1: py -3.12 launcher
py -3.12 -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%p in ('py -3.12 -c "import sys; print(sys.executable)"') do set "BOOTSTRAP_PYTHON=%%p"
    goto :python_found
)

:: Check 2: python in PATH (is it 3.12?)
python -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%p in ('python -c "import sys; print(sys.executable)"') do set "BOOTSTRAP_PYTHON=%%p"
    goto :python_found
)

:: Check 3: Standard LocalAppData installation
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "BOOTSTRAP_PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto :python_found
)

:: Check 4: Standard Program Files installation
if exist "%ProgramFiles%\Python312\python.exe" (
    set "BOOTSTRAP_PYTHON=%ProgramFiles%\Python312\python.exe"
    goto :python_found
)

:: Check 5: Generic python in PATH (compatible 3.10 - 3.11 fallback)
python -c "import sys; sys.exit(0 if sys.version_info[0] == 3 and sys.version_info[1] >= 10 else 1)" >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%p in ('python -c "import sys; print(sys.executable)"') do set "BOOTSTRAP_PYTHON=%%p"
    echo [WARNING] Python 3.12 not found, but compatible Python detected: !BOOTSTRAP_PYTHON!
    goto :python_found
)

:: If no compatible Python found:
echo.
echo ======================================================================
echo  [ERROR] COMPATIBLE PYTHON 3.12 RUNTIME NOT FOUND!
echo ======================================================================
echo  The SPECTRA-X demo requires 64-bit Python 3.12 (preferred) or 3.10+.
echo.
echo  Installation Instructions:
echo  1. Download the official Windows 64-bit installer:
echo     https://www.python.org/downloads/release/python-31210/
echo.
echo  2. OR install via Windows Terminal / PowerShell:
echo     winget install Python.Python.3.12
echo.
echo  CRITICAL: Check the box "Add python.exe to PATH" during installation.
echo ======================================================================
echo.
pause
exit /b 1

:python_found
echo [DETECT] Compatible Python found at: %BOOTSTRAP_PYTHON%
"%BOOTSTRAP_PYTHON%" -c "import sys; print(f'         Version: {sys.version.split()[0]} ({sys.maxsize > 2**32 and \"64-bit\" or \"32-bit\"})')"

:: 3. Create .venv_demo if missing
if exist "%VENV_PYTHON%" (
    echo [ENV] Virtual environment .venv_demo already exists.
) else (
    echo.
    echo [ENV] Creating clean virtual environment at:
    echo       "%VENV_DIR%"
    "%BOOTSTRAP_PYTHON%" -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [ENV] Virtual environment successfully created.
)

:: 4. Upgrade packaging tools
echo.
echo [PIP] Upgrading pip, setuptools, and wheel...
"%VENV_PYTHON%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo [WARNING] Pip upgrade encountered a warning, continuing with dependency installation...
)

:: 5. Install demo dependencies
echo.
echo [PIP] Installing required SPECTRA-X runtime dependencies...
echo       Reading manifest: %REQ_FILE%
"%VENV_PYTHON%" -m pip install -r "%REQ_FILE%"
if errorlevel 1 (
    echo.
    echo ======================================================================
    echo  [ERROR] Dependency installation failed!
    echo  Please ensure an active internet connection is available for initial
    echo  package downloads.
    echo ======================================================================
    pause
    exit /b 1
)

:: 6. Run Comprehensive Environment & Model Verification
echo.
echo [VERIFY] Running scientific runtime verification suite...
"%VENV_PYTHON%" "%VERIFY_SCRIPT%"
if errorlevel 1 (
    echo.
    echo [ERROR] Environment verification failed!
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo   SETUP COMPLETED SUCCESSFULLY!
echo   Isolated environment .venv_demo is ready for demo launch.
echo   You can now launch the demo anytime via: NASA_DEMO\START_DEMO.bat
echo ======================================================================
echo.
exit /b 0
