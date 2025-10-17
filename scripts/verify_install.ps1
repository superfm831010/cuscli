# Cuscli 安装验证脚本 (Windows PowerShell)
# 用于验证安装是否成功，版本是否正确
# 要求: PowerShell 5.0+

param(
    [Parameter(Mandatory=$false)]
    [switch]$Help = $false
)

# 设置错误处理
$ErrorActionPreference = "Continue"

# 颜色定义
$Colors = @{
    Info = "Cyan"
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Step = "Magenta"
}

# 打印带颜色的消息
function Print-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor $Colors.Info
}

function Print-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor $Colors.Success
}

function Print-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor $Colors.Error
}

function Print-Step {
    param([string]$Message)
    Write-Host "🔧 $Message" -ForegroundColor $Colors.Step
}

# 显示帮助信息
if ($Help) {
    Write-Host ""
    Write-Host "Cuscli 安装验证脚本 (Windows)" -ForegroundColor Green
    Write-Host ""
    Write-Host "用法:" -ForegroundColor Yellow
    Write-Host "    .\scripts\verify_install.ps1"
    Write-Host ""
    Write-Host "说明:" -ForegroundColor Yellow
    Write-Host "    自动运行 7 项测试验证 cuscli 安装是否成功"
    Write-Host ""
    exit 0
}

# 检测 Python 命令
$PythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $PythonCmd = "python3"
} else {
    Print-Error "未找到 Python 命令！"
    exit 1
}

# 显示 banner
Write-Host ""
Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     " -NoNewline -ForegroundColor Cyan
Write-Host "Cuscli 安装验证工具" -NoNewline -ForegroundColor Green
Write-Host "                 ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$PassCount = 0
$FailCount = 0
$TotalTests = 7

# 测试1: 检查 pip show
Print-Step "测试 1/$TotalTests`: 检查 pip 包信息"
try {
    $pipShowOutput = pip show cuscli 2>&1
    if ($LASTEXITCODE -eq 0) {
        $installedVersion = ($pipShowOutput | Select-String "Version:").ToString().Split(":")[1].Trim()
        $installedLocation = ($pipShowOutput | Select-String "Location:").ToString().Split(":")[1].Trim()

        Write-Host "  包名: " -NoNewline
        Write-Host "cuscli" -ForegroundColor Green
        Write-Host "  版本: " -NoNewline
        Write-Host "$installedVersion" -ForegroundColor Green
        Write-Host "  位置: " -NoNewline
        Write-Host "$installedLocation" -ForegroundColor Cyan
        Print-Success "  测试通过"
        $PassCount++
    } else {
        Print-Error "  cuscli 未安装"
        $FailCount++
    }
} catch {
    Print-Error "  cuscli 未安装"
    $FailCount++
}
Write-Host ""

# 测试2: 检查 Python 版本导入
Print-Step "测试 2/$TotalTests`: 检查 Python 版本导入"
try {
    $pythonVersion = & $PythonCmd -c "from autocoder.version import __version__; print(__version__)" 2>&1
    if ($LASTEXITCODE -eq 0 -and $pythonVersion) {
        Write-Host "  autocoder.version.__version__ = " -NoNewline
        Write-Host "$pythonVersion" -ForegroundColor Green

        # 验证版本号一致性
        if ($pythonVersion -eq $installedVersion) {
            Print-Success "  版本号一致"
        } else {
            Print-Error "  版本号不一致！pip: $installedVersion vs Python: $pythonVersion"
        }
        Print-Success "  测试通过"
        $PassCount++
    } else {
        Print-Error "  无法导入 autocoder.version"
        $FailCount++
    }
} catch {
    Print-Error "  无法导入 autocoder.version"
    $FailCount++
}
Write-Host ""

# 测试3: 检查主入口点
Print-Step "测试 3/$TotalTests`: 检查主入口点"
if (Get-Command cuscli -ErrorAction SilentlyContinue) {
    $cuscliPath = (Get-Command cuscli).Source
    Write-Host "  cuscli 命令路径: " -NoNewline
    Write-Host "$cuscliPath" -ForegroundColor Cyan
    Print-Success "  测试通过"
    $PassCount++
} else {
    Print-Error "  cuscli 命令未找到"
    $FailCount++
}
Write-Host ""

# 测试4: 检查 checker 模块
Print-Step "测试 4/$TotalTests`: 检查 checker 模块"
try {
    $checkerResult = & $PythonCmd -c @"
try:
    from autocoder.checker import core, rules_loader, file_processor
    print('OK')
except Exception as e:
    print(f'FAIL: {e}')
"@ 2>&1

    if ($checkerResult -eq "OK") {
        Write-Host "  autocoder.checker.core: " -NoNewline
        Write-Host "✓" -ForegroundColor Green
        Write-Host "  autocoder.checker.rules_loader: " -NoNewline
        Write-Host "✓" -ForegroundColor Green
        Write-Host "  autocoder.checker.file_processor: " -NoNewline
        Write-Host "✓" -ForegroundColor Green
        Print-Success "  测试通过"
        $PassCount++
    } else {
        Write-Host "  $checkerResult" -ForegroundColor Red
        Print-Error "  checker 模块导入失败"
        $FailCount++
    }
} catch {
    Print-Error "  checker 模块导入失败"
    $FailCount++
}
Write-Host ""

