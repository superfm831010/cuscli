"""
Auto Coder Chat V3 - 入口文件

这是重构后的终端交互入口，使用模块化的设计。
"""

from loguru import logger

logger.remove()  # 把默认 sink 去掉，彻底静音

from autocoder.run_context import get_run_context, RunMode

# 设置运行模式为终端模式
get_run_context().set_mode(RunMode.TERMINAL)

import asyncio
import argparse
from pathlib import Path
from autocoder.auto_coder_runner import (
    load_tokenizer,
    initialize_system,
    InitializeSystemRequest,
    configure,
    start as start_engine,
    completer,
    ask,
    coding,
    chat,
    design,
    voice_input,
    auto_command,
    run_agentic,
    execute_shell_command,
    active_context,
    get_mcp_server,
    stop as stop_engine,
)
from autocoder.chat_auto_coder_lang import (
    get_message,
    get_message_with_format as get_message_with_format_local,
)
from autocoder.plugins import PluginManager
from autocoder.terminal_v3 import AutoCoderChatApp


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Auto-Coder V3 - Claude-style Chat Interface"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Enter the auto-coder.chat without initializing the system",
    )
    parser.add_argument(
        "--skip_provider_selection",
        action="store_true",
        help="Skip the provider selection",
    )
    parser.add_argument(
        "--product_mode",
        type=str,
        default="lite",
        help="The mode of the auto-coder.chat, lite/pro default is lite",
    )
    parser.add_argument("--lite", action="store_true", help="Lite mode")
    parser.add_argument("--pro", action="store_true", help="Pro mode")
    return parser.parse_args()

def load_builtin_plugins(plugin_manager):
    """加载内置插件"""
    try:
        # 发现所有可用的插件
        discovered_plugins = plugin_manager.discover_plugins()

        # 排除的示例插件列表
        excluded_plugins = {
            "autocoder.plugins.dynamic_completion_example",
            "autocoder.plugins.sample_plugin",
        }

        # 自动加载内置插件（在autocoder.plugins模块中的插件）
        builtin_loaded = 0
        for plugin_class in discovered_plugins:
            module_name = plugin_class.__module__
            if (
                module_name.startswith("autocoder.plugins.")
                and not module_name.endswith(".__init__")
                and module_name not in excluded_plugins
            ):
                try:
                    if plugin_manager.load_plugin(plugin_class):
                        builtin_loaded += 1
                        print(f"✓ Loaded builtin plugin: {plugin_class.plugin_name()}")
                except Exception as e:
                    print(
                        f"✗ Failed to load builtin plugin {plugin_class.plugin_name()}: {e}"
                    )

        if builtin_loaded > 0:
            print(
                get_message_with_format_local(
                    "loaded_plugins_builtin", count=builtin_loaded
                )
            )
        else:
            print(get_message("no_builtin_plugins_loaded"))

    except Exception as e:
        print(f"Error loading builtin plugins: {e}")


async def async_main():
    """异步主函数"""
    load_tokenizer()
    args = parse_arguments()
    
    if args.lite:
        args.product_mode = "lite"
    
    if args.pro:
        args.product_mode = "pro"
    
    if not args.quick:
        initialize_system(
            InitializeSystemRequest(
                product_mode=args.product_mode,
                skip_provider_selection=args.skip_provider_selection,
                debug=args.debug,
                quick=args.quick,
                lite=args.lite,
                pro=args.pro,
            )
        )



    # 启动引擎
    start_engine()

    # 初始化插件系统
    plugin_manager = PluginManager()
    plugin_manager.load_global_plugin_dirs()

    # 添加内置插件目录
    plugins_dir = Path(__file__).parent.parent / "plugins"
    plugin_manager.add_global_plugin_directory(str(plugins_dir))

    # 加载保存的运行时配置
    plugin_manager.load_runtime_cfg()

    # 自动加载内置插件
    load_builtin_plugins(plugin_manager)

    # 配置 product_mode
    configure(f"product_mode:{args.product_mode}")

    # 创建原始函数字典
    original_functions = {
        "ask": ask,
        "coding": coding,
        "chat": chat,
        "design": design,
        "voice_input": voice_input,
        "auto_command": auto_command,
        "run_agentic": run_agentic,
        "execute_shell_command": execute_shell_command,
        "active_context": active_context,
    }

    # 创建 wrapped functions
    wrapped_functions = {}
    for func_name, original_func in original_functions.items():
        wrapped_functions[func_name] = plugin_manager.wrap_function(
            original_func, func_name
        )
    
    # 创建并运行聊天式 TUI 应用
    chat_app = AutoCoderChatApp(plugin_manager=plugin_manager)
    await chat_app.run()


def main():
    """同步入口函数，供 console_scripts 使用"""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
