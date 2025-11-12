# Auto-Coder v1.0.39 源代码

> 🔒 **私有仓库** - 这是一个包含 Auto-Coder v1.0.39 源代码的私有仓库，用于二次开发目的。

## 📋 项目简介

本仓库包含 Auto-Coder v1.0.39 的完整源代码，这是一个 AI 驱动的编程助手工具。代码从官方 wheel 安装包中提取，用于二次开发和定制。

**原始安装包**：`auto-coder-1.0.39-py3-none-any.whl`

## ⚠️ 重要声明

本软件为**专有软件**，具有以下限制：
- ❌ 严格禁止商业使用
- ❌ 未经授权禁止分发源代码
- ✅ 仅供个人学习和研究使用
- ✅ 仅限封闭的非公开环境使用

完整许可协议详见 [dist-info/LICENSE](dist-info/LICENSE)。

## 🚀 快速开始

### 前置要求

- Python 3.10、3.11 或 3.12
- pip 包管理器
- 虚拟环境（推荐）

### 安装步骤

1. **克隆仓库**（如果您有访问权限）：
   ```bash
   git clone https://github.com/superfm831010/cuscli.git
   cd cuscli
   ```

2. **创建并激活虚拟环境**：
   ```bash
   # 使用 conda（推荐）
   conda create --name autocoder python=3.10.11
   conda activate autocoder

   # 或使用 venv
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # venv\Scripts\activate   # Windows
   ```

3. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

### 从源码运行

您可以直接从源代码运行 Auto-Coder，无需打包：

#### 方式一：使用 Python 模块（推荐）

```bash
# 启动聊天界面
python -m autocoder.chat_auto_coder

# 运行主 CLI
python -m autocoder.auto_coder --help

# 运行 SDK CLI
python -m autocoder.sdk.cli --help

# 运行 RAG 模式
python -m autocoder.auto_coder_rag
```

#### 方式二：开发模式安装

```bash
# 以可编辑/开发模式安装（修改立即生效）
pip install -e .
# 注意：需要添加 setup.py 或 pyproject.toml

# 然后像安装的包一样使用
auto-coder.chat
auto-coder --help
```

#### 方式三：直接执行 Python 文件

```bash
# 运行聊天界面
python autocoder/chat_auto_coder.py

# 运行主 CLI
python autocoder/auto_coder.py --help
```

## 📁 目录结构

```
cuscli/
├── .git/                   # Git 仓库
├── .gitignore              # Git 忽略规则
├── README.md               # 本文件
├── CLAUDE.md               # Claude Code 开发文档
├── requirements.txt        # Python 依赖列表
├── autocoder/              # 完整源代码（761 个 Python 文件）
│   ├── __init__.py
│   ├── auto_coder.py       # 主 CLI 入口
│   ├── chat_auto_coder.py  # 聊天界面入口
│   ├── auto_coder_rag.py   # RAG 模式入口
│   ├── agent/              # 智能代理系统
│   ├── checker/            # 代码检查系统（二次开发）
│   ├── common/             # 通用工具
│   ├── rag/                # RAG 系统
│   ├── index/              # 代码索引
│   ├── sdk/                # SDK 接口
│   ├── plugins/            # 插件系统
│   └── ...                 # 其他模块
├── rules/                  # 代码检查规则（二次开发）
│   ├── backend_rules.md    # 后端检查规则
│   ├── frontend_rules.md   # 前端检查规则
│   └── rules_config.json   # 规则配置
├── docs/                   # 文档目录
│   ├── code_checker_usage.md        # 代码检查使用指南
│   ├── code_checker_development.md  # 代码检查开发指南
│   └── ...                          # 其他文档
├── dist-info/              # 包元数据
│   ├── METADATA            # 包信息
│   ├── entry_points.txt    # CLI 入口点
│   └── LICENSE             # 许可证文件
└── original/               # 原始文件
    └── auto_coder-1.0.39-py3-none-any.whl
```

