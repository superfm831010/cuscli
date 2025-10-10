# Auto-Coder 二次开发文档

## 项目信息

- **原始项目**: auto-coder v1.0.39
- **项目类型**: 从 wheel 包解压的源代码
- **开发版本**: 1.0.39.dev
- **Python 要求**: 3.10 - 3.12

## 语言设置

Auto-Coder 支持多语言界面（中文、英文等），**默认显示中文界面**。

### 默认行为

直接启动即为中文界面（无需任何配置）：
```bash
auto-coder.chat  # 默认中文界面
```

### 切换到英文界面

**方法1：使用自定义环境变量（推荐）**
```bash
AUTO_CODER_LANG=en auto-coder.chat
```

**方法2：设置 LANG 环境变量**
```bash
LANG=zh_CN.UTF-8 auto-coder.chat  # 注意：en_US 会被忽略，默认显示中文
```

**方法3：永久设置自定义语言**
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
export AUTO_CODER_LANG=en
```

### 技术说明

- 语言检测代码位于：`autocoder/common/international/message_manager.py:23`
- 检测优先级：
  1. `AUTO_CODER_LANG` 环境变量（最高优先级）
  2. `LANG` 环境变量（仅支持 zh/ja/ar/ru，忽略 en）
  3. 默认：zh（中文）
- 支持的语言：en（英文）、zh（中文）、ja（日文）、ar（阿拉伯文）、ru（俄文）
- **英文 locale（如 en_US）会被忽略，默认显示中文**（二次开发版本的定制行为）

## 开发环境搭建

### 1. 快速开始（推荐）

使用提供的自动化脚本快速搭建开发环境：

```bash
# 克隆/进入项目目录
cd /projects/cuscli

# 运行设置脚本（会自动创建虚拟环境）
./dev-setup.sh
```

脚本会自动完成以下操作：
- ✅ 检测 Python 版本
- ✅ 自动创建虚拟环境（`.venv/`）
- ✅ 激活虚拟环境
- ✅ 安装开发模式

**后续使用时激活环境：**
```bash
source .venv/bin/activate
```

### 2. 手动设置

如果自动化脚本无法使用，可以手动执行以下步骤：

#### 2.1 创建虚拟环境

**使用 Conda（推荐）：**

```bash
conda create --name autocoder-dev python=3.10
conda activate autocoder-dev
```

**使用 venv：**

```bash
python -m venv autocoder-dev
source autocoder-dev/bin/activate  # Linux/macOS
# autocoder-dev\Scripts\activate  # Windows
```

#### 2.2 卸载已有版本（如果存在）

```bash
pip uninstall -y auto-coder
```

#### 2.3 安装开发模式

```bash
# 进入项目根目录
cd /projects/cuscli

# 以可编辑模式安装
pip install -e .
```

这将创建一个指向源代码的"符号链接"，之后修改源代码会立即生效，无需重新安装。

#### 2.4 验证安装

```bash
# 检查命令是否可用
which auto-coder
auto-coder --version

# 测试运行
auto-coder.chat --help
```

## 开发工作流

### 日常开发流程

1. **激活开发环境**
   ```bash
   conda activate autocoder-dev
   # 或
   source autocoder-dev/bin/activate
   ```

2. **修改代码**
   - 源代码位于 `autocoder/` 目录
   - 可以使用任何编辑器或 IDE（推荐 VSCode、PyCharm）

3. **测试修改**
   ```bash
   # 直接运行命令测试
   auto-coder.run -p "测试输入"

   # 或启动聊天模式测试
   auto-coder.chat

   # 查看日志
   tail -f .auto-coder/logs/auto-coder.log
   ```

4. **调试**
   - 可以直接在代码中添加 `print()` 或使用 `pdb` 调试器
   - 日志文件位置: `.auto-coder/logs/auto-coder.log`

### 重要文件和目录

```
/projects/cuscli/
├── autocoder/              # 主要源代码目录
│   ├── auto_coder.py       # 主入口点
│   ├── chat_auto_coder.py  # 聊天界面
│   ├── sdk/cli.py          # SDK CLI
│   ├── agent/              # Agent系统
│   ├── common/             # 公共工具
│   ├── rag/                # RAG系统
│   └── plugins/            # 插件系统
├── setup.py                # 安装配置（新建）
├── requirements.txt        # 依赖列表
├── MANIFEST.in             # 资源文件配置（新建）
├── dev-setup.sh            # 开发环境设置脚本（新建）
├── CLAUDE.md               # Claude Code 项目说明
└── docs/                   # 文档目录（新建）
    └── development.md      # 本文档
