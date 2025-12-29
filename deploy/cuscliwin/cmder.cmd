@echo off
REM =============================================================================
REM Cmder Global Command
REM Description: Launch Cmder terminal with cuscli virtual environment activated
REM Usage: Run 'cmder' from any directory after installation
REM =============================================================================

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Call start.bat to launch Cmder with venv activation
call "%SCRIPT_DIR%\start.bat" %*
