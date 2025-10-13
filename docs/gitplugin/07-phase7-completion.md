# Phase 7: 命令补全增强

## 🎯 阶段目标

实现智能命令补全，提升用户体验。

## 📋 前置条件

- ✅ Phase 1-6 已完成
- ✅ 熟悉插件的补全机制

## 🔧 实施步骤

### 步骤 1: 扩展静态补全

修改 `get_completions` 方法：

```python
def get_completions(self) -> Dict[str, List[str]]:
    """Get completions provided by this plugin."""
    completions = {
        # 现有的 git 补全
        "/git": ["/status", "/commit", "/branch", "/checkout", "/diff",
                 "/log", "/pull", "/push", "/reset",
                 "/github", "/gitlab", "/platform"],  # 新增

        # 现有的 reset 补全
        "/git /reset": ["hard", "soft", "mixed"],

        # 新增：GitHub 子命令补全
        "/git /github": ["/setup", "/list", "/modify", "/delete", "/test"],

        # 新增：GitLab 子命令补全
        "/git /gitlab": ["/setup", "/list", "/modify", "/delete", "/test"],

        # 新增：平台子命令补全
        "/git /platform": ["/switch", "/list"],

        # 新增：平台类型补全
        "/git /platform /switch": ["github", "gitlab"],
    }

    # 添加分支补全（现有逻辑保持不变）
    if self.git_available:
        try:
            branches = self._get_git_branches()
            completions["/git /checkout"] = branches
            # ... (现有代码保持不变) ...
        except Exception:
            pass

    return completions
```

### 步骤 2: 实现动态补全

添加 `dynamic_cmds` 类属性：

```python
class GitHelperPlugin(Plugin):
    """Git helper plugin for the Chat Auto Coder."""

    name = "git_helper"
    description = "Git helper plugin providing Git commands and status"
    version = "0.1.0"

    # 新增：需要动态补全的命令
    dynamic_cmds = [
        "/git /github /modify",
        "/git /github /delete",
        "/git /github /test",
        "/git /gitlab /modify",
        "/git /gitlab /delete",
        "/git /gitlab /test",
        "/git /platform /switch",
    ]
```

### 步骤 3: 实现动态补全方法

```python
def get_dynamic_completions(
    self, command: str, current_input: str
) -> List[Tuple[str, str]]:
    """Get dynamic completions based on the current command context.

    Args:
        command: The base command (e.g., "/git /github /modify")
        current_input: The full current input

    Returns:
        A list of tuples containing (completion_text, display_text)
    """
    completions = []

    # GitHub 配置名补全
    if command in ["/git /github /modify", "/git /github /delete", "/git /github /test"]:
        configs = self.platform_manager.list_configs("github")
        for config in configs:
            display = f"{config.name} ({config.base_url})"
            completions.append((config.name, display))

    # GitLab 配置名补全
    elif command in ["/git /gitlab /modify", "/git /gitlab /delete", "/git /gitlab /test"]:
        configs = self.platform_manager.list_configs("gitlab")
        for config in configs:
            display = f"{config.name} ({config.base_url})"
            completions.append((config.name, display))

    # 平台切换补全
    elif command == "/git /platform /switch":
        # 解析当前输入，判断是否已输入平台类型
        parts = current_input.split()

        if len(parts) <= 3:
            # 还没输入平台类型，补全平台
            completions = [
                ("github", "GitHub"),
                ("gitlab", "GitLab"),
            ]
        else:
            # 已输入平台类型，补全配置名
            platform = parts[3] if len(parts) > 3 else ""

            if platform in ["github", "gitlab"]:
                configs = self.platform_manager.list_configs(platform)
                for config in configs:
                    # 标记当前激活的配置
                    current = ""
                    if (self.platform_manager.current_platform == platform and
                        self.platform_manager.current_config.get(platform) == config.name):
                        current = " ✓"

                    display = f"{config.name}{current} ({config.base_url})"
                    completions.append((config.name, display))

    return completions
```

---

## 🧪 测试要点

### 静态补全测试

1. **主命令补全**
   - 输入：`/git /`
   - 按 Tab
   - 预期：显示所有子命令，包括 `/github`、`/gitlab`、`/platform`

2. **GitHub 子命令补全**
   - 输入：`/git /github /`
   - 按 Tab
   - 预期：显示 `/setup`, `/list`, `/modify`, `/delete`, `/test`

3. **平台切换补全**
   - 输入：`/git /platform /switch `
   - 按 Tab
   - 预期：显示 `github`, `gitlab`

### 动态补全测试

1. **GitHub 配置名补全**
   - 先添加几个 GitHub 配置
   - 输入：`/git /github /modify `
   - 按 Tab
   - 预期：显示所有 GitHub 配置名和地址

2. **GitLab 配置名补全**
   - 先添加几个 GitLab 配置
   - 输入：`/git /gitlab /test `
   - 按 Tab
   - 预期：显示所有 GitLab 配置名

3. **平台切换两级补全**

   a. 第一级（平台类型）：
   - 输入：`/git /platform /switch `
   - 按 Tab
   - 预期：显示 `github`, `gitlab`

   b. 第二级（配置名）：
   - 输入：`/git /platform /switch github `
   - 按 Tab
   - 预期：显示所有 GitHub 配置，当前激活的有 ✓ 标记

4. **智能过滤测试**
   - 输入：`/git /github /modify per`
   - 按 Tab
   - 预期：只显示以 "per" 开头的配置名

---

## ✅ 完成标志

- [x] 静态补全覆盖所有新命令
- [x] 动态补全可以补全配置名
- [x] 平台切换支持两级补全
- [x] 当前激活的配置有标记
- [x] 补全选项显示有用信息（地址、状态等）

---

## 📝 提交代码

```bash
git add autocoder/plugins/git_helper_plugin.py
git commit -m "feat(git-plugin): 实现命令补全增强

- 添加静态补全：GitHub/GitLab/Platform 命令
- 实现动态补全：配置名智能补全
- 平台切换支持两级补全
- 显示配置详情和当前状态
- 提升用户体验
"
```

---

## 🎉 Phase 7 完成！

所有核心功能已实现！

➡️ **下一步**: 阅读 `08-testing-guide.md`，进行全面测试
