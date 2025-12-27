# Auto-Coder 2.0.2 → 2.0.32 升级合并方案

> **创建日期**: 2025-12-27
> **状态**: 待执行
> **用户决策**: 不添加新版 git_helper_plugin.py，仅保留二开 git_platform_plugin.py

---

## 一、分析结论

### 1.1 Whl 文件分析
- **auto_coder-2.0.32-py3-none-any.whl** 包含完整源代码（815个文件）
- 版本信息：`__version__ = "2.0.32"`
- 与当前版本（基于2.0.2）相差约30个版本更新

### 1.2 版本对比
| 项目 | 当前版本 | 目标版本 |
|------|---------|---------|
| cuscli | 1.1.5 | 1.2.0 |
| 基于 auto-coder | 2.0.2 | 2.0.32 |

---

## 二、新增功能模块

### 2.1 新增目录/模块
| 模块 | 说明 |
|------|------|
| `autocoder/common/skills/` | 技能管理器 |
| `autocoder/chat/` | 命令处理模块（conf_command, models_command, rules_command） |

### 2.2 新增插件
| 文件 | 功能 | 是否采用 |
|------|------|---------|
| `plugins/git_helper_plugin.py` | Git 命令插件 | **不采用** |
| `plugins/token_helper_plugin.py` | Token 统计插件 | 采用 |

### 2.3 新增公共模块
- `common/async_prompt.py` - 异步提示
- `common/core_config/merge_utils.py` - 配置合并工具
- 新增国际化消息文件

---

## 三、二开特有模块（必须保留）

| 模块路径 | 说明 |
|---------|------|
| `autocoder/checker/` (12文件) | 代码审核系统核心 |
| `plugins/code_checker_plugin.py` | 代码检查插件（141KB） |
| `plugins/customs_rules_plugin.py` | 自定义规则插件 |
| `plugins/git_platform_plugin.py` | Git 平台插件 |
| `common/terminal_compat.py` | 终端兼容性工具 |
| `common/git_platform_config.py` | Git 平台配置 |
| `common/llm_error_handler.py` | LLM 错误处理 |
| `common/llms/connection_test.py` | 连接测试 |
| `common/llms/guided_setup.py` | 引导设置 |

---

## 四、合并实施步骤

### 步骤 1: 备份和准备
```bash
mkdir -p .upgrade-backup/2.0.32-$(date +%Y%m%d)/custom
cp -r autocoder/checker .upgrade-backup/2.0.32-$(date +%Y%m%d)/custom/
cp autocoder/plugins/code_checker_plugin.py .upgrade-backup/2.0.32-$(date +%Y%m%d)/custom/
cp autocoder/plugins/customs_rules_plugin.py .upgrade-backup/2.0.32-$(date +%Y%m%d)/custom/
cp autocoder/plugins/git_platform_plugin.py .upgrade-backup/2.0.32-$(date +%Y%m%d)/custom/
cp autocoder/common/terminal_compat.py .upgrade-backup/2.0.32-$(date +%Y%m%d)/custom/

# 解压新版
mkdir -p /tmp/auto-coder-2.0.32
unzip auto_coder-2.0.32-py3-none-any.whl -d /tmp/auto-coder-2.0.32
```

### 步骤 2: 批量覆盖模块
直接覆盖无二开修改的模块：
- `agent/`、`commands/`、`db/`、`dispacher/`
- `events/`、`index/`、`rag/`、`sdk/`
- `utils/`、`workflow_agents/`、`terminal_v3/`

### 步骤 3: 添加新增模块
- 复制 `chat/`、`skills/` 目录
- 复制 `token_helper_plugin.py`（不复制 git_helper_plugin.py）
- 复制 `async_prompt.py`、`merge_utils.py`

### 步骤 4: 手动合并关键文件

| 文件 | 合并策略 |
|-----|---------|
| `plugins/__init__.py` | 保留二开的 `get_help_text()` 方法 |
| `terminal/app.py` | 保留 `print_warning_box()` 函数 |
| `common/__init__.py` | 合并新字段 `model_file`、`enable_agentic_reasoning_content` |
| `terminal/command_processor.py` | 采用新版 |

### 步骤 5: 恢复二开文件
从备份目录恢复所有二开特有文件

### 步骤 6: 更新版本号
```python
# autocoder/version.py
__version__ = "1.2.0"
__base_version__ = "2.0.32"
```

### 步骤 7: 测试验证
- 基础功能：`/help`、`/plugins`、`/models`
- 二开功能：`/check /file`、`/git /github`
- 跨平台：Windows + Linux 测试

---

## 五、回滚方案

```bash
# Git 回滚
git checkout main

# 或文件恢复
cp -r .upgrade-backup/2.0.32-*/autocoder .
```
