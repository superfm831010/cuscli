"""帮助信息显示"""

from autocoder.chat_auto_coder_lang import get_message


def show_help(plugin_manager):
    """显示帮助信息"""
    print(f"\033[1m{get_message('supported_commands')}\033[0m")
    print()
    print(
        f"  \033[94m{get_message('commands')}\033[0m - \033[93m{get_message('description')}\033[0m"
    )
    print(
        f"  \033[94m/auto\033[0m \033[93m<query>\033[0m - \033[92m{get_message('auto_desc')}\033[0m"
    )
    print(
        f"    \033[94m/auto /new\033[0m \033[93m<query>\033[0m - \033[92m{get_message('auto_new_desc')}\033[0m"
    )
    print(
        f"    \033[94m/auto /resume\033[0m \033[93m<id> <query>\033[0m - \033[92m{get_message('auto_resume_desc')}\033[0m"
    )
    print(
        f"    \033[94m/auto /list\033[0m - \033[92m{get_message('auto_list_desc')}\033[0m"
    )
    print(
        f"    \033[94m/auto /command\033[0m \033[93m<file>\033[0m - \033[92m{get_message('auto_command_desc')}\033[0m"
    )

    print(f"  \033[94m/commit\033[0m - \033[92m{get_message('commit_desc')}\033[0m")

    print(
        f"  \033[94m/conf\033[0m \033[93m<key>:<value>\033[0m  - \033[92m{get_message('conf_desc')}\033[0m"
    )

    print(
        f"  \033[94m/shell\033[0m \033[93m<command>\033[0m - \033[92m{get_message('shell_desc')}\033[0m"
    )
    print(
        f"  \033[94m/shell\033[0m - \033[92m{get_message('shell_interactive_desc')}\033[0m"
    )
    print(
        f"  \033[94m!\033[0m\033[93m<command>\033[0m - \033[92m{get_message('shell_single_command_desc')}\033[0m"
    )

    print(
        f"  \033[94m/add_files\033[0m \033[93m<file1> <file2> ...\033[0m - \033[92m{get_message('add_files_desc')}\033[0m"
    )
    print(
        f"  \033[94m/remove_files\033[0m \033[93m<file1>,<file2> ...\033[0m - \033[92m{get_message('remove_files_desc')}\033[0m"
    )
    print(
        f"  \033[94m/chat\033[0m \033[93m<query>\033[0m - \033[92m{get_message('chat_desc')}\033[0m"
    )
    print(
        f"  \033[94m/coding\033[0m \033[93m<query>\033[0m - \033[92m{get_message('coding_desc')}\033[0m"
    )

    print(f"  \033[94m/revert\033[0m - \033[92m{get_message('revert_desc')}\033[0m")
    print(
        f"  \033[94m/index/query\033[0m \033[93m<args>\033[0m - \033[92m{get_message('index_query_desc')}\033[0m"
    )
    print(
        f"  \033[94m/index/build\033[0m - \033[92m{get_message('index_build_desc')}\033[0m"
    )
    print(
        f"  \033[94m/list_files\033[0m - \033[92m{get_message('list_files_desc')}\033[0m"
    )
    print(f"  \033[94m/help\033[0m - \033[92m{get_message('help_desc')}\033[0m")
    print(f"  \033[94m/mode\033[0m - \033[92m{get_message('mode_desc')}\033[0m")
    print(f"  \033[94m/lib\033[0m - \033[92m{get_message('lib_desc')}\033[0m")
    print(f"  \033[94m/models\033[0m - \033[92m{get_message('models_desc')}\033[0m")
    print(f"  \033[94m/plugins\033[0m - \033[92m{get_message('plugins_desc')}\033[0m")
    print(
        f"  \033[94m/active_context\033[0m - \033[92m{get_message('active_context_desc')}\033[0m"
    )
    print(f"  \033[94m/exit\033[0m - \033[92m{get_message('exit_desc')}\033[0m")
    print()

    # 显示插件命令
    if plugin_manager.command_handlers:
        print(f"\033[1m{get_message('plugin_commands_title')}\033[0m")
        print(
            f"  \033[94m{get_message('plugin_command_header')}\033[0m - \033[93m{get_message('plugin_description_header')}\033[0m"
        )
        for cmd, (_, desc, plugin_id) in plugin_manager.command_handlers.items():
            plugin = plugin_manager.get_plugin(plugin_id)
            if plugin:
                print(
                    f"  \033[94m{cmd}\033[0m - \033[92m{desc} ({get_message('plugin_from')} {plugin.plugin_name()})\033[0m"
                )
            else:
                print(
                    f"  \033[94m{cmd}\033[0m - \033[92m{desc} ({get_message('plugin_from_unknown')})\033[0m"
                )
        print()
