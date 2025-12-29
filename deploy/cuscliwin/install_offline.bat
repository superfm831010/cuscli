@echo off
REM =============================================================================
REM Cuscli Offline Deployment - Install Script (Windows)
REM Description: Install cuscli in offline/intranet environment
REM Creates virtual environment and installs all dependencies from local packages
REM =============================================================================

setlocal enabledelayedexpansion

REM Script directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Configuration
set "VENV_DIR=%SCRIPT_DIR%\venv"
set "PACKAGES_DIR=%SCRIPT_DIR%\packages"
set "WHEELS_DIR=%SCRIPT_DIR%\wheels"
set "PYTHON_CMD=python"
set "AUTO_CONFIRM=0"

REM Parse arguments
:parse_args
if "%~1"=="" goto :main
if /i "%~1"=="-p" (
    set "PYTHON_CMD=%~2"
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--python" (
    set "PYTHON_CMD=%~2"
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="-y" (
    set "AUTO_CONFIRM=1"
    shift
    goto :parse_args
)
if /i "%~1"=="--yes" (
    set "AUTO_CONFIRM=1"
    shift
    goto :parse_args
)
if /i "%~1"=="-h" goto :usage
if /i "%~1"=="--help" goto :usage
echo [ERROR] Unknown option: %~1
goto :usage

:main
call :print_header
call :check_system
if errorlevel 1 goto :error

call :create_venv
if errorlevel 1 goto :error

call :upgrade_pip
if errorlevel 1 goto :error

call :install_dependencies
if errorlevel 1 goto :error

call :install_cuscli
if errorlevel 1 goto :error

call :extract_cmder
call :register_cmder

call :verify_installation
call :add_to_path
call :show_completion

echo.
echo [SUCCESS] Installation completed successfully!
goto :end

:print_header
echo ============================================
echo   Cuscli Offline Installation (Windows)
echo ============================================
echo.
goto :eof

:check_system
echo [INFO] Checking system requirements...

REM Check Python - try multiple commands and verify they actually work
set "PYTHON_CMD="
set "PY_VER="

REM Try py launcher first (most reliable on Windows)
py --version >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=2" %%i in ('py --version 2^>^&1') do set "PY_VER=%%i"
    if defined PY_VER set "PYTHON_CMD=py"
)

REM Try python3 if py didn't work
if not defined PYTHON_CMD (
    python3 --version >nul 2>&1
    if not errorlevel 1 (
        for /f "tokens=2" %%i in ('python3 --version 2^>^&1') do set "PY_VER=%%i"
        if defined PY_VER set "PYTHON_CMD=python3"
    )
)

REM Try python if python3 didn't work (but verify it's not the Windows Store stub)
if not defined PYTHON_CMD (
    python -c "import sys" >nul 2>&1
    if not errorlevel 1 (
        for /f "tokens=2" %%i in ('python --version 2^>^&1') do set "PY_VER=%%i"
        if defined PY_VER set "PYTHON_CMD=python"
    )
)

if not defined PYTHON_CMD (
    echo [ERROR] Python is not installed or not in PATH
    echo.
    if exist "%SCRIPT_DIR%\python\python-3.10.11-amd64.exe" (
        echo [INFO] Python installer found in: %SCRIPT_DIR%\python\
        echo.
        echo Please install Python first:
        echo   1. Run: %SCRIPT_DIR%\python\python-3.10.11-amd64.exe
        echo   2. IMPORTANT: Check "Add Python to PATH" at the bottom!
        echo   3. Close this window and reopen Command Prompt
        echo   4. Run this script again
    ) else (
        echo Please install Python 3.10 or later:
        echo   1. Download from https://www.python.org/downloads/
        echo   2. IMPORTANT: Check "Add Python to PATH" at the bottom!
        echo   3. Close this window and reopen Command Prompt
        echo   4. Run this script again
    )
    exit /b 1
)

echo [INFO] Python version: %PY_VER% (using %PYTHON_CMD%)

for /f "tokens=*" %%i in ('%PYTHON_CMD% -c "import sys; print(sys.version_info.major)"') do set "PY_MAJOR=%%i"
for /f "tokens=*" %%i in ('%PYTHON_CMD% -c "import sys; print(sys.version_info.minor)"') do set "PY_MINOR=%%i"

if "%PY_MAJOR%"=="" set "PY_MAJOR=0"
if "%PY_MINOR%"=="" set "PY_MINOR=0"

if %PY_MAJOR% LSS 3 (
    echo [ERROR] Python version too old: %PY_VER%
    echo [ERROR] Requires Python 3.10 or later
    exit /b 1
)
if %PY_MAJOR% EQU 3 if %PY_MINOR% LSS 10 (
    echo [ERROR] Python version too old: %PY_VER%
    echo [ERROR] Requires Python 3.10 or later
    exit /b 1
)