## 🔧 配置说明

### 环境变量

配置您的 API 密钥和设置：

```bash
# LLM API 密钥
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export GOOGLE_API_KEY="your-google-key"

# 模型配置
export AUTOCODER_MODEL="gpt-4"
export AUTOCODER_BASE_URL="https://api.openai.com/v1"
```

### 产品模式

Auto-Coder 支持两种产品模式：

- **lite 模式**：直接 API 调用，无需 Ray 集群（默认）
  - 使用 `SimpleByzerLLM`
  - 设置简单，适合本地开发

- **pro 模式**：支持 Ray 集群的分布式计算
  - 使用 `ByzerLLM`
  - 大规模操作性能更好

### 代码检查功能（二次开发）

本项目新增了基于 LLM 的智能代码检查功能：

**快速使用**：
```bash
# 启动 chat_auto_coder
python -m autocoder.chat_auto_coder

# 检查单个文件
/check /file src/main.py

# 检查整个项目
/check /folder

# 检查指定目录，过滤文件
/check /folder /path src /ext .py /ignore tests
```

**主要特性**：
- ✅ 基于 LLM 的智能语义检查
- ✅ 支持前后端不同规则集
- ✅ 大文件自动分块处理
- ✅ 并发检查提高效率
- ✅ 支持中断恢复
- ✅ 生成详细报告（JSON/Markdown）

**相关文件**：
- `autocoder/checker/` - 核心检查模块
- `autocoder/plugins/code_checker_plugin.py` - 插件集成
- `rules/` - 检查规则配置
- `docs/code_checker_usage.md` - 使用文档

## 📚 文档资源

- **[CLAUDE.md](CLAUDE.md)**：详细的架构和 Claude Code 开发指南
- **[dist-info/METADATA](dist-info/METADATA)**：包元数据和依赖信息
- **[代码检查使用指南](docs/code_checker_usage.md)**：代码检查功能详细使用文档
- **[代码检查开发指南](docs/code_checker_development.md)**：代码检查功能二次开发文档
- **官方文档**：https://uelng8wukz.feishu.cn/wiki/QIpkwpQo2iSdkwk9nP6cNSPlnPc

## 🛠️ 开发指南

### 入口点

包提供多个 CLI 入口点（在 `dist-info/entry_points.txt` 中定义）：

- `auto-coder` / `auto-coder.core` → `autocoder.auto_coder:main`
- `auto-coder.chat` / `chat-auto-coder` → `autocoder.chat_auto_coder:main`
- `auto-coder.run` / `auto-coder.cli` → `autocoder.sdk.cli:main`
- `auto-coder.rag` → `autocoder.auto_coder_rag:main`

### 修改源代码

由于直接从源码运行：

1. 编辑 `autocoder/` 目录中的任何 `.py` 文件
2. 再次运行代码时修改立即生效
3. 无需重新构建或重新安装

### 添加新功能

1. 在 `autocoder/` 目录中创建新模块
2. 在现有代码中导入并使用
3. 如果添加新依赖，更新 `requirements.txt`

## 🐛 故障排除

### 常见问题

1. **导入错误**：确保在项目根目录中运行
2. **缺少依赖**：运行 `pip install -r requirements.txt`
3. **Python 版本**：确保使用 Python 3.10-3.12
4. **权限问题**：使用虚拟环境

### 日志文件

日志存储位置：
```
.auto-coder/logs/auto-coder.log
```

## 📞 联系方式

- **仓库所有者**：superfm831010@gmail.com
- **原始项目**：https://github.com/allwefantasy/auto-coder

## 📄 许可证

本软件为专有软件，受商业使用限制约束。详见 [dist-info/LICENSE](dist-info/LICENSE)。

**版权所有 (c) 2024 auto-coder 项目所有者。保留所有权利。**

---

**注意**：这是一个用于二次开发的私有仓库。未经适当授权，请勿分发或共享。
