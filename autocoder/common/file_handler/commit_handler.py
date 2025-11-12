import os
import uuid
from typing import Optional

from autocoder.common.international import get_message
from autocoder.common.ac_style_command_parser import create_config, parse_typed_query
from autocoder.common.printer import Printer
from autocoder.auto_coder_runner import (
    get_current_memory,
    get_current_files,
    get_last_yaml_file,
    convert_config_value,
    convert_yaml_config_to_str,
    convert_yaml_to_config,
    get_llm_friendly_package_docs,
    get_global_memory_file_paths,
    get_single_llm,
    auto_coder_main,
)
from autocoder.common.action_yml_file_manager import ActionYmlFileManager
from autocoder.common import git_utils


class CommitHandler:
    """处理代码提交相关的操作"""

    def __init__(self):
        self.printer = Printer()
        self._config = None

    def _create_config(self):
        """创建 commit 命令的类型化配置"""
        if self._config is None:
            self._config = (
                create_config()
                .collect_remainder("message")  # 收集剩余参数作为提交消息
                .command("no_diff")
                .max_args(0)  # 可能的未来扩展
                .build()
            )
        return self._config

    def handle_commit_command(self, query: Optional[str] = None) -> Optional[None]:
        """
        处理提交命令的主入口

        Args:
            query: 可选的查询字符串

        Returns:
            None: 表示处理了命令，应该返回而不继续执行
        """
        if query is None:
            query = ""

        # 检查是否是 /help 命令
        if query.strip() == "/help":
            print(get_message("commit_help_text"))
            return None

        # 执行提交逻辑
        return self._handle_commit(query)

    def _handle_commit(self, query: str) -> None:
        """处理提交逻辑"""
        memory = get_current_memory()
        conf = memory.get("conf", {})
        product_mode = conf.get("product_mode", "lite")

        def prepare_commit_yaml():
            auto_coder_main(["next", "chat_action"])

        prepare_commit_yaml()

        # 暂时注释掉的功能
        # no_diff = query.strip().startswith("/no_diff")
        # if no_diff:
        #     query = query.replace("/no_diff", "", 1).strip()

        latest_yaml_file = get_last_yaml_file("actions")

        memory = get_current_memory()
        conf = memory.get("conf", {})
        current_files = get_current_files()
        execute_file = None

        if latest_yaml_file:
            try:
                execute_file = os.path.join("actions", latest_yaml_file)
                yaml_config = self._prepare_yaml_config(conf, current_files)

                # 临时保存yaml文件，然后读取yaml文件，转换为args
                temp_yaml = os.path.join("actions", f"{uuid.uuid4()}.yml")
                try:
                    with open(temp_yaml, "w", encoding="utf-8") as f:
                        f.write(convert_yaml_config_to_str(yaml_config=yaml_config))
                    args = convert_yaml_to_config(temp_yaml)
                finally:
                    if os.path.exists(temp_yaml):
                        os.remove(temp_yaml)

                target_model = args.commit_model or args.model
                llm = get_single_llm(target_model, product_mode)
                self.printer.print_in_terminal(
                    "commit_generating", style="yellow", model_name=target_model
                )
                commit_message = ""

                try:
                    uncommitted_changes = git_utils.get_uncommitted_changes(".")
                    commit_message = git_utils.generate_commit_message.with_llm(
                        llm
                    ).run(uncommitted_changes, query=query)
                except Exception as e:
                    self.printer.print_in_terminal(
                        "commit_failed",
                        style="red",
                        error=str(e),
                        model_name=target_model,
                    )
                    return None

                # 更新 yaml 配置并保存
                yaml_config["query"] = commit_message
                yaml_content = convert_yaml_config_to_str(yaml_config=yaml_config)
                with open(os.path.join(execute_file), "w", encoding="utf-8") as f:
                    f.write(yaml_content)

                args.file = execute_file

                # 执行提交
                file_name = os.path.basename(execute_file)
                commit_result = git_utils.commit_changes(
                    ".", f"{commit_message}\nauto_coder_{file_name}"
                )

                # 更新相关文件
                self._update_yaml_files(args, commit_result)

                self.printer.print_in_terminal(
                    "commit_success",
                    style="green",
                    commit_message=commit_message,
                    changed_files_count=len(commit_result.changed_files),
                )

                # 打印最后的 Commit 信息
                git_utils.print_commit_info(commit_result)

            except Exception as e:
                self.printer.print_in_terminal(
                    "commit_failed", style="red", error=str(e)
                )
        else:
            self.printer.print_in_terminal("commit_no_yaml_file", style="yellow")

        return None

    def _prepare_yaml_config(self, conf: dict, current_files: list) -> dict:
        """准备 YAML 配置"""
        yaml_config = {
            "include_file": ["./base/base.yml"],
            "auto_merge": conf.get("auto_merge", "editblock"),
            "human_as_model": conf.get("human_as_model", "false") == "true",
            "skip_build_index": conf.get("skip_build_index", "true") == "true",
            "skip_confirm": conf.get("skip_confirm", "true") == "true",
            "silence": conf.get("silence", "true") == "true",
            "include_project_structure": conf.get("include_project_structure", "false")
            == "true",
        }

        for key, value in conf.items():
            converted_value = convert_config_value(key, value)
            if converted_value is not None:
                yaml_config[key] = converted_value

        yaml_config["urls"] = current_files + get_llm_friendly_package_docs(
            return_paths=True
        )

        if conf.get("enable_global_memory", "false") in ["true", "True", True]:
            yaml_config["urls"] += get_global_memory_file_paths()

        return yaml_config

    def _update_yaml_files(self, args, commit_result):
        """更新 YAML 文件"""
        action_yml_file_manager = ActionYmlFileManager(args.source_dir)
        action_file_name = os.path.basename(args.file)
        add_updated_urls = []
        for file in commit_result.changed_files:
            add_updated_urls.append(os.path.join(args.source_dir, file))

        args.add_updated_urls = add_updated_urls
        update_yaml_success = action_yml_file_manager.update_yaml_field(
            action_file_name, "add_updated_urls", add_updated_urls
        )

        if not update_yaml_success:
            self.printer.print_in_terminal("commit_yaml_update_failed", style="yellow")
