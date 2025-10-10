# Auto-Coder 二次开发文档

## 项目信息

- **原始项目**: auto-coder v1.0.39
- **项目类型**: 从 wheel 包解压的源代码
- **开发版本**: 1.0.39.dev
- **Python 要求**: 3.10 - 3.12

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
    source "$VENV_DIR/bin/activate"
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
