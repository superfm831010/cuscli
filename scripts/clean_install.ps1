# Cuscli 清理安装脚本 (Windows PowerShell)
# 用于完全清理旧版本并安装新版本
# 要求: PowerShell 5.0+

param(
    [Parameter(Mandatory=$false)]
    [string]$WheelFile = "",

    [Parameter(Mandatory=$false)]
    [switch]$Verbose = $false,

    [Parameter(Mandatory=$false)]
    [switch]$DryRun = $false,

    [Parameter(Mandatory=$false)]
    [switch]$SkipVerify = $false,

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

function Print-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor $Colors.Warning
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
function Show-Help {
    Write-Host ""
    Write-Host "Cuscli 清理安装脚本 (Windows)" -ForegroundColor Green
    Write-Host ""
    Write-Host "用法:" -ForegroundColor Yellow
    Write-Host "    .\scripts\clean_install.ps1 -WheelFile <file> [选项]"
    Write-Host ""
    Write-Host "参数:" -ForegroundColor Yellow
    Write-Host "    -WheelFile <file>      指定 whl 文件路径（必需）"
    Write-Host "    -Verbose               详细输出清理过程"
    Write-Host "    -DryRun                模拟运行，不实际执行"
    Write-Host "    -SkipVerify            跳过安装后验证"
    Write-Host "    -Help                  显示帮助信息"
    Write-Host ""
    Write-Host "示例:" -ForegroundColor Yellow
    Write-Host "    .\scripts\clean_install.ps1 -WheelFile dist\cuscli-1.0.4-py3-none-any.whl"
    Write-Host "    .\scripts\clean_install.ps1 -WheelFile .\cuscli-1.0.4-py3-none-any.whl -Verbose"
    Write-Host "    .\scripts\clean_install.ps1 -WheelFile .\cuscli-1.0.4-py3-none-any.whl -DryRun"
    Write-Host ""
    Write-Host "清理流程:" -ForegroundColor Yellow
    Write-Host "    1. 卸载旧版本 cuscli"
    Write-Host "    2. 清理 pip 缓存"
    Write-Host "    3. 清理 site-packages 中的残留文件"
    Write-Host "    4. 清理 Python 字节码缓存 (.pyc, __pycache__)"
    Write-Host "    5. 安装新版本（使用 --no-cache-dir --force-reinstall）"
    Write-Host "    6. 验证安装结果"
    Write-Host ""
}

# 显示帮助并退出
if ($Help) {
    Show-Help
    exit 0
}

# 检查必需参数
if ([string]::IsNullOrEmpty($WheelFile)) {
    Print-Error "缺少 -WheelFile 参数"
    Write-Host ""
    Show-Help
    exit 1
}

# 检查 whl 文件是否存在
if (-not (Test-Path $WheelFile)) {
    Print-Error "whl 文件不存在: $WheelFile"
    exit 1
}

# 获取 whl 文件的绝对路径
$WheelFile = Resolve-Path $WheelFile

# 检测 Python 命令
$PythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $PythonCmd = "python3"
} else {
    Print-Error "未找到 Python 命令！请确保已安装 Python 3.10+"
    exit 1
}

# 显示 banner
Write-Host ""
Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     " -NoNewline -ForegroundColor Cyan
Write-Host "Cuscli 清理安装工具" -NoNewline -ForegroundColor Green
Write-Host "                 ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Print-Warning "模拟运行模式 (-DryRun)，不会实际执行操作"
    Write-Host ""
}

$PythonVersion = & $PythonCmd --version 2>&1
Print-Info "Python 版本: $PythonVersion"
Print-Info "whl 文件: $WheelFile"
Write-Host ""

# 执行命令的包装函数
function Invoke-Cmd {
    param(
        [string]$Command,
        [string]$Description
    )

    if ($Verbose) {
        Write-Host "  → 执行: $Command"
    }

    if (-not $DryRun) {
        try {
            $output = Invoke-Expression $Command 2>&1
            return $true
        } catch {
            if ($Verbose) {
                Write-Host "  ✗ 错误: $_" -ForegroundColor Red
            }
            return $false
        }
    } else {
        Write-Host "  [DRY RUN] $Command" -ForegroundColor Gray
        return $true
    }
}

# 步骤1: 卸载旧版本
Print-Step "步骤 1/5: 卸载旧版本 cuscli..."
$uninstallResult = Invoke-Cmd -Command "pip uninstall -y cuscli" -Description "卸载 cuscli"
if ($uninstallResult) {
    Print-Success "已卸载旧版本"
} else {
    Print-Info "未找到已安装的 cuscli（可能是首次安装）"
}
Write-Host ""

