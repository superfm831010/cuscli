# Phase 6: PR 模块集成

## 🎯 阶段目标

将平台配置与现有的 Pull Request 管理模块集成，使 PR 操作使用当前激活的平台配置。

## 📋 前置条件

- ✅ Phase 1-5 已完成
- ✅ 熟悉 `autocoder/common/pull_requests/` 模块

## 🔧 实施步骤

### 步骤 1: 在插件初始化时同步配置

修改 `GitHelperPlugin` 的 `initialize` 方法：

```python
def initialize(self) -> bool:
    """Initialize the plugin."""
    if not self.git_available:
        print(f"[{self.name}] {get_message('git_not_available_warning')}")
        return True

    print(f"[{self.name}] {get_message('git_helper_initialized')}")

    # 新增：同步当前平台配置到 PR 模块
    self._sync_current_config_to_pr()

    return True
```

### 步骤 2: 实现配置同步方法

```python
def _sync_current_config_to_pr(self) -> None:
    """将当前平台配置同步到 PR 模块"""
    try:
        current_config = self.platform_manager.get_current_config()

        if not current_config:
            # 没有配置，跳过
            return

        # 导入 PR 模块
        from autocoder.common.pull_requests import set_global_config
        from autocoder.common.pull_requests.models import PRConfig, PlatformType

        # 转换为 PR 配置
        pr_config = PRConfig(
            platform=PlatformType(current_config.platform),
            token=current_config.token,
            base_url=current_config.base_url,
            verify_ssl=current_config.verify_ssl,
            timeout=current_config.timeout
        )

        # 设置全局配置
        set_global_config(pr_config)

        from loguru import logger
        logger.info(
            f"[Git Plugin] 已同步平台配置到 PR 模块: "
            f"{current_config.platform}/{current_config.name}"
        )

    except Exception as e:
        from loguru import logger
        logger.warning(f"[Git Plugin] 同步 PR 配置失败: {e}")
```

### 步骤 3: 在平台切换时同步

修改 `_platform_switch` 方法，在切换成功后同步：

```python
def _platform_switch(self, platform: str, config_name: str = "") -> None:
    """切换平台"""
    # ... (现有代码保持不变) ...

    # 执行切换
    new_config = self.platform_manager.switch_platform(platform, config_name)

    if new_config:
        platform_name = "GitHub" if platform == "github" else "GitLab"
        console.print(f"\n[green]✅ 已切换到 {platform_name}: {new_config.name}[/green]")
        console.print(f"   地址: {new_config.base_url}\n")

        # 新增：同步到 PR 模块
        self._sync_config_to_pr(new_config)
    else:
        console.print(f"\n[red]❌ 切换失败: 配置 '{config_name}' 不存在[/red]\n")


def _sync_config_to_pr(self, config) -> None:
    """将指定配置同步到 PR 模块"""
    try:
        from autocoder.common.pull_requests import set_global_config
        from autocoder.common.pull_requests.models import PRConfig, PlatformType

        pr_config = PRConfig(
            platform=PlatformType(config.platform),
            token=config.token,
            base_url=config.base_url,
            verify_ssl=config.verify_ssl,
            timeout=config.timeout
        )

        set_global_config(pr_config)

        from loguru import logger
        logger.info(f"[Git Plugin] 平台切换后已同步 PR 配置")

    except Exception as e:
        from rich.console import Console
        console = Console()
        console.print(f"[yellow]⚠️  同步 PR 配置失败: {e}[/yellow]")
```

---

## 🧪 测试要点

### 集成测试流程

1. **启动应用并检查初始同步**
   ```bash
   # 启动 chat-auto-coder
   python -m autocoder.chat_auto_coder
   ```

   检查日志：
   ```bash
   tail -f .auto-coder/logs/auto-coder.log | grep "PR 配置"
   ```

   预期：看到配置同步日志

2. **切换平台并验证同步**
   ```bash
   # 在 chat 中执行
   /git /platform /switch gitlab
   ```

   检查日志：
   预期：看到 "平台切换后已同步 PR 配置"

3. **验证 PR 操作使用正确配置**

   创建测试脚本 `test_pr_integration.py`：

   ```python
   """测试 PR 模块集成"""
   from autocoder.common.pull_requests import get_global_manager

   def test_pr_config():
       """验证 PR 配置是否正确"""
       manager = get_global_manager()

       if manager.config:
           print(f"✅ PR 模块已配置")
           print(f"   平台: {manager.config.platform}")
           print(f"   地址: {manager.config.base_url}")
           print(f"   SSL: {manager.config.verify_ssl}")
       else:
           print("⚠️  PR 模块未配置")

   if __name__ == "__main__":
       test_pr_config()
   ```

   运行：
   ```bash
   python test_pr_integration.py
   ```

4. **完整流程测试**

   a. 配置 GitHub：
   ```bash
   /git /github /setup
   ```

   b. 切换到 GitHub：
   ```bash
   /git /platform /switch github
   ```

   c. 验证 PR 配置：
   ```python
   python test_pr_integration.py
   ```
   预期：显示 GitHub 配置

   d. 切换到 GitLab：
   ```bash
   /git /platform /switch gitlab
   ```

   e. 再次验证：
   ```python
   python test_pr_integration.py
   ```
   预期：显示 GitLab 配置

---

## ✅ 完成标志

- [x] 插件初始化时自动同步配置
- [x] 平台切换时自动同步配置
- [x] PR 模块使用正确的平台配置
- [x] 日志记录同步操作
- [x] 错误处理正常（同步失败不影响插件运行）

---

## 📝 提交代码

```bash
git add autocoder/plugins/git_helper_plugin.py
git commit -m "feat(git-plugin): 集成 PR 管理模块

- 插件初始化时同步配置到 PR 模块
- 平台切换时自动同步配置
- 添加配置转换方法
- 添加同步日志记录
- 完善错误处理
"
```

---

## 🎉 Phase 6 完成！

➡️ **下一步**: 阅读 `07-phase7-completion.md`，实现命令补全增强
