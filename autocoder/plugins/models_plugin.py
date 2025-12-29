"""
Models Plugin for Chat Auto Coder.
Provides command completion for model management commands.
"""

from typing import Any, Dict, List, Optional, Tuple

from autocoder.plugins import Plugin, PluginManager


class ModelsPlugin(Plugin):
    """Models plugin for command completion."""

    name = "models"
    description = "模型管理命令补全插件"
    version = "1.0.0"

    # 需要动态补全的命令列表
    dynamic_cmds = [
        "/models /switch",
        "/models /remove",
        "/models /chat",
    ]

    def __init__(
        self,
        manager: PluginManager,
        config: Optional[Dict[str, Any]] = None,
        config_path: Optional[str] = None,
    ):
        """Initialize the Models plugin."""
        super().__init__(manager, config, config_path)

    def initialize(self) -> bool:
        """Initialize the plugin."""
        return True

    def get_completions(self) -> Dict[str, List[str]]:
        """
        提供静态补全 - /models 子命令列表
        """
        return {
            "/models": [
                "/list",
                "/add",
                "/switch",
                "/add_provider",
                "/remove",
                "/speed-test",
                "/chat",
            ],
        }

    def get_dynamic_completions(
        self, command: str, current_input: str
    ) -> List[Tuple[str, str]]:
        """
        提供动态补全 - 模型名称列表

        Args:
            command: 基础命令，如 /models /switch
            current_input: 当前完整的输入

        Returns:
            List[Tuple[str, str]]: 补全选项列表，每个选项为 (补全文本, 显示文本)
        """
        if command == "/models /switch":
            return self._complete_available_models(current_input)
        elif command == "/models /remove":
            return self._complete_all_models(current_input)
        elif command == "/models /chat":
            return self._complete_available_models(current_input)
        return []

    def _complete_available_models(
        self, current_input: str
    ) -> List[Tuple[str, str]]:
        """
        补全已配置的模型名称（有 API Key 的模型）
        """
        from autocoder.common.llms import LLMManager

        try:
            llm_manager = LLMManager()
            all_models = llm_manager.get_all_models()

            suggestions = []
            for model in all_models.values():
                # 只显示有 API Key 的模型
                if llm_manager.has_key(model.name):
                    provider = model.provider or "custom"
                    display = f"{model.name} ({provider})"
                    suggestions.append((model.name, display))

            return suggestions
        except Exception:
            return []

    def _complete_all_models(
        self, current_input: str
    ) -> List[Tuple[str, str]]:
        """
        补全所有模型名称
        """
        from autocoder.common.llms import LLMManager

        try:
            llm_manager = LLMManager()
            all_models = llm_manager.get_all_models()

            suggestions = []
            for model in all_models.values():
                provider = model.provider or "custom"
                has_key = llm_manager.has_key(model.name)
                status = "✓" if has_key else "✗"
                display = f"{model.name} ({provider}) {status}"
                suggestions.append((model.name, display))

            return suggestions
        except Exception:
            return []

    async def execute(self, command: str, args: str) -> str:
        """
        执行命令（此插件不处理命令执行，由 models_command.py 处理）
        """
        return ""