```

### 入口点说明

所有命令行入口点配置在 `setup.py` 中：

| 命令 | 入口函数 | 说明 |
|------|---------|------|
| `auto-coder` | autocoder.auto_coder:main | 主CLI入口 |
| `auto-coder.chat` | autocoder.chat_auto_coder:main | 交互式聊天界面 |
| `auto-coder.run` | autocoder.sdk.cli:main | SDK CLI接口 |
| `auto-coder.rag` | autocoder.auto_coder_rag:main | RAG模式 |
| `chat-auto-coder` | autocoder.chat_auto_coder:main | 聊天模式别名 |

### 常见开发场景

#### 场景1：修改聊天界面

```bash
# 1. 编辑文件
vim autocoder/chat_auto_coder.py

# 2. 直接测试（无需重新安装）
auto-coder.chat

# 3. 查看日志
tail -f .auto-coder/logs/auto-coder.log
```

#### 场景2：添加新功能

```bash
# 1. 在合适的目录创建新文件
vim autocoder/common/my_new_feature.py

# 2. 在相关入口点导入并使用
vim autocoder/auto_coder.py

# 3. 测试
auto-coder --help  # 查看是否有新选项
```

#### 场景3：修改依赖

```bash
# 1. 编辑 requirements.txt
vim requirements.txt

# 2. 重新安装依赖
pip install -e .

# 或只更新特定依赖
pip install -U package-name
```

#### 场景4：调试问题

```python
# 在代码中添加断点
import pdb; pdb.set_trace()

# 或使用 IPython 调试
from IPython import embed; embed()
```

## 开发注意事项

### 1. 代码修改规范

- **保留原有功能**: 尽量不破坏原有功能
- **添加注释**: 新增代码要添加中文注释说明
- **记录变更**: 重要修改记录到本文档

### 2. 测试建议

- 修改后先进行基本功能测试
- 涉及核心功能的修改要进行更全面的测试
- 建议创建测试用例（可选）

### 3. 版本管理

当前使用 Git 进行版本控制：

```bash
# 查看修改
git status
git diff

# 提交修改
git add .
git commit -m "描述修改内容"

# 查看历史
git log
```

### 4. 日志和调试

日志配置在 `autocoder/__init__.py` 中：

- 默认日志位置: `.auto-coder/logs/auto-coder.log`
- 可以通过环境变量或配置文件调整日志级别

## 常见问题

### Q1: 修改代码后没有生效？

**解决方案:**
```bash
# 1. 确认安装模式是否正确
pip show auto-coder | grep Location

# 2. 重新安装开发模式
pip uninstall auto-coder
pip install -e .

# 3. 重启 Python 解释器或重新运行命令
```

### Q2: 导入错误或模块找不到？

**解决方案:**
```bash
# 1. 检查虚拟环境
echo $VIRTUAL_ENV
echo $CONDA_DEFAULT_ENV

# 2. 重新激活环境
conda activate autocoder-dev

# 3. 检查 Python 路径
python3 -c "import sys; print('\n'.join(sys.path))"
```

### Q5: dev-setup.sh 脚本运行出错？

**常见错误:**
- `python: command not found` - 系统中没有 `python` 命令
- `Illegal number` - 版本检测失败

**解决方案:**
```bash
# 1. 确保系统中有 python3
which python3
python3 --version

# 2. 如果脚本仍有问题，手动执行安装
pip install -e .

# 3. 检查脚本使用的 shell
ls -l /bin/sh  # 确认系统默认 shell

