@echo off
title Sentinel EDR Setup
color 0B

echo.
echo  ============================================================
echo   SENTINEL EDR - Automated Setup
echo   Monitor. Prevent. Analyze.
echo  ============================================================
echo.
echo  This will install Sentinel EDR on your computer.
echo  Please do not close this window.
echo.
pause

:: ── Step 1: Check Python ─────────────────────────────────────────
echo.
echo  [1/5] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  Python not found. Downloading Python 3.13.1...
    curl -o "%TEMP%\python_installer.exe" "https://www.python.org/ftp/python/3.13.1/python-3.13.1-amd64.exe"
    echo  Installing Python...
    "%TEMP%\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    del "%TEMP%\python_installer.exe"
    echo  Python installed. Restarting setup to apply PATH...
    :: Refresh PATH so python is available
    call refreshenv >nul 2>&1
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo  [!] Python installed but PATH not updated yet.
        echo  Please close this window and double-click sentinel_setup.bat again.
        echo.
        pause
        exit
    )
) else (
    for /f "tokens=*" %%i in ('python --version') do echo  Found: %%i
)

:: ── Step 2: Set install location ─────────────────────────────────
echo.
echo  [2/5] Setting up Sentinel folder...
set INSTALL_DIR=%~dp0
echo  Using current folder: %INSTALL_DIR%

:: ── Step 3: Create or update venv ────────────────────────────────
echo.
echo  [3/5] Setting up virtual environment...
if exist "%INSTALL_DIR%venv\Scripts\python.exe" (
    echo  Virtual environment already exists — skipping creation.
) else (
    echo  Creating virtual environment...
    python -m venv "%INSTALL_DIR%venv"
    if %errorlevel% neq 0 (
        echo  [!] Failed to create venv. Trying with py launcher...
        py -3 -m venv "%INSTALL_DIR%venv"
    )
    echo  Virtual environment created.
)

:: ── Step 4: Install requirements ─────────────────────────────────
echo.
echo  [4/5] Installing required libraries...
"%INSTALL_DIR%venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
"%INSTALL_DIR%venv\Scripts\pip.exe" install -r "%INSTALL_DIR%requirements.txt" --quiet
if %errorlevel% neq 0 (
    echo  [!] Some libraries failed. Trying again...
    "%INSTALL_DIR%venv\Scripts\pip.exe" install -r "%INSTALL_DIR%requirements.txt"
)
echo  Libraries installed.

:: ── Step 5: Create run script ─────────────────────────────────────
echo.
echo  [5/5] Creating launch shortcut...
(
echo @echo off
echo title Sentinel EDR
echo color 0B
echo cd /d "%INSTALL_DIR%"
echo call venv\Scripts\activate
echo echo.
echo echo  Starting Sentinel EDR...
echo echo  Press Ctrl+C to stop.
echo echo.
echo python edr_main.py
echo pause
) > "%INSTALL_DIR%Run_Sentinel.bat"

:: Copy shortcut to Desktop
copy "%INSTALL_DIR%Run_Sentinel.bat" "%USERPROFILE%\Desktop\Run_Sentinel.bat" >nul 2>&1

:: ── Done ──────────────────────────────────────────────────────────
echo.
echo  ============================================================
echo   SENTINEL EDR INSTALLED SUCCESSFULLY!
echo  ============================================================
echo.
echo   Location : %INSTALL_DIR%
echo   Shortcut : Run_Sentinel.bat on your Desktop
echo.
echo   BEFORE RUNNING, open config.py and set:
echo     SECURITY_CODE  = your secret code
echo     ARDUINO_PORT   = your COM port (e.g. COM3)
echo     REPORT_URL     = https://sentinel-mesh.onrender.com
echo.
echo  ============================================================
echo.
pause
