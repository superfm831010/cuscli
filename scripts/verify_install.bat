@echo off
REM Cuscli 安装验证脚本 (Windows 批处理包装器)
REM 调用 PowerShell 脚本执行验证

setlocal enabledelayedexpansion

REM 检查是否在脚本目录中运行
cd /d "%~dp0"

REM 检查 PowerShell 脚本是否存在
if not exist "verify_install.ps1" (
    echo [错误] 找不到 verify_install.ps1 文件！
    echo 请确保此批处理文件与 verify_install.ps1 在同一目录下。
    pause
    exit /b 1
)

REM 检查是否请求帮助
if "%~1"=="-h" goto show_help
if "%~1"=="/?" goto show_help
if "%~1"=="--help" goto show_help
if "%~1"=="-Help" goto show_help

REM 直接运行验证脚本（不需要参数）
echo [信息] 正在调用 PowerShell 验证脚本...
echo.
PowerShell -ExecutionPolicy Bypass -File "%~dp0verify_install.ps1"

REM 保存退出码
set EXITCODE=%ERRORLEVEL%

REM 如果失败则暂停以便查看错误信息
if %EXITCODE% neq 0 (
    echo.
    echo [错误] 验证失败！退出码: %EXITCODE%
    pause
)

exit /b %EXITCODE%

:show_help
echo.
echo Cuscli 安装验证工具 ^(Windows^)
echo.
echo 用法:
echo     verify_install.bat
echo.
echo 说明:
echo     自动运行 7 项测试验证 cuscli 安装是否成功
echo.
echo 测试项目:
echo     1. 检查 pip 包信息
echo     2. 检查 Python 版本导入
echo     3. 检查主入口点
echo     4. 检查 checker 模块
echo     5. 检查 code_checker_plugin
echo     6. 检查 /check 命令注册
echo     7. 检查规则数据文件
echo.
pause
exit /b 0
