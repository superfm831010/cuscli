"""底部工具栏"""

import os
from pathlib import Path


def get_bottom_toolbar_func(
    get_mode_func, get_human_as_model_string_func, get_agentic_mode_string_func, plugin_manager
):
    """创建底部工具栏函数

    Args:
        get_mode_func: 获取当前模式的函数
        get_human_as_model_string_func: 获取 human_as_model 字符串的函数
        get_agentic_mode_string_func: 获取 agentic_mode 字符串的函数
        plugin_manager: 插件管理器

    Returns:
        callable: 返回工具栏内容的函数
    """

    def get_bottom_toolbar():
        mode = get_mode_func()
        agentic_mode = get_agentic_mode_string_func()
        MODES = {
            "normal": "normal",
            "auto_detect": "nature language auto detect",
            "voice_input": "voice input",
            "shell": "shell",
        }
        if mode not in MODES:
            mode = "auto_detect"
        pwd = os.getcwd()
        pwd_parts = pwd.split(os.sep)
        if len(pwd_parts) > 3:
            pwd = os.sep.join(pwd_parts[-3:])

        plugin_info = (
            f"Plugins: {len(plugin_manager.plugins)}" if plugin_manager.plugins else ""
        )

        # 获取正在运行的 async 任务数量
        async_tasks_info = ""
        try:
            from autocoder.sdk.async_runner.task_metadata import TaskMetadataManager

            async_agent_dir = Path.home() / ".auto-coder" / "async_agent"
            meta_dir = async_agent_dir / "meta"

            if meta_dir.exists():
                metadata_manager = TaskMetadataManager(str(meta_dir))
                summary = metadata_manager.get_task_summary()
                running_count = summary.get("running", 0)

                if running_count > 0:
                    async_tasks_info = f" | Async Tasks: 🔄 {running_count}"
        except Exception:
            # 静默处理异常，不影响底部工具栏的显示
            pass

        return f"PWD: {pwd} \nInput: {MODES[mode]} | Agentic Mode: {agentic_mode} | {plugin_info}{async_tasks_info}"

    return get_bottom_toolbar
