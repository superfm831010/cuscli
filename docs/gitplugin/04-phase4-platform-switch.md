# Phase 4: 平台切换功能实现

## 🎯 阶段目标

实现 GitHub 和 GitLab 之间的平台切换功能。

## 📋 前置条件

- ✅ Phase 1-3 已完成
- ✅ 至少配置了一个 GitHub 或 GitLab

## 🔧 实施步骤

### 步骤 1: 添加平台管理命令

在 `handle_git` 方法中添加路由：

```python
elif subcommand == "/platform":
    self.handle_platform(sub_args)
```

### 步骤 2: 实现平台命令处理

```python
def handle_platform(self, args: str) -> None:
    """
    处理 /git /platform 命令

    子命令：
    - (无) - 显示当前平台状态
    - /switch <platform> [config_name] - 切换平台
    - /list - 列出所有平台配置概览
    """
    args = args.strip()

    if not args:
        self._platform_status()
        return

    parts = args.split(maxsplit=2)
    subcmd = parts[0]

    if subcmd == "/switch":
        platform = parts[1] if len(parts) > 1 else ""
        config_name = parts[2] if len(parts) > 2 else ""
        self._platform_switch(platform, config_name)
    elif subcmd == "/list":
        self._platform_list()
    else:
        print(f"❌ 未知的子命令: {subcmd}")
        self._show_platform_help()
```

### 步骤 3: 实现平台状态显示

```python
def _platform_status(self) -> None:
    """显示当前平台状态"""
    from rich.console import Console
    from rich.panel import Panel

    console = Console()

    current_config = self.platform_manager.get_current_config()

    if not current_config:
        console.print("\n[yellow]⚠️  未配置任何平台[/yellow]\n")
        console.print("请先配置平台：")
        console.print("  [cyan]/git /github /setup[/cyan]  - 配置 GitHub")
        console.print("  [cyan]/git /gitlab /setup[/cyan]  - 配置 GitLab\n")
        return

    # 构建状态信息
    platform_name = "GitHub" if current_config.platform == "github" else "GitLab"
    ssl_status = "✓ 启用" if current_config.verify_ssl else "✗ 禁用"

    status_text = (
        f"[bold cyan]平台：[/bold cyan] {platform_name}\n"
        f"[bold cyan]配置：[/bold cyan] {current_config.name}\n"
        f"[bold cyan]地址：[/bold cyan] {current_config.base_url}\n"
        f"[bold cyan]SSL：[/bold cyan] {ssl_status}\n"
        f"[bold cyan]超时：[/bold cyan] {current_config.timeout} 秒"
    )

    # 最后测试时间
    if current_config.last_tested:
        test_time = current_config.last_tested[:19].replace('T', ' ')
        status_text += f"\n[bold cyan]测试：[/bold cyan] {test_time}"

    console.print("\n")
    console.print(Panel(
        status_text,
        title="📍 当前平台配置",
        border_style="cyan"
    ))
    console.print()
```

### 步骤 4: 实现平台切换

```python
def _platform_switch(self, platform: str, config_name: str = "") -> None:
    """切换平台"""
    from rich.console import Console

    console = Console()

    if not platform:
        console.print("\n[red]❌ 请指定平台类型[/red]")
        console.print("\n用法: [cyan]/git /platform /switch <platform> [config_name][/cyan]")
        console.print("\n平台类型: github, gitlab\n")
        return

    platform = platform.lower()

    if platform not in ["github", "gitlab"]:
        console.print(f"\n[red]❌ 不支持的平台: {platform}[/red]")
        console.print("\n支持的平台: github, gitlab\n")
        return

    # 检查是否有配置
    if not self.platform_manager.has_config(platform):
        console.print(f"\n[red]❌ 平台 {platform} 还没有配置[/red]\n")
        console.print(f"请先配置: [cyan]/git /{platform} /setup[/cyan]\n")
        return

    # 如果未指定配置名，显示可用配置让用户选择
    if not config_name:
        configs = self.platform_manager.list_configs(platform)

        if len(configs) == 1:
            # 只有一个配置，直接使用
            config_name = configs[0].name
        else:
            # 多个配置，显示列表
            console.print(f"\n[yellow]平台 {platform} 有多个配置，请指定：[/yellow]\n")
            for i, cfg in enumerate(configs, 1):
                marker = "✓" if self.platform_manager.current_config.get(platform) == cfg.name else " "
                console.print(f"  [{marker}] {i}. {cfg.name} ({cfg.base_url})")
            console.print(f"\n用法: [cyan]/git /platform /switch {platform} <配置名>[/cyan]\n")
            return

    # 执行切换
    new_config = self.platform_manager.switch_platform(platform, config_name)

    if new_config:
        platform_name = "GitHub" if platform == "github" else "GitLab"
        console.print(f"\n[green]✅ 已切换到 {platform_name}: {new_config.name}[/green]")
        console.print(f"   地址: {new_config.base_url}\n")

        # 同步到 PR 模块（Phase 6 实现）
        # self._sync_to_pr_module(new_config)
    else:
        console.print(f"\n[red]❌ 切换失败: 配置 '{config_name}' 不存在[/red]\n")
```