# 4. 如果使用 dash 等非 bash shell，显式使用 bash 运行
bash dev-setup.sh
```

### Q3: 依赖冲突？

**解决方案:**
```bash
# 1. 重新创建干净的虚拟环境
conda deactivate
conda remove --name autocoder-dev --all
conda create --name autocoder-dev python=3.10
conda activate autocoder-dev

# 2. 重新安装
pip install -e .
```

### Q4: 如何回退到原始版本？

**解决方案:**
```bash
# 使用 Git 回退
git log  # 找到原始提交
git checkout <commit-hash>

# 或重新从 wheel 包解压
```

## 二次开发记录

### 2025-10-10: 初始化开发环境

**修改内容:**
1. 创建 `setup.py` - 支持开发模式安装
2. 创建 `dev-setup.sh` - 自动化环境设置脚本
3. 创建 `MANIFEST.in` - 资源文件配置
4. 创建本开发文档

**目的:**
- 实现无需打包即可测试的开发流程
- 提高开发效率
- 方便快速迭代和调试

**影响范围:**
- 仅影响开发环境设置
- 不改变原有代码逻辑
- 不影响最终部署包的功能

---

### 2025-10-10: 修复开发环境设置脚本的兼容性问题

**修改内容:**
修改文件 `dev-setup.sh`，解决以下问题：
1. 支持 `python3` 命令而不仅仅是 `python`（系统中没有 `python` 命令）
2. 将 `echo -e` 替换为 `printf` 以提高跨 shell 兼容性（避免在 dash 等 shell 中出错）
3. 添加 Python 命令检测逻辑，优先使用 `python3`，其次 `python`
4. 改进错误提示信息

**修改原因:**
- 用户运行脚本时遇到版本检测错误：`Illegal number: 20:`
- 原因是系统中只有 `python3` 命令，没有 `python` 命令
- `echo -e` 在某些 shell（如 dash）中不被支持或行为不同

**技术细节:**
```bash
# 修改前
python_version=$(python --version 2>&1 | awk '{print $2}')

# 修改后
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    printf "${RED}✗ 未找到 Python 命令${NC}\n"
    exit 1
fi
python_version=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
```

**影响范围:**
- 仅影响 `dev-setup.sh` 脚本
- 提高了脚本在不同 Linux 发行版和 shell 环境下的兼容性
- 不影响其他文件和功能

**测试情况:**
- 在 Linux 系统（只有 python3 命令）上测试通过
- 脚本能正确检测 Python 3.10.12 版本

---

### 2025-10-10: 增强脚本自动化 - 自动创建虚拟环境

**修改内容:**
1. 修改 `dev-setup.sh`，增加自动创建虚拟环境功能
2. 当检测到未激活虚拟环境时，自动创建 `.venv` 目录
3. 自动激活新创建的虚拟环境并继续安装
4. 添加虚拟环境使用提示信息
5. 更新 `.gitignore`，排除 `.venv/` 目录

**修改原因:**
- 用户希望脚本完全自动化，无需手动创建虚拟环境
- 简化开发环境搭建流程，提升用户体验
- 避免在系统环境中安装包导致的污染

**技术细节:**
```bash
# 自动创建虚拟环境
if [ -z "$VIRTUAL_ENV" ] && [ -z "$CONDA_DEFAULT_ENV" ]; then
    VENV_DIR=".venv"
    if [ ! -d "$VENV_DIR" ]; then
        $PYTHON_CMD -m venv "$VENV_DIR"
    fi
    . "$VENV_DIR/bin/activate"  # 使用 . 代替 source（POSIX 兼容）