# 步骤2: 清理 pip 缓存
Print-Step "步骤 2/5: 清理 pip 缓存..."
$cacheResult = Invoke-Cmd -Command "pip cache remove cuscli" -Description "清理 cuscli 缓存"
if ($cacheResult) {
    Print-Success "已清理 cuscli pip 缓存"
} else {
    if ($Verbose) {
        Print-Info "pip cache remove 失败，尝试 purge..."
    }
    $purgeResult = Invoke-Cmd -Command "pip cache purge" -Description "清理所有 pip 缓存"
    if ($purgeResult) {
        Print-Success "已清理所有 pip 缓存"
    } else {
        Print-Warning "无法清理 pip 缓存（可能不支持此功能）"
    }
}
Write-Host ""

# 步骤3: 清理 site-packages 残留
Print-Step "步骤 3/5: 清理 site-packages 残留文件..."

# 获取 site-packages 路径
$sitePackagesDirs = @()
try {
    $sitePackagesOutput = & $PythonCmd -c "import site; print('\n'.join(site.getsitepackages()))" 2>&1
    if ($sitePackagesOutput) {
        $sitePackagesDirs += $sitePackagesOutput -split "`n" | Where-Object { $_ -ne "" }
    }
} catch {
    if ($Verbose) {
        Print-Warning "无法获取全局 site-packages 路径"
    }
}

# 添加用户 site-packages
try {
    $userSite = & $PythonCmd -m site --user-site 2>&1
    if ($userSite -and (Test-Path $userSite)) {
        $sitePackagesDirs += $userSite
    }
} catch {
    # 忽略错误
}

$cleanedCount = 0

foreach ($siteDir in $sitePackagesDirs) {
    $siteDir = $siteDir.Trim()
    if ([string]::IsNullOrEmpty($siteDir) -or -not (Test-Path $siteDir)) {
        continue
    }

    if ($Verbose) {
        Write-Host "  → 检查目录: $siteDir"
    }

    # 清理 autocoder 目录
    $autocoderPath = Join-Path $siteDir "autocoder"
    if (Test-Path $autocoderPath) {
        if ($Verbose) {
            Write-Host "    → 发现 autocoder/ 目录"
        }
        if (-not $DryRun) {
            try {
                Remove-Item -Path $autocoderPath -Recurse -Force
                Print-Success "  已删除: $autocoderPath"
                $cleanedCount++
            } catch {
                Print-Warning "  无法删除: $autocoderPath"
            }
        } else {
            Write-Host "  [DRY RUN] Remove-Item -Path $autocoderPath -Recurse -Force" -ForegroundColor Gray
            $cleanedCount++
        }
    }

    # 清理 cuscli*.dist-info 目录
    $distInfos = Get-ChildItem -Path $siteDir -Filter "cuscli*.dist-info" -Directory -ErrorAction SilentlyContinue
    foreach ($distInfo in $distInfos) {
        if ($Verbose) {
            Write-Host "    → 发现 $($distInfo.Name)"
        }
        if (-not $DryRun) {
            try {
                Remove-Item -Path $distInfo.FullName -Recurse -Force
                Print-Success "  已删除: $($distInfo.FullName)"
                $cleanedCount++
            } catch {
                Print-Warning "  无法删除: $($distInfo.FullName)"
            }
        } else {
            Write-Host "  [DRY RUN] Remove-Item -Path $($distInfo.FullName) -Recurse -Force" -ForegroundColor Gray
            $cleanedCount++
        }
    }
}

if ($cleanedCount -eq 0) {
    Print-Info "未发现需要清理的残留文件"
} else {
    Print-Success "共清理 $cleanedCount 个目录"
}
Write-Host ""

# 步骤4: 清理 Python 字节码缓存
Print-Step "步骤 4/5: 清理 Python 字节码缓存..."

$cacheCleaned = 0

