@echo off
REM Cuscli 清理安装脚本 (Windows 批处理包装器)
REM 调用 PowerShell 脚本执行清理安装

setlocal enabledelayedexpansion

REM 检查是否在脚本目录中运行
cd /d "%~dp0"

REM 检查 PowerShell 脚本是否存在
if not exist "clean_install.ps1" (
    echo [错误] 找不到 clean_install.ps1 文件！
    echo 请确保此批处理文件与 clean_install.ps1 在同一目录下。
    pause
    exit /b 1
)

REM 如果没有参数，显示帮助
if "%~1"=="" (
    echo.
    echo Cuscli 清理安装工具 ^(Windows^)
    echo.
    echo 用法:
    echo     clean_install.bat ^<whl文件路径^> [选项]
    echo.
    echo 参数:
    echo     ^<whl文件路径^>         必需 - 指定 whl 文件路径
    echo     -Verbose              可选 - 详细输出清理过程
    echo     -DryRun               可选 - 模拟运行，不实际执行
    echo     -SkipVerify           可选 - 跳过安装后验证
    echo.
    echo 示例:
    echo     clean_install.bat dist\cuscli-1.0.4-py3-none-any.whl
    echo     clean_install.bat cuscli-1.0.4-py3-none-any.whl -Verbose
    echo     clean_install.bat cuscli-1.0.4-py3-none-any.whl -DryRun
    echo.
    pause
    exit /b 0
)

REM 构建 PowerShell 命令参数
set "PS_ARGS=-WheelFile \"%~1\""
shift

REM 处理其余参数
:parse_args
if "%~1"=="" goto run_script
set "PS_ARGS=%PS_ARGS% %~1"
shift
goto parse_args

:run_script
REM 执行 PowerShell 脚本
echo [信息] 正在调用 PowerShell 脚本...
echo.
PowerShell -ExecutionPolicy Bypass -File "%~dp0clean_install.ps1" %PS_ARGS%

REM 保存退出码
set EXITCODE=%ERRORLEVEL%

REM 如果失败则暂停以便查看错误信息
if %EXITCODE% neq 0 (
    echo.
    echo [错误] 脚本执行失败！退出码: %EXITCODE%
    pause
)

exit /b %EXITCODE%
