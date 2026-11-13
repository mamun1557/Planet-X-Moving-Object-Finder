@echo off
setlocal EnableExtensions EnableDelayedExpansion
title SPECTRA-X Interactive Observatory - NASA Space Apps Demo Launcher

echo ======================================================================
echo    SPECTRA-X INTERACTIVE OBSERVATORY - ONE-CLICK NASA DEMO LAUNCHER
echo    NASA Space Apps Challenge 2026 - F1 V2.1 Pipeline (l2b-v27-2026-222)
echo ======================================================================
echo.

:: 1. Resolve project root directory relative to this script
for %%I in ("%~dp0..") do set "PROJECT_ROOT=%%~fI"
set "VENV_DIR=%PROJECT_ROOT%\.venv_demo"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "SETUP_BAT=%PROJECT_ROOT%\NASA_DEMO\SETUP_ENVIRONMENT.bat"
set "APP_PY=%PROJECT_ROOT%\observatory\app.py"
set "DIST_INDEX=%PROJECT_ROOT%\frontend\dist\index.html"
set "DEMO_URL=http://127.0.0.1:8050/"
set "STATUS_URL=http://127.0.0.1:8050/api/status"

echo [PREFLIGHT] Project root:     %PROJECT_ROOT%
echo [PREFLIGHT] Demo environment: %VENV_DIR%
echo [PREFLIGHT] App entry point:  %APP_PY%

:: 2. Check if .venv_demo exists; if missing, invoke automatic setup wizard
if not exist "%PYTHON_EXE%" (
    echo.
    echo [INFO] Demonstration virtual environment was not detected at:
    echo        "%VENV_DIR%"
    echo [INFO] Automatically launching SETUP_ENVIRONMENT.bat to initialize environment...
    echo.
    call "%SETUP_BAT%"
    if errorlevel 1 (
        echo.
        echo [ERROR] Automated environment setup failed!
        echo Please resolve the error above and rerun START_DEMO.bat.
        echo.
        pause
        exit /b 1
    )
)

:: Re-verify Python runtime
if not exist "%PYTHON_EXE%" (
    echo.
    echo [ERROR] Python runtime is still missing after setup attempt:
    echo         "%PYTHON_EXE%"
    echo.
    pause
    exit /b 1
)

:: 3. Verify Observatory backend application exists
if not exist "%APP_PY%" (
    echo.
    echo [ERROR] Observatory entry point not found at:
    echo         "%APP_PY%"
    echo.
    pause
    exit /b 1
)

:: 4. Verify pre-compiled production frontend bundle exists
if not exist "%DIST_INDEX%" (
    echo.
    echo ======================================================================
    echo  [ERROR] PRE-COMPILED FRONTEND BUNDLE NOT FOUND!
    echo ======================================================================
    echo  Missing expected file: "%DIST_INDEX%"
    echo.
    echo  The SPECTRA-X Observatory user interface must be pre-built on a
    echo  development machine using 'npm --prefix frontend run build' prior to
    echo  distributing this demo folder.
    echo.
    echo  Target PCs do NOT require Node.js or npm, but the 'frontend/dist/'
    echo  folder must be present in the distributed package.
    echo ======================================================================
    echo.
    pause
    exit /b 1
)

:: 5. Port collision detection: check if port 8050 is already listening
netstat -ano | findstr /R /C:":8050 .*LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo.
    echo [INFO] SPECTRA-X Observatory backend is already active on port 8050.
    echo [INFO] Reusing active server instance and opening web browser directly...
    start "" "%DEMO_URL%"
    goto :finished
)

:: 6. Start Observatory backend in a dedicated console window
echo.
echo [LAUNCH] Starting SPECTRA-X Observatory backend server...
start "SPECTRA-X Observatory Backend (Port 8050)" /D "%PROJECT_ROOT%" "%PYTHON_EXE%" "%APP_PY%" --no-browser

:: 7. Polling HTTP readiness probe (max 15 seconds)
echo [WAIT] Waiting for backend readiness at %STATUS_URL%...
set RETRY_COUNT=0

:wait_loop
set /a RETRY_COUNT+=1
if %RETRY_COUNT% gtr 30 goto :wait_timeout

:: Probe status endpoint via python urllib
"%PYTHON_EXE%" -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8050/api/status', timeout=1).getcode() == 200 else 1)" >nul 2>&1
if not errorlevel 1 goto :wait_success

:: Sleep 500ms using python
"%PYTHON_EXE%" -c "import time; time.sleep(0.5)" >nul 2>&1
goto :wait_loop

:wait_timeout
echo [WARNING] Backend did not respond within timeout. Attempting browser launch...
goto :open_browser

:wait_success
echo [READY] Observatory backend is operational (HTTP 200 OK).

:open_browser
:: 8. Launch default web browser
echo [LAUNCH] Opening default web browser to: %DEMO_URL%
start "" "%DEMO_URL%"

:finished
echo.
echo ======================================================================
echo   DEMO LAUNCH COMPLETE!
echo   Interface URL: %DEMO_URL%
echo   Sample Inputs: %PROJECT_ROOT%\NASA_DEMO\sample_inputs
echo.
echo   * The backend server is running in a separate console window.
echo   * To shut down the demo: close that server console window.
echo ======================================================================
echo.
