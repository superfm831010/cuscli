import os
import io
import contextlib
import fnmatch
import json
from typing import Dict, Any, List, Callable, Optional, Literal
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from autocoder.common.conf_validator import ConfigValidator
from autocoder.common.international import get_message, get_message_with_format
from autocoder.common.ac_style_command_parser import create_config, parse_typed_query

# Import core_config functions for direct configuration management
from autocoder.common.core_config import get_memory_manager, get_global_memory_manager


# Helper function to print the configuration table (internal implementation)
def _print_conf_table(content: Dict[str, Any], title: str = "Configuration Settings"):
    """Display configuration dictionary in a Rich table format."""
    output_buffer = io.StringIO()
    console = Console(
        file=output_buffer, force_terminal=True, color_system="truecolor"
    )  # Capture output

    # Create a styled table with rounded borders
    table = Table(
        show_header=True,
        header_style="bold magenta",
        title=title,
        title_style="bold blue",
        border_style="blue",
        show_lines=True,
    )

    # Add columns with explicit width and alignment
    table.add_column(
        get_message("conf_key"), style="cyan", justify="right", width=30, no_wrap=False
    )
    table.add_column(
        get_message("conf_value"),
        style="green",
        justify="left",
        width=50,
        no_wrap=False,
    )

    # Sort keys for consistent display
    for key in sorted(content.keys()):
        value = content[key]
        # Format value based on type
        if isinstance(value, (dict, list)):
            formatted_value = Text(json.dumps(value, indent=2), style="yellow")
        elif isinstance(value, bool):
            formatted_value = Text(str(value), style="bright_green" if value else "red")
        elif isinstance(value, (int, float)):
            formatted_value = Text(str(value), style="bright_cyan")
        else:
            formatted_value = Text(str(value), style="green")

        table.add_row(str(key), formatted_value)

    # Add padding and print with a panel
    console.print(
        Panel(
            table,
            padding=(1, 2),
            subtitle=f"[italic]{get_message('conf_subtitle')}[/italic]",
            border_style="blue",
        )
    )
    return output_buffer.getvalue()  # Return captured string


# --- Command Handlers ---


def _handle_list_conf(
    args: List[str], scope: Literal["project", "global", "merged"] = "merged"
) -> str:
    """Handles listing configuration settings, supports wildcard filtering."""
    if scope == "global":
        memory_manager = get_global_memory_manager()
        source_scope = "project"  # Global manager reads from its own "project" scope
    else:
        memory_manager = get_memory_manager()
        source_scope = scope

    conf = memory_manager.get_all_config(source=source_scope)
    pattern = args[0] if args else "*"  # Default to all if no pattern

    if pattern == "*":
        scope_suffix = f" ({scope})" if scope != "merged" else ""
        title = get_message("conf_title") + scope_suffix
        filtered_conf = conf
    else:
        scope_suffix = f" ({scope})" if scope != "merged" else ""
        title = (
            get_message_with_format("conf_filtered_title", pattern=pattern)
            + scope_suffix
        )
        filtered_conf = {k: v for k, v in conf.items() if fnmatch.fnmatch(k, pattern)}
        if not filtered_conf:
            return get_message_with_format("conf_no_pattern_matches", pattern=pattern)

    if not filtered_conf and pattern == "*":
        return get_message("conf_no_configs_found")

    return _print_conf_table(filtered_conf, title)


def _handle_get_conf(
    args: List[str], scope: Literal["project", "global", "merged"] = "merged"
) -> str:
    """Handles getting a specific configuration setting."""
    if len(args) != 1:
        return get_message("conf_get_error_args")
    key = args[0]

    if scope == "global":
        memory_manager = get_global_memory_manager()
        value = memory_manager.get_config(key, source="project")
    else:
        memory_manager = get_memory_manager()
        value = memory_manager.get_config(key, source=scope)

    if value is None:
        return get_message_with_format("conf_get_error_not_found", key=key)
    else:
        # Format value for better readability
        if isinstance(value, (list, dict)):
            formatted_value = json.dumps(value, indent=2)
        else:
            formatted_value = repr(value)
        return f"{key}: {formatted_value}"


def _parse_value(value_str: str) -> Any:
    """Attempts to parse the value string into common types."""
    value_str = value_str.strip()
    if value_str.lower() == "true":
        return True
    if value_str.lower() == "false":
        return False
    if value_str.lower() == "none" or value_str.lower() == "null":
        return None
    # Keep quoted strings as strings without quotes
    if (value_str.startswith('"') and value_str.endswith('"')) or (
        value_str.startswith("'") and value_str.endswith("'")
    ):
        return value_str[1:-1]

    try:
        # Try int first
        return int(value_str)
    except ValueError:
        pass
    try:
        # Then try float
        return float(value_str)
    except ValueError:
        pass
    # If none of the above, return as string
    return value_str


