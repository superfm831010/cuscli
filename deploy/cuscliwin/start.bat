@echo off
REM =============================================================================
REM Cuscli Startup Script (Windows)
REM Description: Launch Cmder terminal and activate virtual environment
REM Features: Auto-launches in Cmder terminal for better display on legacy systems
REM Usage: Double-click this script, then cd to your project and run cuscli
REM =============================================================================

setlocal enabledelayedexpansion

REM Script directory (where cuscliwin is installed)
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "VENV_DIR=%SCRIPT_DIR%\venv"
set "CMDER_DIR=%SCRIPT_DIR%\cmder"
set "CMDER_INIT=%SCRIPT_DIR%\cmder_init.bat"

REM Check if virtual environment exists
if not exist "%VENV_DIR%" (
    echo [ERROR] Virtual environment not found: %VENV_DIR%
    echo [ERROR] Please run install_offline.bat first
    pause
    exit /b 1
)

REM Check if activate script exists
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [ERROR] Virtual environment is corrupted
    echo [ERROR] Please re-run install_offline.bat
    pause
    exit /b 1
)

REM ============================================================================
REM Cmder Terminal Detection and Launch
REM ============================================================================

REM Check if already running inside Cmder (CMDER_ROOT is set by Cmder)
if defined CMDER_ROOT (
    REM Already in Cmder, proceed to activate venv
    goto :activate_venv
)

REM Check if Cmder exists and is available
if exist "%CMDER_DIR%\Cmder.exe" (
    REM Launch Cmder with cuscli initialization
    echo [INFO] Launching Cmder terminal...

    REM Write config to temp file for cmder_init.bat to read
    set "CONFIG_FILE=%SCRIPT_DIR%\cmder_config.tmp"
    echo CUSCLI_VENV=%VENV_DIR%> "%CONFIG_FILE%"

    REM Start Cmder with init script using ConEmu's -run parameter
    start "" "%CMDER_DIR%\Cmder.exe" /SINGLE /START "%SCRIPT_DIR%" -run "\"%CMDER_INIT%\""

    REM Exit current cmd window
    exit /b 0
)

REM ============================================================================
REM Fallback: Normal terminal mode (when Cmder is not available)
REM ============================================================================

:activate_venv

REM Set console to UTF-8
chcp 65001 >nul 2>&1

REM Activate virtual environment
call "%VENV_DIR%\Scripts\activate.bat"

REM Show welcome message and usage instructions
echo.
echo ============================================
echo   Cuscli AI Programming Assistant
echo ============================================
echo.
echo   Virtual environment activated!
echo.
echo   Usage:
echo     1. cd to your project directory
echo     2. Run: cuscli
echo.
echo   Example:
echo     cd C:\projects\myapp
echo     cuscli
echo.
echo ============================================
echo.

REM Keep the terminal open with activated venv
cmd /k

endlocal
