# Cuscli Windows 离线部署指南

本目录包含 Cuscli AI 编程助手的 Windows 离线部署包。

## 目录结构

```
cuscliwin/
├── README.md              # 本文档
├── download_deps.bat      # 下载依赖包脚本
├── install_offline.bat    # 离线安装脚本
├── start.bat              # 启动脚本
├── python/                # Python 安装包
│   └── python-3.10.11-amd64.exe
├── venv/                  # 虚拟环境（安装后生成）
├── packages/              # Windows x64 依赖包
└── wheels/                # cuscli wheel 包
```

## 使用流程

### 第一步：在联网环境下载依赖

在一台可以访问互联网的 Windows 机器上：

```cmd
cd cuscliwin
download_deps.bat
```

脚本会自动下载：
- Python 3.10 安装程序
- 所有依赖包
- cuscli wheel 包

### 第二步：打包传输

将整个 `cuscliwin` 文件夹打包为 zip 文件，传输到内网机器：

1. 右键点击 `cuscliwin` 文件夹
2. 选择"发送到" -> "压缩(zipped)文件夹"
3. 将生成的 zip 文件复制到 U 盘

### 第三步：安装 Python（如未安装）

如果目标机器没有 Python，先安装：

1. 运行 `python\python-3.10.11-amd64.exe`
2. **重要：勾选 "Add Python to PATH"**
3. 点击 "Install Now" 完成安装
4. 重新打开命令提示符

### 第四步：安装 Cuscli

```cmd
cd cuscliwin
install_offline.bat
```

### 第五步：启动使用

安装完成后，**重启命令提示符**，然后可以在任意项目目录直接运行：

```cmd
cd C:\your\project\directory
cuscli
```

就这么简单！cuscli 会自动使用虚拟环境，无需手动激活。

## 脚本参数说明

### download_deps.bat

| 参数 | 说明 |
|------|------|
| `-p, --python VER` | 指定 Python 版本（默认 3.10）|
| `-h, --help` | 显示帮助 |

### install_offline.bat

| 参数 | 说明 |
|------|------|
| `-p, --python CMD` | 指定 Python 命令（默认 python）|
| `-y, --yes` | 自动确认所有提示 |
| `-h, --help` | 显示帮助 |

## 系统要求

- Windows 10/11 x64
- Python 3.10 - 3.12（安装包已包含）
- 磁盘空间：至少 2GB

## 常见问题

### Q: 安装时提示找不到 Python？

A: 请先安装 Python：
1. 运行 `python\python-3.10.11-amd64.exe`
2. **必须勾选 "Add Python to PATH"**
3. 安装完成后，关闭并重新打开命令提示符
4. 重新运行 `install_offline.bat`

### Q: 安装时提示找不到某些包？

A: 可能是下载不完整。请在联网环境重新运行 `download_deps.bat`。

### Q: 如何更新到新版本？

A:
1. 获取新的 wheel 包放入 `wheels/` 目录
2. 运行安装脚本：`install_offline.bat -y`

### Q: 中文显示乱码？

A: 脚本会自动设置 UTF-8 编码。如果仍有问题：
1. 确保系统区域设置使用 UTF-8
2. 使用 Windows Terminal 或支持 UTF-8 的终端

### Q: 如何手动激活虚拟环境？

```cmd
call cuscliwin\venv\Scripts\activate.bat
cuscli
```

## 技术支持

如遇问题，请参考项目文档或联系技术支持。