fi
```

**影响范围:**
- 仅影响 `dev-setup.sh` 脚本和 `.gitignore`
- 虚拟环境统一创建在项目根目录的 `.venv/` 下
- 不影响已有的 Conda 环境使用方式

**使用说明:**
首次运行脚本：
```bash
./dev-setup.sh  # 自动创建并激活虚拟环境
```

后续开发时激活环境：
```bash
source .venv/bin/activate
# 或使用 POSIX 兼容写法
. .venv/bin/activate
```

或添加快捷别名：
```bash
alias autocoder-dev='cd /projects/cuscli && source .venv/bin/activate'
```

**测试情况:**
- 脚本能自动创建虚拟环境
- 能够在虚拟环境中成功安装开发模式
- 虚拟环境激活和命令可用性验证通过

---

### 2025-10-10: 修复 source 命令的 Shell 兼容性问题

**修改内容:**
修改 `dev-setup.sh` 中的 `source` 命令为 `.` 命令

**问题描述:**
用户运行脚本时遇到错误：
```
dev-setup.sh: 64: source: not found
```

**原因分析:**
- 系统 `/bin/sh` 链接到 `dash` 而不是 `bash`
- `source` 是 bash 的内置命令，不是 POSIX 标准
- `dash` 等 POSIX shell 不支持 `source` 命令
- POSIX 标准使用 `.` 命令来实现相同功能

**技术修改:**
```bash
# 修改前
source "$VENV_DIR/bin/activate"

# 修改后（POSIX 兼容）
. "$VENV_DIR/bin/activate"
```

**影响范围:**
- 仅影响 `dev-setup.sh` 脚本的虚拟环境激活部分
- 提高脚本在不同 shell 环境下的兼容性
- 功能完全相同，只是使用 POSIX 标准写法

**兼容性说明:**
- `.` 命令在所有 POSIX 兼容 shell 中都可用（bash、dash、sh、zsh 等）
- `source` 命令仅在 bash、zsh 等扩展 shell 中可用
- 使用 `.` 提高了脚本的可移植性

**测试情况:**
- 在 dash shell 环境下测试通过
- 虚拟环境创建和激活成功

---

### 2025-10-10: 添加中文界面支持

**修改内容:**
1. 创建 `auto-coder-zh.sh` - 中文界面启动脚本
2. 更新开发文档，添加语言设置说明
3. 更新 DEV-README.md，添加中文界面使用方法

**问题描述:**
用户反馈开发模式安装后，启动的界面是英文的，而直接安装的版本是中文界面

**原因分析:**
- Auto-Coder 使用 `locale.getdefaultlocale()` 检测系统语言
- 系统的 `LANG` 环境变量设置为 `en_US.UTF-8`
- 代码位置：`autocoder/common/international/message_manager.py:31`
- 系统自动根据 locale 的前两个字符判断语言（如 zh_CN -> zh）

**解决方案:**
提供三种方式切换到中文界面：

1. **使用中文启动脚本（最简单）**
```bash
./auto-coder-zh.sh
```

2. **临时设置环境变量**
```bash
LANG=zh_CN.UTF-8 auto-coder.chat
```

3. **永久设置（修改 ~/.bashrc 或 ~/.zshrc）**
```bash
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8
```

**技术细节:**
- 支持的语言：en、zh、ja、ar、ru
- 不支持的语言自动回退到英文
- 语言配置在 `autocoder/lang.py` 中定义
- 消息文件在 `autocoder/common/international/messages/` 目录

**影响范围:**
- 新增中文启动脚本
- 不影响现有功能
- 提供更好的中文用户体验

**测试情况:**
- 使用中文启动脚本可正常显示中文界面
- 环境变量设置方法测试通过

---

### 2025-10-10: 修改默认语言为中文（第二版 - 忽略英文 locale）

**修改内容:**
重新设计语言检测逻辑，忽略英文 locale，强制默认中文，并支持通过环境变量切换

**修改原因:**
- 第一版修改存在逻辑问题：系统 LANG=en_US 时仍然返回 en
- 用户希望在开发模式下直接启动就是中文，无需任何设置
- 需要保留切换到其他语言的能力

**技术修改:**
```python
def get_system_language(self) -> str:
    """优先级：AUTO_CODER_LANG > LANG(非en) > 默认zh"""
    try:
        import os

        # 1. 检查自定义环境变量（最高优先级）
        custom_lang = os.environ.get('AUTO_CODER_LANG', '').strip().lower()
        if custom_lang in ['en', 'zh', 'ja', 'ar', 'ru']:
            return custom_lang

        # 2. 检查 LANG 环境变量（忽略英文）
        lang_env = os.environ.get('LANG', '')
        if lang_env:
            detected_lang = lang_env.split('.')[0].split('_')[0].lower()
            # 只接受中文和其他非英文语言
            if detected_lang in ['zh', 'ja', 'ar', 'ru']:
                return detected_lang

        # 3. 默认中文（忽略 en_US 等英文 locale）
        return "zh"
    except:
        return "zh"