REM Check packages directory
if not exist "%PACKAGES_DIR%" (
    echo [ERROR] Packages directory not found: %PACKAGES_DIR%
    echo [ERROR] Please run download_deps.bat first on a machine with internet access
    exit /b 1
)

REM Count packages
set "PKG_COUNT=0"
for %%F in ("%PACKAGES_DIR%\*.whl") do set /a PKG_COUNT+=1
for %%F in ("%PACKAGES_DIR%\*.tar.gz") do set /a PKG_COUNT+=1

if %PKG_COUNT% EQU 0 (
    echo [ERROR] No packages found in %PACKAGES_DIR%
    echo [ERROR] Please run download_deps.bat first
    exit /b 1
)
echo [INFO] Found %PKG_COUNT% packages

REM Check wheel file
set "WHEEL_FOUND=0"
for %%F in ("%WHEELS_DIR%\*.whl") do (
    echo [INFO] Wheel file: %%~nxF
    set "WHEEL_FOUND=1"
)
if "%WHEEL_FOUND%"=="0" (
    echo [WARN] No cuscli wheel file found in %WHEELS_DIR%
    echo [WARN] Will install dependencies only
)

echo [INFO] System check passed
goto :eof

:create_venv
echo.
echo [INFO] Creating virtual environment...

if exist "%VENV_DIR%" (
    if "%AUTO_CONFIRM%"=="1" (
        echo [INFO] Removing existing virtual environment...
        rmdir /s /q "%VENV_DIR%"
    ) else (
        echo [WARN] Virtual environment already exists: %VENV_DIR%
        set /p CONFIRM="Do you want to recreate it? [y/N] "
        if /i "!CONFIRM!"=="y" (
            echo [INFO] Removing existing virtual environment...
            rmdir /s /q "%VENV_DIR%"
        ) else (
            echo [INFO] Using existing virtual environment
            goto :eof
        )
    )
)

%PYTHON_CMD% -m venv "%VENV_DIR%"
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    exit /b 1
)
echo [INFO] Virtual environment created: %VENV_DIR%
goto :eof

:upgrade_pip
echo.
echo [INFO] Upgrading pip in virtual environment...

call "%VENV_DIR%\Scripts\activate.bat"

REM Try to upgrade pip from local packages
pip install --no-index --find-links="%PACKAGES_DIR%" pip --upgrade --quiet 2>nul
if errorlevel 1 (
    echo [WARN] Could not upgrade pip from local packages, using bundled pip
) else (
    echo [INFO] pip upgraded from local package
)
REM Clear errorlevel - pip upgrade failure is not critical
cmd /c "exit /b 0"
goto :eof

:install_dependencies
echo.
echo [INFO] Installing dependencies from local packages...
echo [INFO] This may take a while...

call "%VENV_DIR%\Scripts\activate.bat"

REM Install wheel and setuptools first
pip install --no-index --find-links="%PACKAGES_DIR%" --find-links="%WHEELS_DIR%" wheel setuptools 2>nul

REM Install all dependencies from packages
pip install --no-index --find-links="%PACKAGES_DIR%" --find-links="%WHEELS_DIR%" -r "%SCRIPT_DIR%\requirements.txt"
if errorlevel 1 (
    echo [WARN] Some packages may have failed to install
    echo [WARN] Continuing with available packages...
)

echo [INFO] Dependencies installed
REM Clear errorlevel - partial install failure is not critical
cmd /c "exit /b 0"
goto :eof

:install_cuscli
echo.
echo [INFO] Installing cuscli...

call "%VENV_DIR%\Scripts\activate.bat"

set "WHEEL_FILE="
for %%F in ("%WHEELS_DIR%\*.whl") do set "WHEEL_FILE=%%F"

if defined WHEEL_FILE (
    pip install --no-index --find-links="%PACKAGES_DIR%" "%WHEEL_FILE%" --force-reinstall
    for %%F in ("%WHEEL_FILE%") do echo [INFO] Cuscli installed: %%~nxF
) else (
    echo [WARN] No cuscli wheel file found, skipping installation
)
goto :eof

:extract_cmder
echo.
echo [INFO] Setting up Cmder terminal...

set "CMDER_ZIP=%SCRIPT_DIR%\cmder_mini.zip"
set "CMDER_DIR=%SCRIPT_DIR%\cmder"

REM Check if Cmder zip exists
if not exist "%CMDER_ZIP%" (
    echo [INFO] Cmder Mini not found - skipping (optional component)
    goto :eof
)

REM Check if already extracted
if exist "%CMDER_DIR%\Cmder.exe" (
    echo [INFO] Cmder already extracted
    goto :eof
)

