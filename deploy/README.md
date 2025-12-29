# Cuscli 离线部署指南

本目录包含 Cuscli AI 编程助手的离线部署脚本。

## 目录结构

```
deploy/
├── README.md                    # 本文档
├── download_deps.sh             # Linux: 下载依赖包脚本
├── install_offline.sh           # Linux: 离线安装脚本
├── start.sh                     # Linux: 启动脚本
├── venv/                        # 虚拟环境（安装后生成）
├── packages/
│   └── linux_x86_64/           # Linux x86_64 依赖包
├── wheels/                      # cuscli wheel 包
└── cuscliwin/                   # Windows 专用部署目录
    ├── README.md               # Windows 使用说明
    ├── download_deps.bat       # 下载依赖包脚本
    ├── install_offline.bat     # 离线安装脚本
    ├── start.bat               # 启动脚本
    ├── packages/               # Windows x64 依赖包
    └── wheels/                 # cuscli wheel 包
```

## Linux/银河麒麟 部署

### 第一步：下载依赖

在联网环境运行：

```bash
cd deploy
chmod +x download_deps.sh
./download_deps.sh
```

### 第二步：打包传输

```bash
zip -r cuscli-linux.zip deploy/
# 排除 Windows 目录可节省空间
zip -r cuscli-linux.zip deploy/ -x "deploy/cuscliwin/*"
```

### 第三步：安装

在目标机器解压后运行：

```bash
cd deploy
chmod +x install_offline.sh start.sh
./install_offline.sh
```

### 第四步：启动

```bash
./start.sh
```

## Windows 部署

请参考 `cuscliwin/README.md`，Windows 部署包是独立的。

### 快速步骤

1. 在联网 Windows 机器运行 `cuscliwin/download_deps.bat`
2. 将 `cuscliwin` 文件夹打包为 zip
3. 传输到内网机器，运行 `install_offline.bat`
4. 使用 `start.bat` 启动

## 系统要求

| 平台 | 架构 | Python | 磁盘空间 |
|------|------|--------|----------|
| Linux/银河麒麟 | x86_64 | 3.10-3.12 | 2GB |
| Windows 10/11 | x64 | 3.10-3.12 | 2GB |

## 常见问题

### Q: 如何更新到新版本？

1. 获取新的 wheel 包
2. 放入对应的 `wheels/` 目录
3. 运行安装脚本：`./install_offline.sh -y`

### Q: 手动激活虚拟环境？

**Linux:**
```bash
source deploy/venv/bin/activate
```

**Windows:**
```cmd
call cuscliwin\venv\Scripts\activate.bat
```

## 技术支持

如遇问题，请参考项目文档或联系技术支持。
