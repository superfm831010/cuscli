@echo off
:: =============================================================================
:: Cuscli Auto-initialization for Cmder
:: Description: Automatically activates cuscli virtual environment when Cmder starts
:: This file is executed by Cmder's init.bat on startup
:: =============================================================================

setlocal enabledelayedexpansion

:: Get cuscliwin directory (parent of cmder directory)
:: config is inside cmder, so we need to go up two levels
set "CONFIG_DIR=%~dp0"
set "CONFIG_DIR=%CONFIG_DIR:~0,-1%"
for %%I in ("%CONFIG_DIR%\..") do set "CMDER_DIR=%%~fI"
for %%I in ("%CMDER_DIR%\..") do set "CUSCLI_DIR=%%~fI"

:: Check for config file (written by start.bat)
set "CONFIG_FILE=%CUSCLI_DIR%\cmder_config.tmp"
if exist "%CONFIG_FILE%" (
    for /f "usebackq tokens=1,* delims==" %%a in ("%CONFIG_FILE%") do (
        set "%%a=%%b"
    )
    del "%CONFIG_FILE%" >nul 2>&1
)

:: Default venv path
if not defined CUSCLI_VENV set "CUSCLI_VENV=%CUSCLI_DIR%\venv"

:: Activate virtual environment
if exist "%CUSCLI_VENV%\Scripts\activate.bat" (
    endlocal
    call "%CUSCLI_VENV%\Scripts\activate.bat"

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
) else (
    echo [WARN] Virtual environment not found: %CUSCLI_VENV%
    echo [WARN] Please run install_offline.bat first
    endlocal
)
