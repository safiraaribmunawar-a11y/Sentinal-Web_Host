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

:: ── Check if Python is installed ────────────────────────────────
echo.
echo  [1/5] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  Python not found. Downloading Python 3.13...
    echo  Please wait...
    curl -o "%TEMP%\python_installer.exe" "https://www.python.org/ftp/python/3.13.1/python-3.13.1-amd64.exe"
    echo  Installing Python...
    "%TEMP%\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    echo  Python installed successfully.
) else (
    echo  Python found.
)

:: ── Create Sentinel folder ───────────────────────────────────────
echo.
echo  [2/5] Creating Sentinel folder...
set INSTALL_DIR=%USERPROFILE%\Desktop\Sentinel
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
cd /d "%INSTALL_DIR%"
echo  Folder created at %INSTALL_DIR%

:: ── Download Sentinel files ──────────────────────────────────────
echo.
echo  [3/5] Downloading Sentinel files...
echo  Downloading from sentinel-mesh.onrender.com...

curl -o "%INSTALL_DIR%\edr_main.py"     "https://sentinel-mesh.onrender.com/download/edr_main.py"
curl -o "%INSTALL_DIR%\monitor.py"      "https://sentinel-mesh.onrender.com/download/monitor.py"
curl -o "%INSTALL_DIR%\detector.py"     "https://sentinel-mesh.onrender.com/download/detector.py"
curl -o "%INSTALL_DIR%\arduino_comm.py" "https://sentinel-mesh.onrender.com/download/arduino_comm.py"
curl -o "%INSTALL_DIR%\reporter.py"     "https://sentinel-mesh.onrender.com/download/reporter.py"
curl -o "%INSTALL_DIR%\config.py"       "https://sentinel-mesh.onrender.com/download/config.py"
curl -o "%INSTALL_DIR%\requirements.txt" "https://sentinel-mesh.onrender.com/download/requirements.txt"

echo  Files downloaded.

:: ── Create virtual environment ───────────────────────────────────
echo.
echo  [4/5] Creating virtual environment...
python -m venv "%INSTALL_DIR%\venv"
echo  Virtual environment created.

:: ── Install requirements ─────────────────────────────────────────
echo.
echo  [5/5] Installing required libraries...
"%INSTALL_DIR%\venv\Scripts\pip.exe" install -r "%INSTALL_DIR%\requirements.txt" --quiet
echo  Libraries installed.

:: ── Create run script ────────────────────────────────────────────
echo.
echo  Creating launch script...
(
echo @echo off
echo title Sentinel EDR
echo color 0B
echo cd /d "%INSTALL_DIR%"
echo call venv\Scripts\activate
echo python edr_main.py
echo pause
) > "%INSTALL_DIR%\Run_Sentinel.bat"

:: ── Create desktop shortcut ──────────────────────────────────────
copy "%INSTALL_DIR%\Run_Sentinel.bat" "%USERPROFILE%\Desktop\Run_Sentinel.bat" >nul

:: ── Done ─────────────────────────────────────────────────────────
echo.
echo  ============================================================
echo   SENTINEL EDR INSTALLED SUCCESSFULLY!
echo  ============================================================
echo.
echo   Location: %INSTALL_DIR%
echo.
echo   To run Sentinel:
echo   Double-click "Run_Sentinel.bat" on your Desktop
echo.
echo   Before running, open config.py and set:
echo   - SECURITY_CODE  (your secret code)
echo   - ARDUINO_PORT   (e.g. COM3)
echo.
echo  ============================================================
echo.
pause