echo [INFO] Extracting Cmder Mini...

REM Use PowerShell to extract (available on Windows Server 2016+)
powershell -Command "& {Expand-Archive -Path '%CMDER_ZIP%' -DestinationPath '%CMDER_DIR%' -Force}" 2>nul
if errorlevel 1 (
    echo [WARN] Failed to extract Cmder using PowerShell
    echo [WARN] Trying alternative method...

    REM Try using tar (available on Windows 10 1803+)
    tar -xf "%CMDER_ZIP%" -C "%SCRIPT_DIR%" 2>nul
    if errorlevel 1 (
        echo [WARN] Failed to extract Cmder
        echo [WARN] Please manually extract %CMDER_ZIP% to %CMDER_DIR%
        echo [WARN] Cmder is optional - cuscli will still work without it
    ) else (
        echo [INFO] Cmder extracted successfully (using tar)
    )
) else (
    echo [INFO] Cmder extracted successfully
)

goto :eof

:register_cmder
echo.
echo [INFO] Registering Cmder command to system PATH...

REM Check if cuscliwin directory is already in PATH
echo %PATH% | findstr /i /c:"%SCRIPT_DIR%" >nul
if not errorlevel 1 (
    echo [INFO] Cuscliwin directory already in PATH
    goto :eof
)

REM Add cuscliwin directory to user PATH (no admin required)
REM This makes 'cmder.cmd' globally accessible
setx PATH "%PATH%;%SCRIPT_DIR%" >nul 2>&1
if errorlevel 1 (
    echo [WARN] Could not add to PATH automatically
    echo [WARN] To use 'cmder' command globally, please add this directory to PATH manually:
    echo [WARN]   %SCRIPT_DIR%
) else (
    echo [INFO] Cmder command registered successfully
    echo [INFO] After restarting Command Prompt, you can run 'cmder' from any directory
)

goto :eof

:verify_installation
echo.
echo [INFO] Verifying installation...

call "%VENV_DIR%\Scripts\activate.bat"

REM Check if cuscli is installed
pip show cuscli >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=2" %%v in ('pip show cuscli ^| findstr "^Version:"') do (
        echo [SUCCESS] Cuscli version: %%v
    )
) else (
    pip show auto-coder >nul 2>&1
    if not errorlevel 1 (
        for /f "tokens=2" %%v in ('pip show auto-coder ^| findstr "^Version:"') do (
            echo [SUCCESS] auto-coder version: %%v
        )
    )
)

REM Check entry points
if exist "%VENV_DIR%\Scripts\cuscli.exe" (
    echo [SUCCESS] Entry point 'cuscli': OK
) else (
    echo [WARN] Entry point 'cuscli' not found
)
goto :eof

:add_to_path
echo.
echo [INFO] Adding cuscli to system PATH...

REM Check if already in PATH
echo %PATH% | findstr /i /c:"%SCRIPT_DIR%" >nul
if not errorlevel 1 (
    echo [INFO] Already in PATH
    goto :eof
)

REM Add to user PATH using setx
setx PATH "%PATH%;%SCRIPT_DIR%" >nul 2>&1
if errorlevel 1 (
    echo [WARN] Could not add to PATH automatically
    echo [WARN] Please add this directory to PATH manually: %SCRIPT_DIR%
) else (
    echo [INFO] Added to PATH successfully
    echo [INFO] Please restart Command Prompt to use 'cuscli' command globally
)
goto :eof

:show_completion
echo.
echo ============================================
echo   Installation Complete!
echo ============================================
echo.
echo Virtual environment: %VENV_DIR%
echo Cuscli directory: %SCRIPT_DIR%
echo.
echo ============================================
echo   How to use cuscli
echo ============================================
echo.
echo Method 1: Use 'cmder' command (Recommended)
echo   After restarting Command Prompt, run from any directory:
echo.
echo     cmder
echo.
echo   This opens Cmder terminal with venv activated.
echo   Then cd to your project and run: cuscli
echo.
echo Method 2: Use start.bat directly
echo.
echo   %SCRIPT_DIR%\start.bat
echo.
echo NOTE: Restart Command Prompt for PATH changes to take effect!
echo.
goto :eof

:usage
echo.
echo Usage: %~nx0 [OPTIONS]
echo.
echo Options:
echo   -p, --python CMD   Specify Python command (default: python)
echo   -y, --yes          Auto-confirm all prompts
echo   -h, --help         Show this help message
echo.
echo Examples:
echo   %~nx0              Install with default settings
echo   %~nx0 -p py        Use 'py' launcher
echo   %~nx0 -y           Non-interactive mode
echo.
goto :end

:error
echo.
echo [ERROR] Installation failed with errors
exit /b 1

:end
endlocal