def _handle_set_conf(
    args: List[str], scope: Literal["project", "global"] = "project"
) -> str:
    """Handles setting or updating a configuration setting."""
    if len(args) < 2:
        return get_message("conf_set_error_args")
    key = args[0]
    # Join the rest of the arguments to form the value string
    value_str = " ".join(args[1:])
    try:
        parsed_value = _parse_value(value_str)

        # Get appropriate memory manager based on scope
        if scope == "global":
            memory_manager = get_global_memory_manager()
        else:
            memory_manager = get_memory_manager()

        product_mode = memory_manager.get_config("product_mode", "lite")
        ConfigValidator.validate(key, str(parsed_value), product_mode)

        # Set configuration using MemoryManager
        memory_manager.set_config(key, parsed_value)

        scope_suffix = f" (global)" if scope == "global" else ""
        # Use repr for confirmation message for clarity
        return (
            get_message_with_format(
                "conf_set_success", key=key, value=repr(parsed_value)
            )
            + scope_suffix
        )
    except Exception as e:
        return get_message_with_format("conf_set_error", key=key, error=str(e))


def _handle_delete_conf(
    args: List[str], scope: Literal["project", "global"] = "project"
) -> str:
    """Handles deleting configuration settings. Supports multiple keys separated by commas."""
    if len(args) != 1:
        return get_message("conf_delete_error_args")

    # 支持逗号分隔的多个key
    keys_str = args[0]
    keys = [key.strip() for key in keys_str.split(",") if key.strip()]

    if not keys:
        return "Error: No valid keys provided for deletion."

    # Get appropriate memory manager based on scope
    if scope == "global":
        memory_manager = get_global_memory_manager()
    else:
        memory_manager = get_memory_manager()

    results = []
    deleted_keys = []
    not_found_keys = []
    error_keys = []

    for key in keys:
        if memory_manager.has_config(key, source="project"):
            try:
                memory_manager.delete_config(key)
                deleted_keys.append(key)
            except Exception as e:
                error_keys.append(f"{key} ({str(e)})")
        else:
            not_found_keys.append(key)

    # 构建返回消息
    messages = []
    scope_suffix = f" (global)" if scope == "global" else ""

    if deleted_keys:
        if len(deleted_keys) == 1:
            messages.append(
                get_message_with_format("conf_delete_success", key=deleted_keys[0])
                + scope_suffix
            )
        else:
            messages.append(
                f"Successfully deleted configurations: {', '.join(deleted_keys)}"
                + scope_suffix
            )

    if not_found_keys:
        if len(not_found_keys) == 1:
            messages.append(
                get_message_with_format("conf_delete_not_found", key=not_found_keys[0])
            )
        else:
            messages.append(f"Configurations not found: {', '.join(not_found_keys)}")

    if error_keys:
        messages.append(f"Failed to delete: {', '.join(error_keys)}")

    return "\n".join(messages)


def _handle_help(args: List[str]) -> str:
    """Provides help text for the /conf command."""
    if args:
        return get_message("conf_help_args_error")

    help_text = get_message("conf_help_text")
    return help_text


# Command dispatch table
COMMAND_HANDLERS: Dict[str, Callable[[List[str]], str]] = {
    "list": _handle_list_conf,
    "show": _handle_list_conf,  # Alias
    "get": _handle_get_conf,
    "set": _handle_set_conf,
    "delete": _handle_delete_conf,
    "del": _handle_delete_conf,  # Alias
    "rm": _handle_delete_conf,  # Alias
    "drop": _handle_delete_conf,  # Add this line for /drop command
    "help": _handle_help,
}


