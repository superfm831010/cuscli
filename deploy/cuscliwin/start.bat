@echo off
REM =============================================================================
REM Cuscli Startup Script (Windows)
REM Description: Activate virtual environment and start cuscli
REM Usage: Run this script from your project directory
REM =============================================================================

setlocal

REM Script directory (where cuscliwin is installed)
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "VENV_DIR=%SCRIPT_DIR%\venv"

REM Current working directory (user's project directory)
set "WORK_DIR=%CD%"

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

REM Set console to UTF-8
chcp 65001 >nul 2>&1

REM Activate virtual environment
call "%VENV_DIR%\Scripts\activate.bat"

REM Print startup info
echo ============================================
echo   Cuscli AI Programming Assistant
echo ============================================
echo.
echo Virtual environment: %VENV_DIR%
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo Python: %%v
echo.
echo Working directory: %WORK_DIR%
echo.

REM Check if we're in a valid project directory
if "%WORK_DIR%"=="%SCRIPT_DIR%" (
    echo [WARN] You are running from the cuscliwin directory.
    echo [WARN] Please run this script from your project directory.
    echo.
    echo Usage:
    echo   1. Open Command Prompt
    echo   2. cd to your project directory
    echo   3. Run: "%SCRIPT_DIR%\start.bat"
    echo.
    echo Or drag your project folder onto this script.
    echo.
    set /p "PROJECT_DIR=Enter project directory path (or press Enter to continue anyway): "
    if defined PROJECT_DIR (
        if exist "!PROJECT_DIR!" (
            cd /d "!PROJECT_DIR!"
            set "WORK_DIR=!PROJECT_DIR!"
            echo.
            echo Changed to: !PROJECT_DIR!
            echo.
        ) else (
            echo [ERROR] Directory not found: !PROJECT_DIR!
            pause
            exit /b 1
        )
    )
)

REM Start cuscli with all passed arguments
if "%~1"=="" (
    REM No arguments - start interactive chat mode
    cuscli
) else (
    REM Pass all arguments to cuscli
    cuscli %*
)

endlocal
