@echo off
REM =============================================================================
REM Cuscli Cmder Initialization Script
REM Description: Called by Cmder to activate venv and show usage instructions
REM This script is invoked automatically when start.bat launches Cmder
REM =============================================================================

setlocal enabledelayedexpansion

REM Script directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "CONFIG_FILE=%SCRIPT_DIR%\cmder_config.tmp"

REM Set console to UTF-8
chcp 65001 >nul 2>&1

REM Read configuration from temp file if exists
if exist "%CONFIG_FILE%" (
    for /f "usebackq tokens=1,* delims==" %%a in ("%CONFIG_FILE%") do (
        set "%%a=%%b"
    )
    REM Clean up temp file
    del "%CONFIG_FILE%" >nul 2>&1
)

REM Fallback to default venv path if not set
if not defined CUSCLI_VENV set "CUSCLI_VENV=%SCRIPT_DIR%\venv"

REM Activate virtual environment
if exist "%CUSCLI_VENV%\Scripts\activate.bat" (
    call "%CUSCLI_VENV%\Scripts\activate.bat"
) else (
    echo [ERROR] Virtual environment not found: %CUSCLI_VENV%
    echo [ERROR] Please run install_offline.bat first
    pause
    exit /b 1
)

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
