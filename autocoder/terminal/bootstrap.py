"""引导模块 - 初始化系统并启动应用"""

import asyncio
import os
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
from autocoder.common.core_config import (
    cycle_mode,
    get_mode,
    set_mode,
    toggle_human_as_model,
    get_human_as_model_string,
    toggle_agentic_mode,
    get_agentic_mode_string,
)
from autocoder.plugins import PluginManager
from autocoder.chat_auto_coder_lang import (
    get_message,
    get_message_with_format as get_message_with_format_local,
)
from autocoder.terminal.args import parse_arguments
from autocoder.terminal.help import show_help
from autocoder.terminal.app import TerminalApp


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


def run_cli():
    """CLI 入口函数"""
    # 加载 tokenizer
    load_tokenizer()

    # 解析参数
    args = parse_arguments()

    # 处理 lite/pro 模式
    if args.lite:
        args.product_mode = "lite"
    if args.pro:
        args.product_mode = "pro"

    # 初始化系统（如果不是 quick 模式）
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

    # 创建 show_help 函数
    def show_help_func():
        show_help(plugin_manager)

    # 创建终端应用
    app = TerminalApp(
        plugin_manager=plugin_manager,
        wrapped_functions=wrapped_functions,
        configure_func=configure,
        show_help_func=show_help_func,
        base_completer=completer,
        get_mode_func=get_mode,
        get_human_as_model_string_func=get_human_as_model_string,
        get_agentic_mode_string_func=get_agentic_mode_string,
        cycle_mode_func=cycle_mode,
        toggle_human_as_model_func=toggle_human_as_model,
        toggle_agentic_mode_func=toggle_agentic_mode,
        voice_input_func=wrapped_functions.get("voice_input"),
        get_mcp_server_func=get_mcp_server,
        stop_engine_func=stop_engine,
        debug=args.debug,
    )

    # 运行应用
    asyncio.run(app.run())