```

**行为变化:**
| 场景 | 修改前 | 修改后（第二版） |
|------|--------|------------------|
| 系统 `LANG=en_US.UTF-8` | 显示英文 | 显示中文 ✓ |
| 系统 `LANG=zh_CN.UTF-8` | 显示中文 | 显示中文 ✓ |
| `AUTO_CODER_LANG=en` | 不支持 | 显示英文 ✓ |
| 未设置任何环境变量 | 显示中文 | 显示中文 ✓ |

**使用说明:**

默认中文（不管系统 LANG 是什么）：
```bash
auto-coder.chat  # 始终显示中文
```

切换到英文：
```bash
AUTO_CODER_LANG=en auto-coder.chat
```

切换到其他语言：
```bash
AUTO_CODER_LANG=ja auto-coder.chat  # 日文
AUTO_CODER_LANG=ru auto-coder.chat  # 俄文
```

**影响范围:**
- 彻底忽略英文 locale（en_US、en_GB 等）
- 通过 `AUTO_CODER_LANG` 环境变量支持语言切换
- 所有入口点生效
- 开发模式下修改代码立即生效（需要清理缓存）

**问题修复:**
- ✓ 解决了第一版中 LANG=en_US 仍显示英文的问题
- ✓ 开发模式下修改代码后需要清理 Python 缓存：`find autocoder -name "*.pyc" -delete`
- ✓ 提供了明确的语言切换机制

**测试情况:**
- 在 LANG=en_US.UTF-8 的系统上启动，显示中文 ✓
- AUTO_CODER_LANG=en 可以切换到英文 ✓
- 修改代码后清理缓存，立即生效 ✓

---

### 2025-10-10: 修改启动界面 ASCII 艺术字为 CUS-CLI

**修改内容:**
1. 修改文件 `autocoder/chat_auto_coder.py` 第 1137-1143 行
2. 将原始 "Chat Auto Coder" ASCII 艺术字替换为 "CUS-CLI"
3. 使用 Unicode 方块字符（`█`、`╔`、`╗` 等）创建新艺术字
4. 保留绿色配色主题（`\033[1;32m`）和版本号显示

**修改原因:**
- 项目需要定制化的品牌标识
- 用户希望启动界面更加个性化，体现 "CUS-CLI" 品牌
- 选择方块字符风格的粗连字符版本（版本3），更加醒目

**技术细节:**
```python
# 修改前（原始艺术字）
  ____ _           _          _         _               ____          _
 / ___| |__   __ _| |_       / \\  _   _| |_ ___        / ___|___   __| | ___ _ __
 | |   | '_ \\ / _` | __|____ / _ \\| | | | __/ _ \\ _____| |   / _ \\ / _` |/ _ \\ '__|
 | |___| | | | (_| | ||_____/ ___ \\ |_| | || (_) |_____| |__| (_) | (_| |  __/ |
 \\____|_| |_|\\__,_|\\__|   /_/   \\_\\__,_|\\__\\___/       \\____\\___/ \\__,_|\\___|_|

# 修改后（CUS-CLI 艺术字）
  ██████╗██╗   ██╗███████╗          ██████╗██╗     ██╗
 ██╔════╝██║   ██║██╔════╝         ██╔════╝██║     ██║
 ██║     ██║   ██║███████╗ ██████  ██║     ██║     ██║
 ██║     ██║   ██║╚════██║         ██║     ██║     ██║
 ╚██████╗╚██████╔╝███████║         ╚██████╗███████╗██║
  ╚═════╝ ╚═════╝ ╚══════╝          ╚═════╝╚══════╝╚═╝
```

**影响范围:**
- 仅影响启动界面的视觉显示
- 不影响任何功能逻辑
- 保持原有的版本号显示和颜色主题
- 用户启动 `auto-coder.chat` 时会看到新的 "CUS-CLI" 标识

**Git 提交:**
- 提交哈希: 8602366
- 提交信息: "修改启动界面 ASCII 艺术字为 CUS-CLI"

**测试情况:**
- 艺术字显示清晰，"CUS-CLI" 易于识别
- 中间的粗连字符（`██████`）效果明显
- 绿色配色和版本号正常显示
- 不影响后续的帮助信息和插件加载提示

---

### 2025-10-10: 修改启动界面欢迎提示文字

**修改内容:**
1. 修改文件 `autocoder/common/international/messages/chat_auto_coder_messages.py` 第 1493 行
2. 将启动提示从"输入 /help 查看可用命令。"改为"欢迎使用中国海关智能编码助手，输入 /help 查看可用命令。"
3. 修改的是 `type_help_to_see_commands` 消息键的中文（zh）翻译

**修改原因:**
- 需要在启动界面添加欢迎语，体现"中国海关智能编码助手"的品牌标识
- 提升用户体验，让用户一启动就知道这是定制化的海关智能助手
- 与 CUS-CLI 品牌形象保持一致

**技术细节:**
```python
# 修改前
"type_help_to_see_commands": {
    "en": "Type /help to see available commands.",
    "zh": "输入 /help 查看可用命令。",
    ...
}

# 修改后
"type_help_to_see_commands": {
    "en": "Type /help to see available commands.",
    "zh": "欢迎使用中国海关智能编码助手，输入 /help 查看可用命令。",
    ...
}
```

**使用位置:**
- `chat_auto_coder.py:1144` - 主聊天界面启动时
- `terminal/app.py:333` - 终端应用启动时

**影响范围:**
- 仅影响启动界面的中文提示文字
- 英文和其他语言界面不受影响
- 不影响任何功能逻辑
- 用户启动 `auto-coder.chat` 时会看到新的欢迎提示

**测试情况:**
- 修改后启动界面会显示："欢迎使用中国海关智能编码助手，输入 /help 查看可用命令。"
- 保持蓝色配色显示（`\033[1;34m`）
- 不影响后续的插件加载和其他提示信息

---

### 2025-10-10: 添加 cuscli 主入口点命令

**修改内容:**
1. 修改 `setup.py` 第 54-68 行，在 `entry_points` 中添加新的入口点
2. 添加 `cuscli=autocoder.chat_auto_coder:main` 作为主要命令入口
3. 保留原有 `auto-coder.chat` 等入口点以保持向后兼容
4. 重新安装包使新入口点生效：`pip install -e .`

**修改原因:**
- 用户希望使用更简洁的 `cuscli` 命令启动聊天界面
- 将 `cuscli` 作为 CUS-CLI 品牌的主要命令入口点
- 与之前修改的 ASCII 艺术字和欢迎提示保持品牌一致性
- 简化用户使用体验，避免输入冗长的 `auto-coder.chat` 命令

**技术细节:**
```python
# setup.py 中的修改
entry_points={
    'console_scripts': [
        # CUS-CLI 主入口点（新增）
        'cuscli=autocoder.chat_auto_coder:main',
        # 原 auto-coder 入口点（保留以兼容旧脚本）
        'auto-coder=autocoder.auto_coder:main',
        'auto-coder.chat=autocoder.chat_auto_coder:main',
        ...
    ],
},
```

**影响范围:**
- 添加新的命令入口点 `cuscli`，不影响现有功能
- 保留所有原有入口点，完全向后兼容
- 用户可以使用 `cuscli` 或 `auto-coder.chat` 启动聊天界面
- 需要重新安装包才能生效：`pip install -e .`

**使用方式:**
```bash
# 新的主入口点（推荐）
cuscli

# 旧的入口点（仍然可用）
auto-coder.chat
chat-auto-coder
```

**测试情况:**
- `which cuscli` 返回 `/usr/local/bin/cuscli` ✓
- `cuscli --help` 正常显示帮助信息 ✓
- 命令入口点已正确安装并可用 ✓
- 保持与原有入口点相同的功能和参数支持 ✓

---

### 2025-10-10: 统一修改显示文本中的 auto-coder 为 cuscli

**修改内容:**
1. 修改聊天界面提示符（2处）：
   - `autocoder/chat_auto_coder.py:1171` - `"auto-coder.chat"` → `"cuscli.chat"`
   - `autocoder/terminal/app.py:365` - `"auto-coder.chat"` → `"cuscli.chat"`

2. 修改问答对话标题（4处）：
   - `autocoder/agent/base_agentic/tools/ask_followup_question_tool_resolver.py:51` - `"auto-coder.chat's Question"` → `"cuscli.chat's Question"`
   - `autocoder/agent/project_reader.py:186` - `"auto-coder.chat's Question"` → `"cuscli.chat's Question"`
   - `autocoder/commands/tools.py:137` - `"auto-coder.chat's Question"` → `"cuscli.chat's Question"`
   - `autocoder/common/v2/agent/agentic_edit_tools/ask_followup_question_tool_resolver.py:60` - `"auto-coder.chat's Question"` → `"cuscli.chat's Question"`

3. 修改AI系统提示和自我介绍（3处）：
   - `autocoder/agent/coder.py:845` - `"You are auto-coder"` → `"You are cuscli"`
   - `autocoder/commands/auto_command.py:131` - `"你是 auto-coder.chat 软件"` → `"你是 cuscli.chat 软件"`
   - `autocoder/commands/auto_command.py:1406` - `"你好，我是 auto-coder"` → `"你好，我是 cuscli"`

4. 修改提示词文档中的软件名称（2处）：
   - `autocoder/commands/auto_command.py:202` - `"auto-coder.chat 自动感知的一些文件列表"` → `"cuscli.chat 自动感知的一些文件列表"`
   - `autocoder/commands/auto_command.py:283` - `"是否根据需求动态修改auto-coder软件配置"` → `"是否根据需求动态修改cuscli软件配置"`

**修改原因:**
- 延续之前的品牌统一工作，将所有用户可见的显示文本中的 "auto-coder" 改为 "cuscli"
- 确保聊天界面、AI提示、对话框等所有显示元素与 CUS-CLI 品牌保持一致
- 提升用户体验的一致性

**技术说明:**
- **修改的内容**：仅修改用户可见的显示文本（UI提示符、对话框标题、AI自我介绍等）
- **未修改的内容**：
  - `.auto-coder/` 目录路径（配置目录名，属于代码逻辑）
  - `auto-coder.log` 等文件名（日志文件名）
  - `auto-coder.run` 等命令名（命令入口点）
  - 技术文档中关于 auto-coder YAML 系统的说明（技术原理说明）

**影响范围:**
- 影响所有与用户交互的界面显示文本
- 聊天界面提示符从 `coding@auto-coder.chat:~$ ` 变为 `coding@cuscli.chat:~$ `
- AI 系统提示和自我介绍统一为 "cuscli"
- 问答对话框标题统一为 "cuscli.chat's Question"
- 不影响任何代码逻辑和功能
- 不影响配置文件路径和日志文件名

**测试建议:**
- 启动聊天界面，验证提示符显示为 `coding@cuscli.chat:~$ `
- 触发 AI 提问功能，验证对话框标题显示为 "cuscli.chat's Question"
- 询问 AI "你是谁"，验证回答为 "你好，我是 cuscli"

---

### 2025-10-10: 完全移除官方文档链接

**修改内容:**
1. 删除 `autocoder/common/international/messages/chat_auto_coder_messages.py` 第 1009-1015 行
   - 移除整个 `official_doc` 国际化消息条目（包含所有语言版本）
2. 删除 `autocoder/chat_auto_coder.py` 第 173-174 行
   - 移除 `show_help()` 函数中显示官方文档链接的代码
3. 删除 `autocoder/terminal/help.py` 第 8-9 行
   - 移除 `show_help()` 函数中显示官方文档链接的代码

**修改原因:**
- 用户要求删除原始项目的官方文档链接（飞书文档）
- 作为二次开发项目，不再需要显示原始项目的官方文档
- 简化帮助信息界面

**技术细节:**
```python
# 删除的国际化消息条目
"official_doc": {
    "en": "Official Documentation: https://uelng8wukz.feishu.cn/wiki/NhPNwSRcWimKFIkQINIckloBncI",
    "zh": "官方文档: https://uelng8wukz.feishu.cn/wiki/NhPNwSRcWimKFIkQINIckloBncI",
    "ja": "公式ドキュメント: https://uelng8wukz.feishu.cn/wiki/NhPNwSRcWimKFIkQINIckloBncI",
    "ar": "الوثائق الرسمية: https://uelng8wukz.feishu.cn/wiki/NhPNwSRcWimKFIkQINIckloBncI",
    "ru": "Официальная документация: https://uelng8wukz.feishu.cn/wiki/NhPNwSRcWimKFIkQINIckloBncI"
}

# 删除的显示代码（两处相同）
print(f"\033[1m{get_message('official_doc')}\033[0m")
print()
```

**影响范围:**
- 启动帮助信息不再显示官方文档链接
- `/help` 命令显示的帮助信息也不再包含官方文档链接
- 不影响其他任何功能
- 已确认没有其他地方引用 `official_doc` 消息键

**测试情况:**
- 使用 `grep` 搜索确认所有 `official_doc` 引用已删除 ✓
- 删除后代码结构完整，不会出现引用错误 ✓

---

### 2025-10-10: 修改启动界面版本号和添加单位信息

**修改内容:**
1. 修改 `autocoder/version.py` 第 4 行
   - 将版本号从 `'1.0.39'` 改为 `'dev-0.1'`
2. 修改 `autocoder/chat_auto_coder.py` 第 1133-1142 行
   - 在启动界面 ASCII 艺术字的版本号下方添加一行
   - 显示文本："Produced by 黄埔海关科技处"
   - 保持相同的绿色样式和居中对齐

**修改原因:**
- 定制化版本号，标识这是开发版本（dev-0.1）
- 在启动界面添加单位标识，体现黄埔海关科技处的品牌
- 提升用户体验，让用户一眼看出这是定制化的海关版本

**技术细节:**
```python
# version.py 修改
# 修改前
__version__ = '1.0.39'

# 修改后
__version__ = 'dev-0.1'

# chat_auto_coder.py 修改（在 ASCII 艺术字末尾添加一行）
# 修改前
  ╚═════╝ ╚═════╝ ╚══════╝          ╚═════╝╚══════╝╚═╝
                                                   v{__version__}\033[0m"""

# 修改后
  ╚═════╝ ╚═════╝ ╚══════╝          ╚═════╝╚══════╝╚═╝
                                                   v{__version__}
                          Produced by 黄埔海关科技处\033[0m"""
```

**影响范围:**
- 启动界面显示的版本号变更为 dev-0.1
- 启动界面增加单位信息显示
- 不影响任何功能逻辑
- 所有使用 `__version__` 的地方（如 `--version` 参数）都会显示新版本号

**测试情况:**
- 启动 `cuscli` 命令，版本号显示为 `vdev-0.1` ✓
- 启动界面正确显示 "Produced by 黄埔海关科技处" ✓
- 单位信息居中对齐，样式与 ASCII 艺术字一致 ✓

---

## 后续开发记录模板

### YYYY-MM-DD: 修改标题

**修改内容:**
- 修改了哪些文件
- 添加了什么功能
- 修复了什么问题

**修改原因:**
- 为什么要做这个修改

**影响范围:**
- 这个修改影响了哪些模块
- 是否有兼容性问题

**测试情况:**
- 如何测试的
- 测试结果

---

## 参考资源

- [原始项目文档](https://uelng8wukz.feishu.cn/wiki/QIpkwpQo2iSdkwk9nP6cNSPlnPc)
- [项目说明文件](../CLAUDE.md)
- [依赖列表](../requirements.txt)
- [入口点配置](../dist-info/entry_points.txt)

## 联系和支持

如有问题或建议，请参考原项目文档或在项目仓库提 Issue。