# 测试5: 检查 checker 插件
Print-Step "测试 5/$TotalTests`: 检查 code_checker_plugin"
try {
    $pluginResult = & $PythonCmd -c @"
try:
    from autocoder.plugins.code_checker_plugin import CodeCheckerPlugin
    plugin = CodeCheckerPlugin()
    print(f'OK:{plugin.plugin_name()}:{plugin.version}')
except Exception as e:
    print(f'FAIL:{e}')
"@ 2>&1

    if ($pluginResult -like "OK:*") {
        $parts = $pluginResult.Split(":")
        $pluginName = $parts[1]
        $pluginVersion = $parts[2]
        Write-Host "  插件名称: " -NoNewline
        Write-Host "$pluginName" -ForegroundColor Green
        Write-Host "  插件版本: " -NoNewline
        Write-Host "$pluginVersion" -ForegroundColor Green
        Print-Success "  测试通过"
        $PassCount++
    } else {
        Write-Host "  $pluginResult" -ForegroundColor Red
        Print-Error "  插件加载失败"
        $FailCount++
    }
} catch {
    Print-Error "  插件加载失败"
    $FailCount++
}
Write-Host ""

# 测试6: 检查 checker 命令注册
Print-Step "测试 6/$TotalTests`: 检查 /check 命令注册"
try {
    $commandsResult = & $PythonCmd -c @"
try:
    from autocoder.plugins.code_checker_plugin import CodeCheckerPlugin
    plugin = CodeCheckerPlugin()
    commands = plugin.register_commands()
    if commands:
        for cmd in commands.keys():
            print(cmd)
        print('OK')
    else:
        print('FAIL:No commands registered')
except Exception as e:
    print(f'FAIL:{e}')
"@ 2>&1

    if ($commandsResult -match "OK") {
        Write-Host "  注册的命令："
        $lines = $commandsResult -split "`n"
        foreach ($line in $lines) {
            if ($line -ne "OK" -and $line.Trim() -ne "") {
                Write-Host "    - " -NoNewline
                Write-Host "$line" -ForegroundColor Green
            }
        }
        Print-Success "  测试通过"
        $PassCount++
    } else {
        Write-Host "  $commandsResult" -ForegroundColor Red
        Print-Error "  命令注册失败"
        $FailCount++
    }
} catch {
    Print-Error "  命令注册失败"
    $FailCount++
}
Write-Host ""

# 测试7: 检查数据文件
Print-Step "测试 7/$TotalTests`: 检查规则数据文件"
try {
    $dataResult = & $PythonCmd -c @"
import os
try:
    from autocoder import checker
    checker_dir = os.path.dirname(checker.__file__)
    parent_dir = os.path.dirname(checker_dir)
    rules_dir = os.path.join(parent_dir, 'data', 'rules')

    if os.path.exists(rules_dir):
        rules_config = os.path.join(rules_dir, 'rules_config.json')
        frontend_rules = os.path.join(rules_dir, 'frontend_rules.md')
        backend_rules = os.path.join(rules_dir, 'backend_rules.md')

        files_found = []
        if os.path.exists(rules_config):
            files_found.append('rules_config.json')
        if os.path.exists(frontend_rules):
            files_found.append('frontend_rules.md')
        if os.path.exists(backend_rules):
            files_found.append('backend_rules.md')

        if files_found:
            print('OK:' + ','.join(files_found))
        else:
            print('FAIL:Rules directory exists but no rule files found')
    else:
        print(f'FAIL:Rules directory not found: {rules_dir}')
except Exception as e:
    print(f'FAIL:{e}')
"@ 2>&1

    if ($dataResult -like "OK:*") {
        $files = $dataResult.Split(":")[1].Split(",")
        Write-Host "  规则文件："
        foreach ($file in $files) {
            Write-Host "    - " -NoNewline
            Write-Host "$file" -ForegroundColor Green
        }
        Print-Success "  测试通过"
        $PassCount++
    } else {
        Write-Host "  $dataResult" -ForegroundColor Red
        Print-Error "  规则文件检查失败"
        $FailCount++
    }
} catch {
    Print-Error "  规则文件检查失败"
    $FailCount++
}
Write-Host ""

# 显示测试汇总
Write-Host ""
Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     " -NoNewline -ForegroundColor Cyan
Write-Host "测试汇总" -NoNewline -ForegroundColor Green
Write-Host "                                ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "  总测试数: $TotalTests"
Write-Host "  通过: " -NoNewline
Write-Host "$PassCount" -ForegroundColor Green

if ($FailCount -gt 0) {
    Write-Host "  失败: " -NoNewline
    Write-Host "$FailCount" -ForegroundColor Red
    Write-Host ""
    Print-Error "验证失败！"
    Write-Host ""
    Print-Info "建议操作："
    Write-Host "  1. 重新运行清理安装脚本："
    Write-Host "     .\scripts\clean_install.ps1 -WheelFile <whl文件>"
    Write-Host ""
    Write-Host "  2. 检查 Python 环境："
    Write-Host "     $PythonCmd --version"
    Write-Host "     pip list | Select-String cuscli"
    Write-Host ""
    exit 1
} else {
    Write-Host ""
    Print-Success "所有测试通过！安装验证成功！"
    Write-Host ""
    Print-Info "可以开始使用 cuscli 了："
    Write-Host "  cuscli"
    Write-Host ""
    Print-Info "尝试以下命令："
    Write-Host "  /help          - 查看帮助"
    Write-Host "  /check /help   - 查看 checker 帮助"
    Write-Host "  /plugins       - 查看已加载的插件"
    Write-Host ""
    exit 0
}
