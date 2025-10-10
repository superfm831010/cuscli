# Auto-Coder 二次开发快速指南

> 基于 auto-coder v1.0.39 的二次开发环境

## 🚀 快速开始

### 一键设置开发环境

```bash
# 直接运行设置脚本（会自动创建虚拟环境）
./dev-setup.sh
```

完成！脚本会自动创建 `.venv/` 虚拟环境并完成安装。

### 后续使用

```bash
# 激活虚拟环境
source .venv/bin/activate

# 现在可以直接使用命令
auto-coder.chat
```

### 手动设置

```bash
# 激活虚拟环境
conda activate autocoder-dev

# 安装为可编辑模式
pip install -e .
```

## ✨ 开发优势

使用 `pip install -e .` (editable install) 的好处：

- ✅ **即改即用**: 修改代码后立即生效，无需重新安装
- ✅ **保留源码**: 在 `autocoder/` 目录直接编辑源代码
- ✅ **快速调试**: 可以添加 print、断点等调试手段
- ✅ **完整功能**: 所有命令行工具正常可用

## 📝 开发流程

```bash
# 1. 修改代码
vim autocoder/chat_auto_coder.py

# 2. 直接测试（无需重新安装！）
auto-coder.chat

# 3. 查看日志
tail -f .auto-coder/logs/auto-coder.log

# 4. 提交修改
git add .
git commit -m "修改说明"
```

## 🔧 可用命令

安装后，以下命令都可以直接使用：

```bash
auto-coder              # 主CLI
auto-coder.chat         # 聊天模式（推荐）
auto-coder.run          # SDK CLI
auto-coder.rag          # RAG模式
chat-auto-coder         # 聊天模式别名
```

### 🌏 语言设置

**默认中文界面** - 无需任何配置，直接启动即为中文：
```bash
auto-coder.chat  # 默认中文界面
```

如需切换到英文界面：
```bash
AUTO_CODER_LANG=en auto-coder.chat
```

或切换到其他语言：
```bash
AUTO_CODER_LANG=ja auto-coder.chat  # 日文
AUTO_CODER_LANG=ru auto-coder.chat  # 俄文
```

## 📚 文档

详细开发文档请查看: [docs/development.md](docs/development.md)

包含：
- 完整的环境搭建说明
- 开发工作流和最佳实践
- 常见问题解决方案
- 二次开发记录模板

## 🎯 核心文件

- `autocoder/auto_coder.py` - 主入口
- `autocoder/chat_auto_coder.py` - 聊天界面
- `autocoder/sdk/cli.py` - SDK CLI
- `setup.py` - 安装配置
- `requirements.txt` - 依赖列表

## ⚠️ 注意事项

1. **必须在虚拟环境中开发** - 避免污染系统 Python 环境
2. **重要修改需记录** - 在 `docs/development.md` 中记录重要变更
3. **测试后再提交** - 确保基本功能正常工作

## 🐛 常见问题

### 修改代码后没有生效？

```bash
# 重新安装开发模式
pip uninstall auto-coder
pip install -e .
```

### 命令找不到？

```bash
# 检查虚拟环境
which python
which auto-coder

# 重新激活环境
conda activate autocoder-dev
```

## 📞 获取帮助

- 查看详细文档: `docs/development.md`
- 查看原项目文档: [飞书文档](https://uelng8wukz.feishu.cn/wiki/QIpkwpQo2iSdkwk9nP6cNSPlnPc)
- 项目配置说明: `CLAUDE.md`

---

**License**: 专有软件许可协议（详见 `dist-info/LICENSE`）
