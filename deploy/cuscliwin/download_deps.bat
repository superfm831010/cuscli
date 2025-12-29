@echo off
REM =============================================================================
REM Cuscli Offline Deployment - Download Dependencies Script (Windows)
REM Description: Download all Windows x64 dependencies for offline installation
REM =============================================================================

setlocal enabledelayedexpansion

REM Script directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "PROJECT_ROOT=%SCRIPT_DIR%\..\.."

REM Configuration
set "PYTHON_VERSION=3.10"
set "REQUIREMENTS_FILE=%SCRIPT_DIR%\requirements.txt"
set "PACKAGES_DIR=%SCRIPT_DIR%\packages"
set "WHEELS_DIR=%SCRIPT_DIR%\wheels"

REM Parse arguments
:parse_args
if "%~1"=="" goto :main
if /i "%~1"=="-p" (
    set "PYTHON_VERSION=%~2"
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--python" (
    set "PYTHON_VERSION=%~2"
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="-h" goto :usage
if /i "%~1"=="--help" goto :usage
echo [ERROR] Unknown option: %~1
goto :usage

:main
call :print_header
call :check_requirements

call :download_python
if errorlevel 1 goto :error

REM If Python is not available, stop here and ask user to install
if not defined PYTHON_CMD (
    echo.
    echo ============================================
    echo   Python Not Installed
    echo ============================================
    echo.
    echo Python installer has been downloaded to:
    echo   %SCRIPT_DIR%\python\python-3.10.11-amd64.exe
    echo.
    echo Please:
    echo   1. Run the Python installer
    echo   2. CHECK "Add Python to PATH" during installation
    echo   3. Close and reopen Command Prompt
    echo   4. Run this script again to download packages
    echo.
    goto :end
)

call :download_packages
if errorlevel 1 goto :error

call :copy_wheel
call :show_summary

echo.
echo [INFO] Download completed successfully!
goto :end

:print_header
echo ============================================
echo   Cuscli Offline Deployment (Windows)
echo   Download Dependencies Script
echo ============================================
echo.
goto :eof

:check_requirements
echo [INFO] Checking requirements...

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
    echo [WARN] Python is not installed - will download Python installer
    echo [WARN] After download, please install Python first, then re-run this script
    goto :eof
)

echo [INFO] Python version: %PY_VER% (using %PYTHON_CMD%)

REM Check pip
%PYTHON_CMD% -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [WARN] pip is not available
    echo [WARN] Will continue to download packages anyway
)

REM Check requirements.txt
if not exist "%REQUIREMENTS_FILE%" (
    echo [WARN] requirements.txt not found: %REQUIREMENTS_FILE%
    echo [WARN] Will only download Python installer
) else (
    echo [INFO] All requirements satisfied
)
goto :eof

:download_python
echo.
echo [INFO] Downloading Python installer...

set "PYTHON_DIR=%SCRIPT_DIR%\python"
if not exist "%PYTHON_DIR%" mkdir "%PYTHON_DIR%"

REM Python download URL (3.10.11 is a stable LTS version)
set "PYTHON_URL=https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe"
set "PYTHON_FILE=%PYTHON_DIR%\python-3.10.11-amd64.exe"

if exist "%PYTHON_FILE%" (
    echo [INFO] Python installer already exists: python-3.10.11-amd64.exe
    goto :eof
)

echo [INFO] Downloading from %PYTHON_URL%
echo [INFO] This may take a few minutes...

REM Use PowerShell to download (more reliable than curl on Windows)
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_FILE%'}" 2>nul
if errorlevel 1 (
    REM Try curl as fallback
    curl -L -o "%PYTHON_FILE%" "%PYTHON_URL%" 2>nul
    if errorlevel 1 (
        echo [WARN] Failed to download Python installer
        echo [WARN] Please manually download from: %PYTHON_URL%
        echo [WARN] And place it in: %PYTHON_DIR%
    ) else (
        echo [INFO] Python installer downloaded successfully
    )
) else (
    echo [INFO] Python installer downloaded successfully
)

goto :eof

