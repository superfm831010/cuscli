# Auto-Coder v1.0.39 Source Code

> 🔒 **Private Repository** - This is a private repository containing the source code of Auto-Coder v1.0.39 for secondary development purposes.

## 📋 Project Description

This repository contains the complete source code of Auto-Coder v1.0.39, an AI-powered coding assistant tool. The code has been extracted from the official wheel package for secondary development and customization.

**Original Package**: `auto-coder-1.0.39-py3-none-any.whl`

## ⚠️ Important Notice

This software is **proprietary software** with the following restrictions:
- ❌ Commercial use is strictly prohibited
- ❌ Source code distribution is prohibited without authorization
- ✅ Personal learning and research only
- ✅ Closed, non-public environment use

For full license details, see [dist-info/LICENSE](dist-info/LICENSE).

## 🚀 Quick Start

### Prerequisites

- Python 3.10, 3.11, or 3.12
- pip package manager
- Virtual environment (recommended)

### Installation

1. **Clone the repository** (if you have access):
   ```bash
   git clone https://github.com/superfm831010/cuscli.git
   cd cuscli
   ```

2. **Create and activate virtual environment**:
   ```bash
   # Using conda (recommended)
   conda create --name autocoder python=3.10.11
   conda activate autocoder

   # Or using venv
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # venv\Scripts\activate   # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running from Source

You can run Auto-Coder directly from source code without packaging:

#### Option 1: Using Python Module (Recommended)

```bash
# Start chat interface
python -m autocoder.chat_auto_coder

# Run main CLI
python -m autocoder.auto_coder --help

# Run SDK CLI
python -m autocoder.sdk.cli --help

# Run RAG mode
python -m autocoder.auto_coder_rag
```

#### Option 2: Development Mode Installation

```bash
# Install in editable/development mode (changes take effect immediately)
pip install -e .
# Note: Requires setup.py or pyproject.toml (to be added)

# Then use like installed package
auto-coder.chat
auto-coder --help
```

#### Option 3: Direct Python Execution

```bash
# Run chat interface
python autocoder/chat_auto_coder.py

# Run main CLI
python autocoder/auto_coder.py --help
```

## 📁 Directory Structure

```
cuscli/
├── .git/                   # Git repository
├── .gitignore              # Git ignore rules
├── README.md               # This file
├── CLAUDE.md               # Claude Code documentation
├── requirements.txt        # Python dependencies
├── autocoder/              # Complete source code (761 Python files)
│   ├── __init__.py
│   ├── auto_coder.py       # Main CLI entry
│   ├── chat_auto_coder.py  # Chat interface entry
│   ├── auto_coder_rag.py   # RAG mode entry
│   ├── agent/              # Agent system
│   ├── common/             # Common utilities
│   ├── rag/                # RAG system
│   ├── index/              # Code indexing
│   ├── sdk/                # SDK interface
│   ├── plugins/            # Plugin system
│   └── ...                 # Other modules
├── dist-info/              # Package metadata
│   ├── METADATA            # Package information
│   ├── entry_points.txt    # CLI entry points
│   └── LICENSE             # License file
└── original/               # Original files
    └── auto_coder-1.0.39-py3-none-any.whl
```

## 🔧 Configuration

### Environment Variables

Configure your API keys and settings:

```bash
# LLM API Keys
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export GOOGLE_API_KEY="your-google-key"

# Model configuration
export AUTOCODER_MODEL="gpt-4"
export AUTOCODER_BASE_URL="https://api.openai.com/v1"
```

### Product Modes

Auto-Coder supports two product modes:

- **lite mode**: Direct API calls without Ray cluster (default)
  - Uses `SimpleByzerLLM`
  - Simpler setup, suitable for local development

- **pro mode**: Ray cluster support for distributed computing
  - Uses `ByzerLLM`
  - Better performance for large-scale operations

## 📚 Documentation

- **[CLAUDE.md](CLAUDE.md)**: Detailed architecture and development guide for Claude Code
- **[dist-info/METADATA](dist-info/METADATA)**: Package metadata and dependencies
- **Official Docs**: https://uelng8wukz.feishu.cn/wiki/QIpkwpQo2iSdkwk9nP6cNSPlnPc

## 🛠️ Development

### Entry Points

The package provides multiple CLI entry points (defined in `dist-info/entry_points.txt`):

- `auto-coder` / `auto-coder.core` → `autocoder.auto_coder:main`
- `auto-coder.chat` / `chat-auto-coder` → `autocoder.chat_auto_coder:main`
- `auto-coder.run` / `auto-coder.cli` → `autocoder.sdk.cli:main`
- `auto-coder.rag` → `autocoder.auto_coder_rag:main`

### Modifying Source Code

Since you're running from source:

1. Edit any `.py` file in the `autocoder/` directory
2. Changes take effect immediately when you run the code again
3. No need to rebuild or reinstall

### Adding Features

1. Create new modules in `autocoder/` directory
2. Import and use them in existing code
3. Update `requirements.txt` if adding new dependencies

## 🐛 Troubleshooting

### Common Issues

1. **Import errors**: Make sure you're in the project root directory
2. **Missing dependencies**: Run `pip install -r requirements.txt`
3. **Python version**: Ensure you're using Python 3.10-3.12
4. **Permission issues**: Use virtual environment

### Logs

Logs are stored in:
```
.auto-coder/logs/auto-coder.log
```

## 📞 Contact

- **Repository Owner**: superfm831010@gmail.com
- **Original Project**: https://github.com/allwefantasy/auto-coder

## 📄 License

This software is proprietary and subject to commercial use restrictions. See [dist-info/LICENSE](dist-info/LICENSE) for details.

**Copyright (c) 2024 auto-coder Project Owner. All Rights Reserved.**

---

**Note**: This is a private repository for secondary development purposes. Do not distribute or share without proper authorization.