foreach ($siteDir in $sitePackagesDirs) {
    $siteDir = $siteDir.Trim()
    if ([string]::IsNullOrEmpty($siteDir) -or -not (Test-Path $siteDir)) {
        continue
    }

    # 清理 .pyc 文件
    $pycFiles = Get-ChildItem -Path $siteDir -Filter "*.pyc" -Recurse -ErrorAction SilentlyContinue
    if ($pycFiles) {
        if ($Verbose) {
            $pycCount = ($pycFiles | Measure-Object).Count
            Write-Host "  → 发现 $pycCount 个 .pyc 文件"
        }
        if (-not $DryRun) {
            foreach ($pycFile in $pycFiles) {
                try {
                    Remove-Item -Path $pycFile.FullName -Force -ErrorAction SilentlyContinue
                } catch {
                    # 忽略错误
                }
            }
            $cacheCleaned++
        }
    }

    # 清理 __pycache__ 目录
    $pycacheDirs = Get-ChildItem -Path $siteDir -Filter "__pycache__" -Directory -Recurse -ErrorAction SilentlyContinue
    if ($pycacheDirs) {
        if ($Verbose) {
            $pycacheCount = ($pycacheDirs | Measure-Object).Count
            Write-Host "  → 发现 $pycacheCount 个 __pycache__ 目录"
        }
        if (-not $DryRun) {
            foreach ($pycacheDir in $pycacheDirs) {
                try {
                    Remove-Item -Path $pycacheDir.FullName -Recurse -Force -ErrorAction SilentlyContinue
                } catch {
                    # 忽略错误
                }
            }
            $cacheCleaned++
        }
    }
}

if ($cacheCleaned -gt 0) {
    Print-Success "已清理字节码缓存"
} else {
    Print-Info "未发现需要清理的字节码缓存"
}
Write-Host ""

# 步骤5: 安装新版本
Print-Step "步骤 5/5: 安装新版本..."
Write-Host ""

if (-not $DryRun) {
    Print-Info "使用参数: --no-cache-dir --force-reinstall"
    $installResult = & pip install --no-cache-dir --force-reinstall $WheelFile
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Print-Success "安装成功！"
    } else {
        Write-Host ""
        Print-Error "安装失败！"
        exit 1
    }
} else {
    Write-Host "  [DRY RUN] pip install --no-cache-dir --force-reinstall $WheelFile" -ForegroundColor Gray
    Print-Info "模拟运行完成"
}
Write-Host ""

# 验证安装
if (-not $SkipVerify -and -not $DryRun) {
    Print-Step "验证安装结果..."
    Write-Host ""

    # 检查 pip show
    Print-Info "检查安装的包信息："
    $pipShowOutput = pip show cuscli 2>&1
    $installedVersion = ($pipShowOutput | Select-String "Version:").ToString().Split(":")[1].Trim()
    if ($installedVersion) {
        Write-Host "  版本: " -NoNewline
        Write-Host "$installedVersion" -ForegroundColor Green
    } else {
        Print-Error "  无法获取版本信息"
    }

    # 检查 Python 导入
    Write-Host ""
    Print-Info "检查 Python 导入："
    try {
        $pythonVersion = & $PythonCmd -c "from autocoder.version import __version__; print(__version__)" 2>&1
        if ($pythonVersion) {
            Write-Host "  autocoder.version.__version__ = " -NoNewline
            Write-Host "$pythonVersion" -ForegroundColor Green
            Print-Success "  ✓ 版本导入正常"
        }
    } catch {
        Print-Error "  ✗ 无法导入版本号"
    }

    # 检查 checker 插件
    Write-Host ""
    Print-Info "检查 checker 插件："
    try {
        $checkerResult = & $PythonCmd -c "from autocoder.plugins.code_checker_plugin import CodeCheckerPlugin; print('OK')" 2>&1
        if ($checkerResult -eq "OK") {
            Print-Success "  ✓ CodeCheckerPlugin 加载成功"
        } else {
            Print-Error "  ✗ CodeCheckerPlugin 加载失败"
        }
    } catch {
        Print-Error "  ✗ CodeCheckerPlugin 加载失败"
    }

    Write-Host ""
}

# 显示完成信息
Write-Host ""
Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     " -NoNewline -ForegroundColor Cyan
Write-Host "✨ 清理安装完成！" -NoNewline -ForegroundColor Green
Write-Host "                    ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

if (-not $DryRun) {
    Print-Info "下一步："
    Write-Host ""
    Write-Host "  1. 启动 cuscli："
    Write-Host "     cuscli"
    Write-Host ""
    Write-Host "  2. 验证 /check 命令："
    Write-Host "     输入 /check 然后按 Tab 查看补全"
    Write-Host ""
    Write-Host "  3. 如需详细验证："
    Write-Host "     .\scripts\verify_install.ps1"
    Write-Host ""
} else {
    Print-Warning "这是模拟运行，实际操作未执行"
    Write-Host ""
    Print-Info "如需实际执行，请去掉 -DryRun 参数："
    Write-Host "  .\scripts\clean_install.ps1 -WheelFile $WheelFile"
    Write-Host ""
}

exit 0