def handle_conf_command(command_args: str) -> str:
    """
    处理配置命令，支持两种格式：
    1. 双斜杠格式（/conf /command）
    2. 键值对格式（/conf key:value）
    3. 全局配置格式（/conf /global /command）

    支持的命令格式：
    - /conf /list [pattern]     - 列出配置（可带过滤模式）
    - /conf /show [pattern]     - 列出配置（list的别名）
    - /conf /get <key>          - 获取单个配置
    - /conf /set <key> <value>  - 设置配置
    - /conf /delete <key>       - 删除配置
    - /conf /del <key>          - 删除配置（别名）
    - /conf /rm <key>           - 删除配置（别名）
    - /conf /drop <key>         - 删除配置（别名）
    - /conf /help               - 显示帮助
    - /conf /export <path>      - 导出配置
    - /conf /import <path>      - 导入配置
    - /conf key:value           - 设置配置（简化格式）

    全局配置命令（操作 ~/.auto-coder）:
    - /conf /global /list [pattern]     - 列出全局配置
    - /conf /global /get <key>          - 获取全局配置
    - /conf /global /set <key> <value>  - 设置全局配置
    - /conf /global /delete <key>       - 删除全局配置

    Args:
        command_args: 命令参数字符串

    Returns:
        str: 返回给用户的响应字符串
    """
    conf_str = command_args.strip()

    # 检查是否为 /global 子命令
    is_global = False
    if conf_str.startswith("/global"):
        is_global = True
        # 移除 /global 前缀，保留后续命令
        conf_str = conf_str[len("/global") :].strip()

    # 检查是否为 key:value 简写格式（项目级与全局级均支持）
    if ":" in conf_str and not conf_str.startswith("/"):
        # 解析 key:value 格式
        parts = conf_str.split(":", 1)  # 只分割第一个冒号
        if len(parts) == 2:
            key = parts[0].strip()
            value = parts[1].strip()
            return _handle_set_conf(
                [key, value], scope="global" if is_global else "project"
            )
        else:
            return f"Error: Invalid key:value format. Usage: /conf key:value"

    # 创建配置解析器
    config = (
        create_config()
        .collect_remainder("query")  # 收集剩余参数
        .command("list")
        .positional("pattern")  # 可选的过滤模式
        .max_args(1)  # 列出配置
        .command("show")  # list的别名
        .positional("pattern")
        .max_args(1)
        .command("get")
        .positional("key", required=True)
        .max_args(1)  # 获取单个配置
        .command("set")
        .positional("key", required=True)
        .positional("value", required=True)
        .max_args(2)  # 设置配置
        .command("delete")
        .collect_remainder("keys")  # 收集所有剩余参数以支持逗号分隔的多个key
        .command("del")  # delete的别名
        .collect_remainder("keys")
        .command("rm")  # delete的别名
        .collect_remainder("keys")
        .command("drop")  # delete的别名
        .collect_remainder("keys")
        .command("help")
        .max_args(0)  # 显示帮助
        .command("export")
        .positional("path", required=True)
        .max_args(1)  # 导出配置
        .command("import")
        .positional("path", required=True)
        .max_args(1)  # 导入配置
        .build()
    )

    if not conf_str:
        # 默认显示所有配置
        scope = "global" if is_global else "merged"
        return _handle_list_conf([], scope=scope)

    # 解析命令
    result = parse_typed_query(conf_str, config)

    # 确定作用域
    read_scope = "global" if is_global else "merged"
    write_scope = "global" if is_global else "project"

    # 检查各种子命令
    if result.has_command("list"):
        list_cmd = result.get_command("list")
        pattern = list_cmd.args[0] if list_cmd.args else "*"
        return _handle_list_conf([pattern] if pattern != "*" else [], scope=read_scope)

    if result.has_command("show"):
        show_cmd = result.get_command("show")
        pattern = show_cmd.args[0] if show_cmd.args else "*"
        return _handle_list_conf([pattern] if pattern != "*" else [], scope=read_scope)

    if result.has_command("get"):
        get_cmd = result.get_command("get")
        if not get_cmd.args:
            return "Error: 'get' command requires exactly one argument (the key). Usage: /conf /get <key>"
        return _handle_get_conf([get_cmd.args[0]], scope=read_scope)

    if result.has_command("set"):
        set_cmd = result.get_command("set")
        if len(set_cmd.args) < 2:
            return "Error: 'set' command requires exactly two arguments (key and value). Usage: /conf /set <key> <value>"
        return _handle_set_conf([set_cmd.args[0], set_cmd.args[1]], scope=write_scope)

    if (
        result.has_command("delete")
        or result.has_command("del")
        or result.has_command("rm")
        or result.has_command("drop")
    ):
        # 查找删除命令
        delete_cmd = None
        for cmd_name in ["delete", "del", "rm", "drop"]:
            if result.has_command(cmd_name):
                delete_cmd = result.get_command(cmd_name)
                break

        if not delete_cmd or not delete_cmd.remainder:
            return "Error: 'delete' command requires at least one key. Usage: /conf /delete <key> or /conf /delete <key1,key2,key3>"

        # remainder 已经是一个字符串，直接传递给处理函数
        keys_str = delete_cmd.remainder
        return _handle_delete_conf([keys_str], scope=write_scope)

    if result.has_command("help"):
        return _handle_help([])

    # Export/Import 暂不支持全局作用域（未来可扩展）
    if result.has_command("export"):
        if is_global:
            return "Error: /conf /global /export is not supported yet."
        export_cmd = result.get_command("export")
        if not export_cmd.args:
            return (
                "Error: Please specify a path for export. Usage: /conf /export <path>"
            )

        export_path = export_cmd.args[0]
        try:
            from autocoder.common.conf_import_export import export_conf

            export_conf(os.getcwd(), export_path)
            return get_message_with_format("conf_export_success", path=export_path)
        except Exception as e:
            return get_message_with_format("conf_export_error", error=str(e))

    if result.has_command("import"):
        if is_global:
            return "Error: /conf /global /import is not supported yet."
        import_cmd = result.get_command("import")
        if not import_cmd.args:
            return (
                "Error: Please specify a path for import. Usage: /conf /import <path>"
            )

        import_path = import_cmd.args[0]
        try:
            from autocoder.common.conf_import_export import import_conf

            import_conf(os.getcwd(), import_path)
            return get_message_with_format("conf_import_success", path=import_path)
        except Exception as e:
            return get_message_with_format("conf_import_error", error=str(e))

    # 未知命令
    return f"Error: Unknown command '/conf {command_args}'. Type '/conf /help' for available commands."