### 步骤 5: 实现平台概览

```python
def _platform_list(self) -> None:
    """列出所有平台配置概览"""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    # 获取所有配置
    github_configs = self.platform_manager.list_configs("github")
    gitlab_configs = self.platform_manager.list_configs("gitlab")

    if not github_configs and not gitlab_configs:
        console.print("\n[yellow]📭 还没有配置任何平台[/yellow]\n")
        console.print("请先配置平台：")
        console.print("  [cyan]/git /github /setup[/cyan]  - 配置 GitHub")
        console.print("  [cyan]/git /gitlab /setup[/cyan]  - 配置 GitLab\n")
        return

    current_platform = self.platform_manager.current_platform
    current_configs = self.platform_manager.current_config

    # 创建表格
    table = Table(title="📋 所有平台配置概览", show_header=True, header_style="bold magenta")
    table.add_column("平台", style="cyan", width=10)
    table.add_column("配置名称", style="green", width=20)
    table.add_column("地址", style="blue")
    table.add_column("状态", style="bold", width=10)

    # 添加 GitHub 配置
    for config in github_configs:
        status = ""
        if current_platform == "github" and current_configs.get("github") == config.name:
            status = "✅ 当前"

        table.add_row("GitHub", config.name, config.base_url, status)

    # 添加 GitLab 配置
    for config in gitlab_configs:
        status = ""
        if current_platform == "gitlab" and current_configs.get("gitlab") == config.name:
            status = "✅ 当前"

        table.add_row("GitLab", config.name, config.base_url, status)

    console.print("\n")
    console.print(table)
    console.print()
```

### 步骤 6: 实现帮助信息

```python
def _show_platform_help(self) -> None:
    """显示平台命令帮助"""
    print("""
📋 平台管理

使用方法:
  /git /platform                           - 显示当前平台状态
  /git /platform /switch <platform> [name] - 切换平台
  /git /platform /list                     - 列出所有平台配置

示例:
  /git /platform
  /git /platform /switch gitlab
  /git /platform /switch github work-github
  /git /platform /list
    """)
```

---

## 🧪 测试要点

### 前置准备

确保已配置至少一个 GitHub 和一个 GitLab：

```bash
/git /github /setup   # 配置 GitHub
/git /gitlab /setup   # 配置 GitLab
```

### 功能测试

1. **查看当前状态**
   ```bash
   /git /platform
   ```
   预期：显示当前激活的平台和配置

2. **切换到 GitLab**
   ```bash
   /git /platform /switch gitlab
   ```
   预期：成功切换，显示确认信息

3. **再次查看状态**
   ```bash
   /git /platform
   ```
   预期：显示已切换到 GitLab

4. **切换回 GitHub**
   ```bash
   /git /platform /switch github
   ```

5. **查看概览**
   ```bash
   /git /platform /list
   ```
   预期：显示所有平台的配置，当前激活的有 ✅ 标记

### 边界测试

1. **未配置平台时查看状态**
   - 删除所有配置
   - 运行 `/git /platform`
   - 预期：提示未配置

2. **切换到不存在的平台**
   ```bash
   /git /platform /switch bitbucket
   ```
   预期：错误提示

3. **切换到未配置的平台**
   - 如果只配置了 GitHub
   - 运行 `/git /platform /switch gitlab`
   - 预期：提示需要先配置

---

## ✅ 完成标志

- [x] `/git /platform` 显示当前状态
- [x] `/git /platform /switch` 可以切换平台
- [x] `/git /platform /list` 显示所有配置
- [x] 切换后配置持久化保存
- [x] 多个配置时提示用户选择
- [x] 错误处理完善

---

## 📝 提交代码

```bash
git add autocoder/plugins/git_helper_plugin.py
git commit -m "feat(git-plugin): 实现平台切换功能

- 添加 /git /platform 命令组
- 实现平台状态显示
- 实现 GitHub/GitLab 平台切换
- 实现所有平台配置概览
- 支持多配置选择
"
```

---

## 🎉 Phase 4 完成！

➡️ **下一步**: 阅读 `05-phase5-connection-test.md`，实现连接测试功能
