@echo off
REM =============================================================================
REM Cuscli Global Wrapper (Windows)
REM This script allows running cuscli from any directory
REM =============================================================================

setlocal

REM Get the directory where this script is located
set "CUSCLI_HOME=%~dp0"
set "CUSCLI_HOME=%CUSCLI_HOME:~0,-1%"
set "VENV_DIR=%CUSCLI_HOME%\venv"

REM Check if virtual environment exists
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [ERROR] Cuscli is not installed properly.
    echo [ERROR] Please run install_offline.bat first.
    exit /b 1
)

REM Set console to UTF-8
chcp 65001 >nul 2>&1

REM Run cuscli using the venv's python directly (no need to activate)
"%VENV_DIR%\Scripts\python.exe" -m autocoder.chat_auto_coder %*

endlocal