:download_packages
echo.
echo [INFO] Downloading Windows x64 packages...

if not exist "%PACKAGES_DIR%" mkdir "%PACKAGES_DIR%"

REM Download essential build tools first (pip, wheel, setuptools)
echo [INFO] Downloading essential build tools...
%PYTHON_CMD% -m pip download ^
    pip wheel setuptools ^
    -d "%PACKAGES_DIR%" ^
    --platform win_amd64 ^
    --only-binary=:all:

REM Download binary wheels for multiple Python versions (3.10, 3.11, 3.12)
REM This ensures compatibility with different target machines
echo [INFO] Downloading dependencies for Python 3.10...
%PYTHON_CMD% -m pip download ^
    -r "%REQUIREMENTS_FILE%" ^
    -d "%PACKAGES_DIR%" ^
    --python-version 3.10 ^
    --platform win_amd64 ^
    --only-binary=:all:

echo [INFO] Downloading dependencies for Python 3.11...
%PYTHON_CMD% -m pip download ^
    -r "%REQUIREMENTS_FILE%" ^
    -d "%PACKAGES_DIR%" ^
    --python-version 3.11 ^
    --platform win_amd64 ^
    --only-binary=:all:

echo [INFO] Downloading dependencies for Python 3.12...
%PYTHON_CMD% -m pip download ^
    -r "%REQUIREMENTS_FILE%" ^
    -d "%PACKAGES_DIR%" ^
    --python-version 3.12 ^
    --platform win_amd64 ^
    --only-binary=:all:

REM Download additional common binary packages that may be indirect dependencies
echo [INFO] Downloading additional common binary packages...
set "BINARY_PKGS=aiohttp frozenlist multidict propcache yarl contourpy duckdb greenlet kiwisolver markupsafe msgpack orjson pillow pydantic_core rpds_py cffi psutil"

for %%V in (3.10 3.11 3.12) do (
    %PYTHON_CMD% -m pip download ^
        %BINARY_PKGS% ^
        -d "%PACKAGES_DIR%" ^
        --python-version %%V ^
        --platform win_amd64 ^
        --only-binary=:all: 2>nul
)

echo [INFO] Packages downloaded to: %PACKAGES_DIR%
goto :eof

:copy_wheel
echo.
echo [INFO] Copying cuscli wheel package...

if not exist "%WHEELS_DIR%" mkdir "%WHEELS_DIR%"

REM Find wheel file in dist directory
set "WHEEL_FOUND=0"
for %%F in ("%PROJECT_ROOT%\dist\*.whl") do (
    copy /Y "%%F" "%WHEELS_DIR%\" >nul
    echo [INFO] Copied: %%~nxF
    set "WHEEL_FOUND=1"
)

if "%WHEEL_FOUND%"=="0" (
    echo [WARN] No wheel file found in %PROJECT_ROOT%\dist\
    echo [WARN] Please build the wheel first: python -m build
)
goto :eof

:show_summary
echo.
echo ============================================
echo   Download Summary
echo ============================================
echo.
echo Packages directory: %PACKAGES_DIR%
echo Wheels directory: %WHEELS_DIR%
echo.

REM Count packages
set "PKG_COUNT=0"
for %%F in ("%PACKAGES_DIR%\*.whl") do set /a PKG_COUNT+=1
for %%F in ("%PACKAGES_DIR%\*.tar.gz") do set /a PKG_COUNT+=1
echo Total packages: %PKG_COUNT%
echo.

REM List wheel files
echo Wheel packages:
for %%F in ("%WHEELS_DIR%\*.whl") do echo   - %%~nxF
echo.
goto :eof

:usage
echo.
echo Usage: %~nx0 [OPTIONS]
echo.
echo Options:
echo   -p, --python VER   Specify Python version (default: 3.10)
echo   -h, --help         Show this help message
echo.
echo Examples:
echo   %~nx0              Download with default settings
echo   %~nx0 -p 3.11      Download for Python 3.11
echo.
goto :end

:error
echo.
echo [ERROR] Download failed with errors
exit /b 1

:end
endlocal
