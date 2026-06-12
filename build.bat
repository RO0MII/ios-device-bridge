@echo off
title iOS Device Bridge — Build .exe
echo ============================================
echo  iOS Device Bridge — Build .exe
echo  Windows 11 One-Click Builder
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo   Download from: https://python.org/downloads
    pause
    exit /b 1
)
echo [OK] Python found

REM Install dependencies
echo [INFO] Installing Python packages...
pip install --upgrade pip >nul 2>&1
pip install PyQt6 pymobiledevice3 pyinstaller
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed

REM Build
echo [BUILD] Building iOS Device Bridge...
echo.
python build.py
if %errorlevel% neq 0 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

echo.
echo ============================================
echo  BUILD COMPLETE
echo ============================================
echo.
echo  Executable:     dist\iOSDeviceBridge.exe
echo  Tools:          dist\tools\ (irecovery, idevicerestore, etc.)
echo.
echo  Total portable bundle: dist\
echo.
echo  To create Inno Setup installer:
echo    python build.py --installer
echo.
echo  REQUIREMENTS TO RUN:
echo  1. Apple Mobile Device USB Driver (comes with iTunes)
echo  2. iPhone connected via USB
echo  3. For restore: device in Recovery or DFU mode
echo.
pause
