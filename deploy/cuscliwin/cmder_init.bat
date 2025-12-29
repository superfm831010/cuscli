@echo off
REM =============================================================================
REM Cuscli Cmder Initialization Script
REM Description: Called by Cmder to activate venv and start cuscli
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

REM Fallback to default paths if not set
if not defined CUSCLI_VENV set "CUSCLI_VENV=%SCRIPT_DIR%\venv"
if not defined CUSCLI_WORKDIR set "CUSCLI_WORKDIR=%CD%"

REM Activate virtual environment
if exist "%CUSCLI_VENV%\Scripts\activate.bat" (
    call "%CUSCLI_VENV%\Scripts\activate.bat"
    echo [cuscli] Virtual environment activated
) else (
    echo [ERROR] Virtual environment not found: %CUSCLI_VENV%
    echo [ERROR] Please run install_offline.bat first
    pause
    exit /b 1
)

REM Change to working directory
if exist "%CUSCLI_WORKDIR%" (
    cd /d "%CUSCLI_WORKDIR%"
    echo [cuscli] Working directory: %CUSCLI_WORKDIR%
) else (
    echo [WARN] Working directory not found: %CUSCLI_WORKDIR%
    echo [WARN] Using current directory
)

echo.

REM Start cuscli
cuscli

REM Keep the terminal open after cuscli exits
cmd /k
