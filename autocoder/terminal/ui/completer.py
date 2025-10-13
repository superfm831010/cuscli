"""增强的命令补全器"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from prompt_toolkit.completion import Completer, Completion


class EnhancedCompleter(Completer):
    """结合内置补全器和插件补全功能的增强补全器"""

    def __init__(self, base_completer: Completer, plugin_manager):
        self.base_completer: Completer = base_completer
        self.plugin_manager = plugin_manager

    def get_completions(self, document, complete_event):
        # 获取当前输入的文本
        text_before_cursor = document.text_before_cursor.lstrip()

        # 只有当我们需要处理命令补全时才进行处理
        if text_before_cursor.startswith("/"):

            # 获取当前输入的命令前缀
            current_input = text_before_cursor
            # 检查是否需要动态补全
            if " " in current_input:
                # 将连续的空格替换为单个空格
                _input_one_space = " ".join(current_input.split())
                # 先尝试动态补全特定命令
                dynamic_cmds = self.plugin_manager.get_dynamic_cmds()

                # 最长命令优先匹配，避免短命令抢占长命令的补全权
                sorted_dynamic_cmds = sorted(dynamic_cmds, key=len, reverse=True)

                for dynamic_cmd in sorted_dynamic_cmds:
                    if _input_one_space.startswith(dynamic_cmd):
                        # 精确匹配：确保匹配到的是完整命令（末尾是空格或输入结束）
                        next_char_pos = len(dynamic_cmd)
                        if next_char_pos == len(_input_one_space) or (
                            next_char_pos < len(_input_one_space)
                            and _input_one_space[next_char_pos] == " "
                        ):
                            # 使用 PluginManager 处理动态补全，通常是用于命令或子命令动态的参数值列表的补全
                            completions = self.plugin_manager.process_dynamic_completions(
                                dynamic_cmd, current_input
                            )
                            for completion_text, display_text in completions:
                                yield Completion(
                                    completion_text,
                                    start_position=0,
                                    display=display_text,
                                )
                            return

                # 如果不是特定命令，检查一般命令 + 空格的情况, 通常是用于固定的下级子命令列表的补全
                # 获取插件命令补全
                plugin_completions_dict = self.plugin_manager.get_plugin_completions()

                # 找到最长的匹配命令前缀（支持多级命令）
                matched_cmd = self._find_longest_matching_command(
                    _input_one_space, plugin_completions_dict
                )

                # 如果找到匹配的命令前缀，进行处理
                if matched_cmd:
                    yield from self._process_command_completions(
                        matched_cmd, current_input, plugin_completions_dict[matched_cmd]
                    )
                    return
            # 处理直接命令补全 - 如果输入不包含空格，匹配整个命令
            for command in self.plugin_manager.get_all_commands_with_prefix(
                current_input
            ):
                yield Completion(
                    command[len(current_input) :],
                    start_position=0,
                    display=command,
                )

        # 获取并返回基础补全器的补全
        if self.base_completer:
            for completion in self.base_completer.get_completions(
                document, complete_event
            ):
                yield completion

    def _find_longest_matching_command(self, current_input, plugin_completions_dict):
        """找到最长的匹配命令前缀（支持多级命令）

        Args:
            current_input: 标准化后的当前输入（如 "/git /github"）
            plugin_completions_dict: 插件补全字典

        Returns:
            匹配的命令前缀，如果没有匹配返回None
        """
        # 收集所有匹配的命令前缀
        matched_commands = []

        for cmd_prefix in plugin_completions_dict.keys():
            # 检查当前输入是否以该命令前缀开头
            if current_input.startswith(cmd_prefix):
                # 精确匹配：确保匹配到的是完整命令（末尾是空格或输入结束）
                next_char_pos = len(cmd_prefix)
                if next_char_pos == len(current_input) or (
                    next_char_pos < len(current_input)
                    and current_input[next_char_pos] == " "
                ):
                    matched_commands.append(cmd_prefix)

        # 返回最长的匹配（支持多级命令，如 "/git /github" 优先于 "/git"）
        if matched_commands:
            return max(matched_commands, key=len)

        return None

    def _process_command_completions(self, command, current_input, completions):
        """处理通用命令补全"""
        # 提取子命令前缀
        # 注意：这里需要根据命令的层级来提取子命令前缀
        # 例如：command="/git /github", current_input="/git /github /setup"
        # 应该提取 "/setup" 作为子命令前缀

        # 计算命令前缀的单词数
        command_parts_count = len(command.split())

        # 分割当前输入
        parts = current_input.split()
        cmd_prefix = ""

        # 如果输入的部分数大于命令的部分数，说明用户开始输入子命令了
        if len(parts) > command_parts_count:
            # 获取命令之后的部分作为子命令前缀
            cmd_prefix = " ".join(parts[command_parts_count:])

        # 对于任何命令，当子命令前缀为空或与补全选项匹配时，都显示补全
        for completion in completions:
            if cmd_prefix == "" or completion.startswith(cmd_prefix):
                # 只提供未输入部分作为补全
                remaining_text = completion[len(cmd_prefix) :]
                # 修复：设置 start_position 为 0，这样不会覆盖用户已输入的部分
                start_position = 0
                yield Completion(
                    remaining_text,
                    start_position=start_position,
                    display=completion,
                )

    async def get_completions_async(self, document, complete_event):
        """异步获取补全内容。

        使用 asyncio.run_in_executor 来异步执行耗时的补全操作，
        避免阻塞主线程导致输入卡顿。
        """
        # 获取当前输入的文本
        text_before_cursor = document.text_before_cursor.lstrip()

        # 只有当我们需要处理命令补全时才进行处理
        if text_before_cursor.startswith("/"):
            # 获取当前输入的命令前缀
            current_input = text_before_cursor

            # 使用线程池执行器来异步执行耗时操作
            loop = asyncio.get_event_loop()
            executor = ThreadPoolExecutor(max_workers=1)

            try:
                # 检查是否需要动态补全
                if " " in current_input:
                    # 将连续的空格替换为单个空格
                    _input_one_space = " ".join(current_input.split())

                    # 异步获取动态命令列表
                    dynamic_cmds = await loop.run_in_executor(
                        executor, self.plugin_manager.get_dynamic_cmds
                    )

                    # 最长命令优先匹配，避免短命令抢占长命令的补全权
                    sorted_dynamic_cmds = sorted(dynamic_cmds, key=len, reverse=True)

                    for dynamic_cmd in sorted_dynamic_cmds:
                        if _input_one_space.startswith(dynamic_cmd):
                            # 精确匹配：确保匹配到的是完整命令（末尾是空格或输入结束）
                            next_char_pos = len(dynamic_cmd)
                            if next_char_pos == len(_input_one_space) or (
                                next_char_pos < len(_input_one_space)
                                and _input_one_space[next_char_pos] == " "
                            ):
                                # 异步处理动态补全
                                completions = await loop.run_in_executor(
                                    executor,
                                    self.plugin_manager.process_dynamic_completions,
                                    dynamic_cmd,
                                    current_input,
                                )
                                for completion_text, display_text in completions:
                                    yield Completion(
                                        completion_text,
                                        start_position=0,
                                        display=display_text,
                                    )
                                return

                    # 如果不是特定命令，检查一般命令 + 空格的情况
                    # 异步获取插件命令补全
                    plugin_completions_dict = await loop.run_in_executor(
                        executor, self.plugin_manager.get_plugin_completions
                    )

                    # 找到最长的匹配命令前缀（支持多级命令）
                    matched_cmd = await loop.run_in_executor(
                        executor,
                        self._find_longest_matching_command,
                        _input_one_space,
                        plugin_completions_dict,
                    )

                    # 如果找到匹配的命令前缀，进行处理
                    if matched_cmd:
                        # 异步处理命令补全
                        completions_list = await loop.run_in_executor(
                            executor,
                            self._get_command_completions_list,
                            matched_cmd,
                            current_input,
                            plugin_completions_dict[matched_cmd],
                        )
                        for completion in completions_list:
                            yield completion
                        return
                else:
                    # 处理直接命令补全 - 异步获取所有匹配的命令
                    commands = await loop.run_in_executor(
                        executor,
                        self.plugin_manager.get_all_commands_with_prefix,
                        current_input,
                    )
                    for command in commands:
                        yield Completion(
                            command[len(current_input) :],
                            start_position=0,
                            display=command,
                        )
            finally:
                executor.shutdown(wait=False)

        # 异步获取基础补全器的补全
        if self.base_completer:
            # 如果基础补全器支持异步方法，优先使用
            if hasattr(self.base_completer, "get_completions_async"):
                async for completion in self.base_completer.get_completions_async(
                    document, complete_event
                ):
                    yield completion
            else:
                # 否则在线程池中运行同步方法
                loop = asyncio.get_event_loop()
                executor = ThreadPoolExecutor(max_workers=1)
                try:
                    completions = await loop.run_in_executor(
                        executor,
                        list,
                        self.base_completer.get_completions(document, complete_event),
                    )
                    for completion in completions:
                        yield completion
                finally:
                    executor.shutdown(wait=False)

    def _get_command_completions_list(self, command, current_input, completions):
        """获取命令补全列表（用于异步执行）"""
        return list(
            self._process_command_completions(command, current_input, completions)
        )
