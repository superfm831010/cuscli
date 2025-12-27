from autocoder.common.project_scanner.compat import create_scanner_functions
from rich.console import Console
from rich.panel import Panel
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit import prompt
import os
import yaml
import json
import sys
import io
import uuid
import time
import byzerllm
import subprocess
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
from autocoder.common import AutoCoderArgs
from autocoder.common.autocoderargs_parser import AutoCoderArgsParser
from pydantic import BaseModel
from pathlib import Path
from autocoder.common.result_manager import ResultManager
from autocoder.version import __version__
from autocoder.auto_coder import main as auto_coder_main
from autocoder.utils import get_last_yaml_file
from autocoder.commands.auto_command import (
    CommandAutoTuner,
    AutoCommandRequest,
    CommandConfig,
    MemoryConfig,
)
from autocoder.common.v2.agent.agentic_edit import AgenticEditRequest
from autocoder.common.v2.agent.agentic_edit_types import (
    AgenticEditConversationConfig,
    ConversationAction,
)
from autocoder.common.conversations.get_conversation_manager import (
    get_conversation_manager,
)
from autocoder.index.symbols_utils import (
    SymbolType,
)
import platform
from rich.panel import Panel
from rich.table import Table
from copy import deepcopy

from rich.markdown import Markdown
from byzerllm.utils.nontext import Image
from autocoder.inner.agentic import RunAgentic

# 延迟导入git模块以避免启动异常
try:
    import git

    GIT_AVAILABLE = True
except ImportError:
    from loguru import logger

    logger.warning("Git module not available. Some git features will be disabled.")
    GIT_AVAILABLE = False
    git = None
from autocoder.common import git_utils
from autocoder.chat_auto_coder_lang import get_message, get_message_with_format
from autocoder.agent.auto_guess_query import AutoGuessQuery

# Do not remove these imports, they are exported to other modules e.g. chat_auto_coder.py
from autocoder.common.mcp_tools.server import get_mcp_server
from autocoder.common.memory_manager import get_global_memory_file_paths

from rich.panel import Panel
from rich.table import Table
from autocoder.common.international import get_message, get_message_with_format
from rich.prompt import Confirm
from autocoder.common.printer import Printer
from autocoder.utils.llms import get_single_llm
import importlib.resources as resources
from autocoder.common.printer import Printer
from autocoder.common.command_completer import MemoryConfig as CCMemoryModel
from autocoder.common.conf_validator import ConfigValidator
from autocoder.common.ac_style_command_parser import parse_query
from loguru import logger as global_logger
from autocoder.utils.project_structure import EnhancedFileAnalyzer
from autocoder.common import SourceCode
from autocoder.common.file_monitor import FileMonitor
from autocoder.common.command_file_manager import CommandManager
from autocoder.common.v2.agent.runner import (
    SdkRunner,
    TerminalRunner,
    FileBasedEventRunner,
)
from autocoder.completer import CommandCompleterV2
from autocoder.common.core_config import get_memory_manager, load_memory as _load_memory
from autocoder.common.global_cancel import global_cancel

# 对外API，用于第三方集成 auto-coder 使用。


class SymbolItem(BaseModel):
    symbol_name: str
    symbol_type: SymbolType
    file_name: str


class InitializeSystemRequest(BaseModel):
    product_mode: str
    skip_provider_selection: bool
    debug: bool
    quick: bool
    lite: bool
    pro: bool


if platform.system() == "Windows":
    from colorama import init

    init()


# Initialize memory and project root
project_root = os.getcwd()

# Initialize memory manager with project root
_memory_manager = get_memory_manager(project_root)

# Wrapper functions to sync global memory variable


def save_memory():
    """Save memory - compatibility function (no-op since MemoryManager handles persistence)"""
    # This function is kept for backward compatibility but does nothing
    # since MemoryManager automatically handles persistence
    raise NotImplementedError(
        "save_memory is not supported anymore, please use autocoder.common.core_config.memory_manager instead."
    )


def load_memory():
    """Load memory using MemoryManager"""
    return _load_memory()


def get_memory():
    """Get current memory"""
    return load_memory()


# Compatibility: base_persist_dir is now managed by memory manager
base_persist_dir = _memory_manager.base_persist_dir

defaut_exclude_dirs = [
    ".git",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".auto-coder",
]

commands = [
    "/add_files",
    "/remove_files",
    "/list_files",
    "/conf",
    "/coding",
    "/chat",
    "/ask",
    "/commit",
    "/rules",
    "/revert",
    "/index/query",
    "/index/build",
    "/index/export",
    "/index/import",
    "/exclude_files",
    "/help",
    "/shell",
    "/voice_input",
    "/exit",
    "/summon",
    "/mode",
    "/lib",
    "/design",
    "/mcp",
    "/models",
    "/auto",
    "/conf/export",
    "/conf/import",
    "/exclude_dirs",
    "/queue",
    "/workflow",
]


def load_tokenizer():
    from autocoder.rag.variable_holder import VariableHolder
    from tokenizers import Tokenizer

    try:
        tokenizer_path = str(resources.files("autocoder") / "data" / "tokenizer.json")
        VariableHolder.TOKENIZER_PATH = tokenizer_path
        VariableHolder.TOKENIZER_MODEL = Tokenizer.from_file(tokenizer_path)
    except FileNotFoundError:
        tokenizer_path = None


def configure_logger():
    # 设置日志目录和文件
    log_dir = os.path.join(project_root, ".auto-coder", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "auto-coder.log")

    # 配置全局日志
    # 默认情况下，所有日志都写入文件
    # 控制台上默认不输出任何日志，除非显式配置
    global_logger.configure(
        handlers=[
            {
                "sink": log_file,
                "level": "INFO",
                "rotation": "10 MB",
                "retention": "1 week",
                "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}",
            },
            {
                "sink": sys.stdout,
                "level": "INFO",
                "format": "{time:YYYY-MM-DD HH:mm:ss} | {name} | {message}",
                # 默认不打印任何日志到控制台
                "filter": lambda record: False,
            },
        ]
    )


def init_singleton_instances():
    # 初始化文件监控系统
    try:
        FileMonitor(project_root).start()
    except Exception as e:
        global_logger.error(f"Failed to start file monitor: {e}")
        global_logger.exception(e)

    # 初始化忽略文件管理器
    from autocoder.common.ignorefiles.ignore_file_utils import IgnoreFileManager

    _ = IgnoreFileManager(project_root=project_root)


def configure_project_type():
    from prompt_toolkit.lexers import PygmentsLexer
    from pygments.lexers.markup import MarkdownLexer
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.shortcuts import print_formatted_text
    from prompt_toolkit.styles import Style
    from html import escape

    style = Style.from_dict(
        {
            "info": "#ansicyan",
            "warning": "#ansiyellow",
            "input-area": "#ansigreen",
            "header": "#ansibrightyellow bold",
        }
    )

    def print_info(text):
        print_formatted_text(HTML(f"<info>{escape(text)}</info>"), style=style)

    def print_warning(text):
        print_formatted_text(HTML(f"<warning>{escape(text)}</warning>"), style=style)

    def print_header(text):
        print_formatted_text(HTML(f"<header>{escape(text)}</header>"), style=style)

    print_header(f"\n=== {get_message('project_type_config')} ===\n")
    print_info(get_message("project_type_supports"))
    print_info(get_message("language_suffixes"))
    print_info(get_message("predefined_types"))
    print_info(get_message("mixed_projects"))
    print_info(get_message("examples"))

    print_warning(f"{get_message('default_type')}\n")

    extensions = get_all_extensions(project_root) or "py"
    project_type = prompt(
        get_message("enter_project_type"), default=extensions, style=style
    ).strip()

    if project_type:
        configure(f"project_type:{project_type}", skip_print=True)
        configure("skip_build_index:true", skip_print=True)
        print_info(f"\n{get_message('project_type_set')} {project_type}")
    else:
        print_info(f"\n{get_message('using_default_type')}")

    print_warning(f"\n{get_message('change_setting_later')}:")
    print_warning("/conf project_type:<new_type>\n")

    return project_type


def get_all_extensions(directory: str = ".") -> str:
    """获取指定目录下所有文件的后缀名,多个按逗号分隔，并且带."""
    args = AutoCoderArgs(
        source_dir=directory,
        # 其他必要参数设置为默认值
        target_file="",
        git_url="",
        project_type="",
        conversation_prune_safe_zone_tokens=0,
    )

    analyzer = EnhancedFileAnalyzer(
        args=args,
        llm=None,  # 如果只是获取后缀名，可以不需要LLM
        config=None,  # 使用默认配置
    )

    # 获取分析结果
    analysis_result = analyzer.analyze_extensions()

    # 合并 code 和 config 的后缀名
    all_extensions = set(analysis_result["code"] + analysis_result["config"])

    # 转换为逗号分隔的字符串
    return ",".join(sorted(all_extensions))


def start():
    if os.environ.get("autocoder_auto_init", "true") in ["true", "True", "True", True]:
        configure_logger()
        init_singleton_instances()

    # conversation_manager = get_conversation_manager()
    # if not conversation_manager.get_current_conversation():
    #     # Format: yyyyMMdd-MM-ss-uuid
    #     current_time = datetime.datetime.now()
    #     time_str = current_time.strftime("%Y%m%d-%H-%M-%S")
    #     name = f"{time_str}-{str(uuid.uuid4())}"
    #     conversation_id = conversation_manager.create_new_conversation(name=name,description="")
    #     conversation_manager.set_current_conversation(conversation_id)


def stop():
    try:
        FileMonitor(project_root).stop()
    except Exception as e:
        global_logger.error(f"Failed to stop file monitor: {e}")
        global_logger.exception(e)


def initialize_system(args: InitializeSystemRequest):
    from autocoder.utils.model_provider_selector import ModelProviderSelector
    from autocoder.common.llms import LLMManager

    print(f"\n\033[1;34m{get_message('initializing')}\033[0m")

    first_time = [False]
    configure_success = [False]

    def print_status(message, status):
        if status == "success":
            print(f"\033[32m✓ {message}\033[0m")
        elif status == "warning":
            print(f"\033[33m! {message}\033[0m")
        elif status == "error":
            print(f"\033[31m✗ {message}\033[0m")
        else:
            print(f"  {message}")

        if not os.path.exists(base_persist_dir):
            os.makedirs(base_persist_dir, exist_ok=True)
            print_status(
                get_message_with_format("created_dir", path=base_persist_dir), "success"
            )

        if first_time[0]:
            configure("project_type:*", skip_print=True)
            configure_success[0] = True

        print_status(get_message("init_complete"), "success")

    init_project_if_required(target_dir=project_root, project_type="*")

    if not args.skip_provider_selection and first_time[0]:
        if args.product_mode == "lite":
            # 如果已经是配置过的项目，就无需再选择
            if first_time[0]:
                llm_manager = LLMManager()
                if not llm_manager.check_model_exists(
                    "v3_chat"
                ) or not llm_manager.check_model_exists("r1_chat"):
                    model_provider_selector = ModelProviderSelector()
                    model_provider_info = model_provider_selector.select_provider()
                    if model_provider_info is not None:
                        models_json_list = model_provider_selector.to_models_json(
                            model_provider_info
                        )
                        llm_manager.add_models(models_json_list)

        if args.product_mode == "pro":
            # Check if Ray is running
            print_status(get_message("checking_ray"), "")
            ray_status = subprocess.run(
                ["ray", "status"], capture_output=True, text=True
            )
            if ray_status.returncode != 0:
                print_status(get_message("ray_not_running"), "warning")
                try:
                    subprocess.run(["ray", "start", "--head"], check=True)
                    print_status(get_message("ray_start_success"), "success")
                except subprocess.CalledProcessError:
                    print_status(get_message("ray_start_fail"), "error")
                    return
            else:
                print_status(get_message("ray_running"), "success")

            # Check if deepseek_chat model is available
            print_status(get_message("checking_model"), "")
            try:
                result = subprocess.run(
                    ["easy-byzerllm", "chat", "v3_chat", "你好"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    print_status(get_message("model_available"), "success")
                    print_status(get_message("init_complete_final"), "success")
                    return
            except subprocess.TimeoutExpired:
                print_status(get_message("model_timeout"), "error")
            except subprocess.CalledProcessError:
                print_status(get_message("model_error"), "error")

            # If deepseek_chat is not available
            print_status(get_message("model_not_available"), "warning")
            api_key = prompt(HTML(f"<b>{get_message('enter_api_key')} </b>"))

            print_status(get_message("deploying_model").format("Deepseek官方"), "")
            deploy_cmd = [
                "byzerllm",
                "deploy",
                "--pretrained_model_type",
                "saas/openai",
                "--cpus_per_worker",
                "0.001",
                "--gpus_per_worker",
                "0",
                "--worker_concurrency",
                "1000",
                "--num_workers",
                "1",
                "--infer_params",
                f"saas.base_url=https://api.deepseek.com/v1 saas.api_key={api_key} saas.model=deepseek-chat",
                "--model",
                "v3_chat",
            ]

            try:
                subprocess.run(deploy_cmd, check=True)
                print_status(get_message("deploy_complete"), "success")
            except subprocess.CalledProcessError:
                print_status(get_message("deploy_fail"), "error")
                return

            deploy_cmd = [
                "byzerllm",
                "deploy",
                "--pretrained_model_type",
                "saas/reasoning_openai",
                "--cpus_per_worker",
                "0.001",
                "--gpus_per_worker",
                "0",
                "--worker_concurrency",
                "1000",
                "--num_workers",
                "1",
                "--infer_params",
                f"saas.base_url=https://api.deepseek.com/v1 saas.api_key={api_key} saas.model=deepseek-reasoner",
                "--model",
                "r1_chat",
            ]

            try:
                subprocess.run(deploy_cmd, check=True)
                print_status(get_message("deploy_complete"), "success")
            except subprocess.CalledProcessError:
                print_status(get_message("deploy_fail"), "error")
                return

            # Validate the deployment
            print_status(get_message("validating_deploy"), "")
            try:
                validation_result = subprocess.run(
                    ["easy-byzerllm", "chat", "v3_chat", "你好"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=True,
                )
                print_status(get_message("validation_success"), "success")
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                print_status(get_message("validation_fail"), "error")
                print_status(get_message("manual_start"), "warning")
                print_status("easy-byzerllm chat v3_chat 你好", "")

            print_status(get_message("init_complete_final"), "success")
            configure_success[0] = True

    if first_time[0] and args.product_mode == "pro" and configure_success[0]:
        configure(f"model:v3_chat", skip_print=True)

    if (
        first_time[0]
        and args.product_mode == "lite"
        and LLMManager().check_model_exists("v3_chat")
    ):
        configure(f"model:v3_chat", skip_print=True)


def convert_yaml_config_to_str(yaml_config):
    yaml_content = yaml.safe_dump(
        yaml_config,
        allow_unicode=True,
        default_flow_style=False,
        default_style=None,
    )
    return yaml_content


def convert_config_value(key, value):
    # 定义需要使用 token 解析的字段
    token_fields = {
        "conversation_prune_safe_zone_tokens",
        "context_prune_safe_zone_tokens",
        "context_prune_sliding_window_size",
        "context_prune_sliding_window_overlap",
        "rag_params_max_tokens",
        "rag_context_window_limit",
        "rag_duckdb_vector_dim",
        "rag_duckdb_query_top_k",
        "rag_emb_dim",
        "rag_emb_text_size",
        "hybrid_index_max_output_tokens",
        "data_cells_max_num",
    }

    field_info = AutoCoderArgs.model_fields.get(key)
    if field_info:
        # 对于需要 token 解析的字段，使用 AutoCoderArgsParser
        if key in token_fields:
            try:
                parser = AutoCoderArgsParser()
                return parser.parse_token_field(key, value)
            except Exception as e:
                print(
                    f"Warning: Failed to parse token field '{key}' with value '{value}': {e}"
                )
                # 如果解析失败，fallback 到原有逻辑
                pass

        # 原有的类型转换逻辑
        if isinstance(value, str) and value.lower() in ["true", "false"]:
            return value.lower() == "true"
        elif "float" in str(field_info.annotation):
            return float(value)
        elif "int" in str(field_info.annotation):
            return int(value)
        else:
            return value
    else:
        print(f"Invalid configuration key: {key}")
        return None


@contextmanager
def redirect_stdout():
    original_stdout = sys.stdout
    sys.stdout = f = io.StringIO()
    try:
        yield f
    finally:
        sys.stdout = original_stdout


def configure(conf: str, skip_print=True):
    printer = Printer()
    memory_manager = get_memory_manager()
    parts = conf.split(None, 1)
    if len(parts) == 2 and parts[0] in ["/drop", "/unset", "/remove"]:
        key = parts[1].strip()
        if memory_manager.has_config(key):
            memory_manager.delete_config(key)
            printer.print_in_terminal("config_delete_success", style="green", key=key)
        else:
            printer.print_in_terminal("config_not_found", style="yellow", key=key)
    else:
        parts = conf.split(":", 1)
        if len(parts) != 2:
            printer.print_in_terminal("config_invalid_format", style="red")
            return
        key, value = parts
        key = key.strip()
        value = value.strip()
        if not value:
            printer.print_in_terminal("config_value_empty", style="red")
            return
        product_mode = memory_manager.get_config("product_mode", None)
        if product_mode:
            ConfigValidator.validate(key, value, product_mode)
        memory_manager.set_config(key, value)
        if not skip_print:
            printer.print_in_terminal(
                "config_set_success", style="green", key=key, value=value
            )


# word_completer = WordCompleter(commands)


# Memory management functions are now imported from core_config module
# Helper functions to access memory without global variables
def get_current_memory():
    """Get current memory as dictionary for backward compatibility"""
    return get_memory()


def get_current_files():
    """Get current files list"""
    memory_manager = get_memory_manager()
    return memory_manager.get_current_files()


def set_current_files(files):
    """Set current files list"""
    memory_manager = get_memory_manager()
    memory_manager.set_current_files(files)


def get_file_groups():
    """Get file groups"""
    memory_manager = get_memory_manager()
    return memory_manager.get_file_groups()


def get_exclude_dirs():
    """Get exclude directories"""
    memory_manager = get_memory_manager()
    return memory_manager.get_exclude_dirs()


# 使用 project_scanner 模块创建兼容函数（供其他地方使用）
scanner_funcs = create_scanner_functions(
    project_root=project_root,
    default_exclude_dirs=defaut_exclude_dirs,
    get_extra_exclude_dirs_func=get_exclude_dirs,
)

# 导出兼容函数
get_all_file_names_in_project = scanner_funcs["get_all_file_names_in_project"]
get_all_file_in_project = scanner_funcs["get_all_file_in_project"]
get_all_file_in_project_with_dot = scanner_funcs["get_all_file_in_project_with_dot"]
get_all_dir_names_in_project = scanner_funcs["get_all_dir_names_in_project"]
find_files_in_project = scanner_funcs["find_files_in_project"]
get_symbol_list = scanner_funcs["get_symbol_list"]

# 直接创建 CommandCompleterV2，它内部会使用 project_scanner
completer = CommandCompleterV2(
    commands,
    memory_model=CCMemoryModel(
        get_memory_func=get_memory, save_memory_func=save_memory
    ),
    project_root=project_root,
)


def revert():
    result_manager = ResultManager()
    last_yaml_file = get_last_yaml_file("actions")
    if last_yaml_file:
        file_path = os.path.join("actions", last_yaml_file)

        with redirect_stdout() as output:
            auto_coder_main(["revert", "--file", file_path])
        s = output.getvalue()

        console = Console()
        panel = Panel(
            Markdown(s),
            title="Revert Result",
            border_style="green" if "Successfully reverted changes" in s else "red",
            padding=(1, 2),
            expand=False,
        )
        console.print(panel)

        if "Successfully reverted changes" in s:
            result_manager.append(
                content=s, meta={"action": "revert", "success": False, "input": {}}
            )
        else:
            result_manager.append(
                content=s, meta={"action": "revert", "success": False, "input": {}}
            )
    else:
        result_manager.append(
            content="No previous chat action found to revert.",
            meta={"action": "revert", "success": False, "input": {}},
        )


def _handle_post_commit_and_pr(post_commit: bool, pr: bool, query: str, args, llm):
    """
    处理 post_commit 和 PR 功能

    Args:
        post_commit: 是否执行 post_commit
        pr: 是否创建 PR
        query: 原始查询
        args: 配置参数
        llm: LLM 实例
    """
    printer = Printer()
    try:
        if post_commit:
            # 执行 post_commit 操作
            printer.print_in_terminal("post_commit_executing", style="blue")

            # 检查是否有未提交的更改
            uncommitted_changes = git_utils.get_uncommitted_changes(".")
            if uncommitted_changes:
                # 生成提交消息
                commit_message = git_utils.generate_commit_message.with_llm(llm).run(
                    uncommitted_changes
                )

                # 执行提交
                commit_result = git_utils.commit_changes(".", commit_message)
                git_utils.print_commit_info(commit_result=commit_result)
                printer.print_in_terminal(
                    "post_commit_success", style="green", message=commit_message
                )

                # 如果需要创建 PR，则继续处理
                if pr:
                    _create_pull_request(commit_result, query, llm)
            else:
                printer.print_in_terminal("post_commit_no_changes", style="yellow")

        elif pr:
            # 只创建 PR，不执行 post_commit
            # 获取最后一个 commit
            try:
                repo = git.Repo(".")
                last_commit = repo.head.commit

                # 创建一个模拟的 commit_result 对象
                class MockCommitResult:
                    def __init__(self, commit):
                        self.commit_hash = commit.hexsha
                        self.commit_message = commit.message.strip()
                        self.changed_files = []

                mock_commit_result = MockCommitResult(last_commit)
                _create_pull_request(mock_commit_result, query, llm)

            except Exception as e:
                printer.print_in_terminal(
                    "pr_get_last_commit_failed", style="red", error=str(e)
                )

    except Exception as e:
        printer.print_in_terminal("post_commit_pr_failed", style="red", error=str(e))


def init_project_if_required(target_dir: str, project_type: str):
    """
    如果项目没有初始化，则自动初始化项目

    Args:
        target_dir: 目标目录路径
    """

    # 确保目标目录是绝对路径
    if not os.path.isabs(target_dir):
        target_dir = os.path.abspath(target_dir)

    actions_dir = os.path.join(target_dir, "actions")
    auto_coder_dir = os.path.join(target_dir, ".auto-coder")

    # 检查是否已经初始化
    if os.path.exists(actions_dir) and os.path.exists(auto_coder_dir):
        return  # 已经初始化，无需再次初始化

    printer = Printer()

    try:
        # 创建必要的目录
        os.makedirs(actions_dir, exist_ok=True)
        os.makedirs(auto_coder_dir, exist_ok=True)

        # 导入并使用 create_actions 创建默认的 action 文件
        from autocoder.common.command_templates import create_actions

        create_actions(
            source_dir=target_dir,
            params={"project_type": project_type, "source_dir": target_dir},
        )

        # 初始化 git 仓库
        try:
            git_utils.init(target_dir)
        except Exception as e:
            global_logger.warning(f"Failed to initialize git repository: {e}")

        # 创建或更新 .gitignore 文件
        gitignore_path = os.path.join(target_dir, ".gitignore")
        gitignore_entries = [
            ".auto-coder/",
            "/actions/",
            "/output.txt",
            ".autocoderrules",
            ".autocodertools",
            ".autocodercommands",
            ".autocoderagents",
            ".autocoderlinters",
            ".autocoderworkflow",
        ]

        try:
            # 读取现有的 .gitignore 内容
            existing_entries = set()
            if os.path.exists(gitignore_path):
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    # 将现有内容按行分割并去除空白字符，转换为集合以便快速查找
                    existing_entries = {line.strip() for line in f if line.strip()}

            # 筛选出需要添加的新条目
            new_entries = [
                entry for entry in gitignore_entries if entry not in existing_entries
            ]

            # 如果有新条目需要添加，则写入文件
            if new_entries:
                with open(gitignore_path, "a", encoding="utf-8") as f:
                    for entry in new_entries:
                        f.write(f"\n{entry}")
        except Exception as e:
            global_logger.warning(f"Failed to update .gitignore: {e}")

        # 创建 .autocoderignore 文件
        try:
            autocoderignore_path = os.path.join(target_dir, ".autocoderignore")
            if not os.path.exists(autocoderignore_path):
                autocoderignore_content = "target\n"
                with open(autocoderignore_path, "w", encoding="utf-8") as f:
                    f.write(autocoderignore_content)
        except Exception as e:
            global_logger.warning(f"Failed to create .autocoderignore: {e}")

        configure(f"project_type:{project_type}", skip_print=True)
        global_logger.info(
            f"Successfully initialized auto-coder project in {target_dir}"
        )

    except Exception as e:
        global_logger.error(f"Failed to initialize project in {target_dir}: {e}")
        printer.print_in_terminal("init_project_error", style="red", error=str(e))


def _create_pull_request(commit_result, original_query: str, llm):
    """
    创建 Pull Request

    Args:
        commit_result: 提交结果对象
        original_query: 原始查询
        llm: LLM 实例
    """
    printer = Printer()
    console = Console()

    try:
        # 检查是否安装了 gh CLI
        gh_check = subprocess.run(["gh", "--version"], capture_output=True, text=True)
        if gh_check.returncode != 0:
            printer.print_in_terminal("pr_gh_not_installed", style="red")
            return

        # 检查是否已经登录 GitHub
        auth_check = subprocess.run(
            ["gh", "auth", "status"], capture_output=True, text=True
        )
        if auth_check.returncode != 0:
            printer.print_in_terminal("pr_gh_not_authenticated", style="red")
            return

        # 获取当前分支名
        repo = git.Repo(".")
        current_branch = repo.active_branch.name

        # 如果在 main/master 分支，创建新分支
        if current_branch in ["main", "master"]:
            # 生成新分支名
            import re

            branch_name = re.sub(r"[^a-zA-Z0-9\-_]", "-", original_query.lower())
            branch_name = f"auto-coder-{branch_name[:30]}-{int(time.time())}"

            # 创建并切换到新分支
            new_branch = repo.create_head(branch_name)
            new_branch.checkout()
            current_branch = branch_name

            printer.print_in_terminal(
                "pr_created_branch", style="blue", branch=branch_name
            )

        # 推送当前分支到远程
        try:
            origin = repo.remotes.origin
            origin.push(current_branch)
            printer.print_in_terminal(
                "pr_pushed_branch", style="blue", branch=current_branch
            )
        except Exception as e:
            printer.print_in_terminal("pr_push_failed", style="red", error=str(e))
            return

        # 生成 PR 标题和描述
        pr_title, pr_body = _generate_pr_content(commit_result, original_query, llm)

        # 创建 PR
        pr_cmd = [
            "gh",
            "pr",
            "create",
            "--title",
            pr_title,
            "--body",
            pr_body,
            "--head",
            current_branch,
        ]

        pr_result = subprocess.run(pr_cmd, capture_output=True, text=True)

        if pr_result.returncode == 0:
            pr_url = pr_result.stdout.strip()
            printer.print_in_terminal("pr_created_success", style="green", url=pr_url)

            # 显示 PR 信息
            console.print(
                Panel(
                    f"[bold green]Pull Request Created Successfully![/bold green]\n\n"
                    f"[bold]Title:[/bold] {pr_title}\n"
                    f"[bold]URL:[/bold] {pr_url}\n"
                    f"[bold]Branch:[/bold] {current_branch}",
                    title="🎉 Pull Request",
                    border_style="green",
                )
            )
        else:
            printer.print_in_terminal(
                "pr_creation_failed", style="red", error=pr_result.stderr
            )

    except Exception as e:
        printer.print_in_terminal("pr_creation_error", style="red", error=str(e))


@byzerllm.prompt()
def _generate_pr_content(commit_result, original_query: str, llm) -> tuple:
    """
    生成 PR 标题和描述

    根据提交信息和原始查询生成合适的 PR 标题和描述。

    Args:
        commit_result: 提交结果，包含 commit_message 和 changed_files
        original_query: 用户的原始查询请求

    Returns:
        tuple: (pr_title, pr_body) PR标题和描述内容

    请生成简洁明了的 PR 标题（不超过72字符）和详细的描述内容。
    标题应该概括主要变更，描述应该包含：
    1. 变更的背景和目的
    2. 主要修改内容
    3. 影响的文件（如果有的话）

    提交信息：{{ commit_result.commit_message }}
    原始需求：{{ original_query }}
    {% if commit_result.changed_files %}
    修改的文件：
    {% for file in commit_result.changed_files %}
    - {{ file }}
    {% endfor %}
    {% endif %}
    """

    # 这个函数会被 byzerllm 装饰器处理，返回 LLM 生成的内容
    # 实际实现会在运行时由装饰器处理
    pass


# 实际的 PR 内容生成函数
def _generate_pr_content(commit_result, original_query: str, llm):
    """
    生成 PR 标题和描述的实际实现
    """
    try:
        # 使用 LLM 生成 PR 内容
        prompt = f"""
根据以下信息生成 Pull Request 的标题和描述：

提交信息：{getattr(commit_result, 'commit_message', 'Auto-generated commit')}
原始需求：{original_query}
修改的文件：{getattr(commit_result, 'changed_files', [])}

请生成：
1. 简洁的 PR 标题（不超过72字符）
2. 详细的 PR 描述，包含变更背景、主要修改内容等

格式要求：
TITLE: [标题内容]
BODY: [描述内容]
"""

        response = llm.chat([{"role": "user", "content": prompt}])

        # 解析响应
        lines = response.split("\n")
        title = ""
        body = ""

        for line in lines:
            if line.startswith("TITLE:"):
                title = line.replace("TITLE:", "").strip()
            elif line.startswith("BODY:"):
                body = line.replace("BODY:", "").strip()
            elif body:  # 如果已经开始收集 body，继续添加后续行
                body += "\n" + line

        # 如果解析失败，使用默认值
        if not title:
            title = f"Auto-coder: {original_query[:50]}..."
        if not body:
            body = f"This PR was automatically generated by Auto-coder.\n\nOriginal request: {original_query}"

        return title, body

    except Exception as e:
        # 如果 LLM 生成失败，使用默认值
        title = f"Auto-coder: {original_query[:50]}..."
        body = f"This PR was automatically generated by Auto-coder.\n\nOriginal request: {original_query}\n\nCommit: {getattr(commit_result, 'commit_message', 'Auto-generated commit')}"
        return title, body


def add_files(args: List[str]):
    """
    处理文件添加命令，使用 AddFilesHandler 进行统一处理

    Args:
        args: 命令参数列表
    """
    from autocoder.common.file_handler import AddFilesHandler

    handler = AddFilesHandler()
    handler.handle_add_files_command(args)


def remove_files(file_names: List[str]):
    """
    处理文件删除命令，使用 RemoveFilesHandler 进行统一处理

    Args:
        file_names: 文件名列表或模式列表
    """
    from autocoder.common.file_handler import RemoveFilesHandler

    handler = RemoveFilesHandler()
    handler.handle_remove_files_command(file_names)


def ask(query: str):
    memory_manager = get_memory_manager()
    conf = memory_manager.get_all_config()
    yaml_config = {
        "include_file": ["./base/base.yml"],
    }
    yaml_config["query"] = query

    if "project_type" in conf:
        yaml_config["project_type"] = conf["project_type"]

    if "model" in conf:
        yaml_config["model"] = conf["model"]

    if "index_model" in conf:
        yaml_config["index_model"] = conf["index_model"]

    if "vl_model" in conf:
        yaml_config["vl_model"] = conf["vl_model"]

    if "code_model" in conf:
        yaml_config["code_model"] = conf["code_model"]

    if "product_mode" in conf:
        yaml_config["product_mode"] = conf["product_mode"]

    yaml_content = convert_yaml_config_to_str(yaml_config=yaml_config)

    execute_file = os.path.join("actions", f"{uuid.uuid4()}.yml")

    with open(os.path.join(execute_file), "w", encoding="utf-8") as f:
        f.write(yaml_content)

    def execute_ask():
        auto_coder_main(["agent", "project_reader", "--file", execute_file])

    try:
        execute_ask()
    finally:
        os.remove(execute_file)


def get_llm_friendly_package_docs(
    package_name: Optional[str] = None, return_paths: bool = False
) -> List[str]:
    """
    Get LLM friendly package documentation using the new AC module system

    Args:
        package_name: Specific package name to get docs for, None for all packages
        return_paths: If True, return file paths; if False, return file contents

    Returns:
        List of documentation content or file paths
    """
    from autocoder.common.llm_friendly_package import get_package_manager

    package_manager = get_package_manager()
    return package_manager.get_docs(package_name, return_paths)


def convert_yaml_to_config(yaml_file: str):
    from autocoder.auto_coder import AutoCoderArgs, load_include_files, Template

    args = AutoCoderArgs()
    with open(yaml_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        config = load_include_files(config, yaml_file)
        for key, value in config.items():
            if key != "file":  # 排除 --file 参数本身
                # key: ENV {{VARIABLE_NAME}}
                if isinstance(value, str) and value.startswith("ENV"):
                    template = Template(value.removeprefix("ENV").strip())
                    value = template.render(os.environ)
                setattr(args, key, value)
    return args


def mcp(query: str):
    """
    处理MCP命令，使用 McpHandler 进行统一处理

    Args:
        query: 查询字符串
    """
    from autocoder.common.file_handler import McpHandler

    handler = McpHandler()
    handler.handle_mcp_command(query)


def code_next(query: str):
    memory = get_current_memory()
    conf = memory.get("conf", {})
    yaml_config = {
        "include_file": ["./base/base.yml"],
        "auto_merge": conf.get("auto_merge", "editblock"),
        "human_as_model": conf.get("human_as_model", "false") == "true",
        "skip_build_index": conf.get("skip_build_index", "true") == "true",
        "skip_confirm": conf.get("skip_confirm", "true") == "true",
        "silence": conf.get("silence", "true") == "true",
        "include_project_structure": conf.get("include_project_structure", "false")
        == "true",
        "exclude_files": memory.get("exclude_files", []),
    }
    for key, value in conf.items():
        converted_value = convert_config_value(key, value)
        if converted_value is not None:
            yaml_config[key] = converted_value

    temp_yaml = os.path.join("actions", f"{uuid.uuid4()}.yml")
    try:
        with open(temp_yaml, "w", encoding="utf-8") as f:
            f.write(convert_yaml_config_to_str(yaml_config=yaml_config))
        args = convert_yaml_to_config(temp_yaml)
    finally:
        if os.path.exists(temp_yaml):
            os.remove(temp_yaml)

    product_mode = conf.get("product_mode", "lite")
    llm = get_single_llm(args.chat_model or args.model, product_mode=product_mode)

    auto_guesser = AutoGuessQuery(llm=llm, project_dir=os.getcwd(), skip_diff=True)

    predicted_tasks = auto_guesser.predict_next_tasks(
        5, is_human_as_model=args.human_as_model
    )

    if not predicted_tasks:
        console = Console()
        console.print(Panel("No task predictions available", style="yellow"))
        return

    console = Console()

    # Create main panel for all predicted tasks
    table = Table(show_header=True, header_style="bold magenta", show_lines=True)
    table.add_column("Priority", style="cyan", width=8)
    table.add_column("Task Description", style="green", width=40, overflow="fold")
    table.add_column("Files", style="yellow", width=30, overflow="fold")
    table.add_column("Reason", style="blue", width=30, overflow="fold")
    table.add_column("Dependencies", style="magenta", width=30, overflow="fold")

    for task in predicted_tasks:
        # Format file paths to be more readable
        file_list = "\n".join([os.path.relpath(f, os.getcwd()) for f in task.urls])

        # Format dependencies to be more readable
        dependencies = (
            "\n".join(task.dependency_queries) if task.dependency_queries else "None"
        )

        table.add_row(
            str(task.priority), task.query, file_list, task.reason, dependencies
        )

    console.print(
        Panel(
            table,
            title="[bold]Predicted Next Tasks[/bold]",
            border_style="blue",
            padding=(1, 2),  # Add more horizontal padding
        )
    )


def commit(query: Optional[str] = None):
    """
    处理提交命令，使用 CommitHandler 进行统一处理

    Args:
        query: 可选的提交消息或命令
    """
    from autocoder.common.file_handler import CommitHandler

    handler = CommitHandler()
    handler.handle_commit_command(query)


def coding(query: str, cancel_token=None):
    """
    处理代码生成命令，使用 CodingHandler 进行统一处理

    Args:
        query: 代码生成查询字符串
        cancel_token: 可选的取消令牌
    """
    from autocoder.common.file_handler import CodingHandler

    handler = CodingHandler()
    handler.handle_coding_command(query, cancel_token)


def rules(query: str):
    from autocoder.chat.rules_command import handle_rules_command

    result = handle_rules_command(query, coding_func=coding)
    # 只有当结果不为空时才打印，避免重复输出
    if result and result.strip():
        print(result)
    completer.refresh_files()


@byzerllm.prompt()
def code_review(query: str) -> str:
    """
    掐面提供了上下文，对代码进行review，参考如下检查点。
    1. 有没有调用不符合方法，类的签名的调用，包括对第三方类，模块，方法的检查（如果上下文提供了这些信息）
    2. 有没有未声明直接使用的变量，方法，类
    3. 有没有明显的语法错误
    4. 如果是python代码，检查有没有缩进方面的错误
    5. 如果是python代码，检查是否 try 后面缺少 except 或者 finally
    {% if query %}
    6. 用户的额外的检查需求：{{ query }}
    {% endif %}

    如果用户的需求包含了@一个文件名 或者 @@符号， 那么重点关注这些文件或者符号（函数，类）进行上述的review。
    review 过程中严格遵循上述的检查点，不要遗漏，没有发现异常的点直接跳过，只对发现的异常点，给出具体的修改后的代码。
    """
    return {}  # type: ignore


def chat(query: str):
    """
    处理聊天命令，使用 ChatHandler 进行统一处理

    Args:
        query: 聊天查询字符串
    """
    from autocoder.common.file_handler import ChatHandler

    handler = ChatHandler()
    handler.handle_chat_command(query)


def summon(query: str):
    memory = get_current_memory()
    conf = memory.get("conf", {})
    current_files = get_current_files()

    file_contents = []
    for file in current_files:
        if os.path.exists(file):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
                    s = f"##File: {file}\n{content}\n\n"
                    file_contents.append(s)
            except Exception as e:
                print(f"Failed to read file: {file}. Error: {str(e)}")

    all_file_content = "".join(file_contents)

    yaml_config = {
        "include_file": ["./base/base.yml"],
    }
    yaml_config["query"] = query
    yaml_config["context"] = json.dumps(
        {"file_content": all_file_content}, ensure_ascii=False
    )

    if "emb_model" in conf:
        yaml_config["emb_model"] = conf["emb_model"]

    if "vl_model" in conf:
        yaml_config["vl_model"] = conf["vl_model"]

    if "code_model" in conf:
        yaml_config["code_model"] = conf["code_model"]

    if "model" in conf:
        yaml_config["model"] = conf["model"]

    if "product_mode" in conf:
        yaml_config["product_mode"] = conf["product_mode"]

    yaml_content = convert_yaml_config_to_str(yaml_config=yaml_config)

    execute_file = os.path.join("actions", f"{uuid.uuid4()}.yml")

    with open(os.path.join(execute_file), "w", encoding="utf-8") as f:
        f.write(yaml_content)

    def execute_summon():
        auto_coder_main(["agent", "auto_tool", "--file", execute_file])

    try:
        execute_summon()
    finally:
        os.remove(execute_file)


def design(query: str):
    memory = get_current_memory()
    conf = memory.get("conf", {})
    yaml_config = {
        "include_file": ["./base/base.yml"],
    }

    if query.strip().startswith("/svg"):
        query = query.replace("/svg", "", 1).strip()
        yaml_config["agent_designer_mode"] = "svg"
    elif query.strip().startswith("/sd"):
        query = query.replace("/svg", "", 1).strip()
        yaml_config["agent_designer_mode"] = "sd"
    elif query.strip().startswith("/logo"):
        query = query.replace("/logo", "", 1).strip()
        yaml_config["agent_designer_mode"] = "logo"
    else:
        yaml_config["agent_designer_mode"] = "svg"

    yaml_config["query"] = query

    if "model" in conf:
        yaml_config["model"] = conf["model"]

    if "designer_model" in conf:
        yaml_config["designer_model"] = conf["designer_model"]

    if "sd_model" in conf:
        yaml_config["sd_model"] = conf["sd_model"]

    yaml_content = convert_yaml_config_to_str(yaml_config=yaml_config)

    execute_file = os.path.join("actions", f"{uuid.uuid4()}.yml")

    with open(os.path.join(execute_file), "w", encoding="utf-8") as f:
        f.write(yaml_content)

    def execute_design():
        auto_coder_main(["agent", "designer", "--file", execute_file])

    try:
        execute_design()
    finally:
        os.remove(execute_file)


def active_context(query: str):
    """
    处理活动上下文命令，使用 ActiveContextHandler 进行统一处理

    Args:
        query: 命令参数，例如 "list" 列出所有任务
    """
    from autocoder.common.file_handler import ActiveContextHandler

    handler = ActiveContextHandler()
    handler.handle_active_context_command(query)


def voice_input():
    memory = get_current_memory()
    conf = memory.get("conf", {})
    yaml_config = {
        "include_file": ["./base/base.yml"],
    }

    if "voice2text_model" not in conf:
        print(
            "Please set voice2text_model in configuration. /conf voice2text_model:<model>"
        )
        return

    yaml_config["voice2text_model"] = conf["voice2text_model"]
    yaml_content = convert_yaml_config_to_str(yaml_config=yaml_config)

    execute_file = os.path.join("actions", f"{uuid.uuid4()}.yml")

    with open(os.path.join(execute_file), "w", encoding="utf-8") as f:
        f.write(yaml_content)

    def execute_voice2text_command():
        auto_coder_main(["agent", "voice2text", "--file", execute_file])

    try:
        execute_voice2text_command()
        with open(
            os.path.join(".auto-coder", "exchange.txt"), "r", encoding="utf-8"
        ) as f:
            return f.read()
    finally:
        os.remove(execute_file)


def generate_shell_command(input_text):
    memory = get_current_memory()
    conf = memory.get("conf", {})
    yaml_config = {
        "include_file": ["./base/base.yml"],
    }

    if "model" in conf:
        yaml_config["model"] = conf["model"]

    yaml_config["query"] = input_text

    yaml_content = convert_yaml_config_to_str(yaml_config=yaml_config)

    execute_file = os.path.join("actions", f"{uuid.uuid4()}.yml")

    with open(os.path.join(execute_file), "w", encoding="utf-8") as f:
        f.write(yaml_content)

    try:
        auto_coder_main(["agent", "generate_command", "--file", execute_file])
        with open(
            os.path.join(".auto-coder", "exchange.txt"), "r", encoding="utf-8"
        ) as f:
            shell_script = f.read()
        result_manager = ResultManager()
        result_manager.add_result(
            content=shell_script,
            meta={"action": "generate_shell_command", "input": {"query": input_text}},
        )
        return shell_script
    finally:
        os.remove(execute_file)


def manage_models(query: str):
    """
    处理模型管理命令，使用 ModelsHandler 进行统一处理

    Args:
        query: 查询字符串，支持多种模型管理子命令
    """
    from autocoder.common.file_handler import ModelsHandler

    handler = ModelsHandler()
    handler.handle_models_command(query)


def exclude_dirs(dir_names: List[str]):
    memory_manager = get_memory_manager()
    new_dirs = memory_manager.add_exclude_dirs(dir_names)

    if new_dirs:
        print(f"Added exclude dirs: {new_dirs}")
        exclude_files(",".join([f"regex://.*/{d}/*." for d in new_dirs]))
    else:
        print("All specified dirs are already in the exclude list.")
    completer.refresh_files()


def exclude_files(query: str):
    memory_manager = get_memory_manager()
    result_manager = ResultManager()
    printer = Printer()

    if "/list" in query:
        query = query.replace("/list", "", 1).strip()
        existing_file_patterns = memory_manager.get_exclude_files()
        console = Console()
        # 打印表格
        table = Table(title="Exclude Files")
        table.add_column("File Pattern")
        for file_pattern in existing_file_patterns:
            table.add_row(file_pattern)
        console.print(table)
        result_manager.add_result(
            content=f"Exclude files: {existing_file_patterns}",
            meta={"action": "exclude_files", "input": {"query": query}},
        )
        return

    if "/drop" in query:
        query = query.replace("/drop", "", 1).strip()
        removed_patterns = memory_manager.remove_exclude_files([query.strip()])
        completer.refresh_files()
        result_manager.add_result(
            content=f"Dropped exclude files: {removed_patterns}",
            meta={"action": "exclude_files", "input": {"query": query}},
        )
        return

    new_file_patterns = query.strip().split(",")

    # Validate patterns
    for file_pattern in new_file_patterns:
        if not file_pattern.startswith("regex://"):
            result_manager.add_result(
                content=printer.get_message_from_key_with_format(
                    "invalid_file_pattern", file_pattern=file_pattern
                ),
                meta={"action": "exclude_files", "input": {"query": file_pattern}},
            )
            raise ValueError(
                printer.get_message_from_key_with_format(
                    "invalid_file_pattern", file_pattern=file_pattern
                )
            )

    # Add new patterns
    new_patterns_added = memory_manager.add_exclude_files(new_file_patterns)

    if new_patterns_added:
        result_manager.add_result(
            content=f"Added exclude files: {new_patterns_added}",
            meta={"action": "exclude_files", "input": {"query": new_patterns_added}},
        )
        print(f"Added exclude files: {new_patterns_added}")
    else:
        result_manager.add_result(
            content=f"All specified files are already in the exclude list.",
            meta={"action": "exclude_files", "input": {"query": new_file_patterns}},
        )
        print("All specified files are already in the exclude list.")


def index_build():
    memory = get_memory()
    conf = memory.get("conf", {})
    yaml_config = {
        "include_file": ["./base/base.yml"],
        "exclude_files": memory.get("exclude_files", []),
    }

    for key, value in conf.items():
        converted_value = convert_config_value(key, value)
        if converted_value is not None:
            yaml_config[key] = converted_value

    yaml_content = convert_yaml_config_to_str(yaml_config=yaml_config)
    yaml_file = os.path.join("actions", f"{uuid.uuid4()}.yml")

    with open(yaml_file, "w", encoding="utf-8") as f:
        f.write(yaml_content)
    try:
        auto_coder_main(["index", "--file", yaml_file])
        completer.refresh_files()
    finally:
        os.remove(yaml_file)


def get_final_config() -> AutoCoderArgs:
    memory_manager = get_memory_manager()
    conf = memory_manager.get_all_config()
    yaml_config = {
        "include_file": ["./base/base.yml"],
        "auto_merge": conf.get("auto_merge", "editblock"),
        "human_as_model": conf.get("human_as_model", "false") == "true",
        "skip_build_index": conf.get("skip_build_index", "true") == "true",
        "skip_confirm": conf.get("skip_confirm", "true") == "true",
        "silence": conf.get("silence", "true") == "true",
        "include_project_structure": conf.get("include_project_structure", "false")
        == "true",
        "exclude_files": memory_manager.get_exclude_files(),
    }
    for key, value in conf.items():
        converted_value = convert_config_value(key, value)
        if converted_value is not None:
            yaml_config[key] = converted_value

    temp_yaml = os.path.join("actions", f"{uuid.uuid4()}.yml")
    try:
        with open(temp_yaml, "w", encoding="utf-8") as f:
            f.write(convert_yaml_config_to_str(yaml_config=yaml_config))
        args = convert_yaml_to_config(temp_yaml)
    finally:
        if os.path.exists(temp_yaml):
            os.remove(temp_yaml)
    return args


def help(query: str):
    from autocoder.common.auto_configure import (
        ConfigAutoTuner,
        MemoryConfig,
        AutoConfigRequest,
    )

    memory_manager = get_memory_manager()
    memory = get_memory()
    args = get_final_config()
    product_mode = memory_manager.get_config("product_mode", "lite")
    llm = get_single_llm(args.chat_model or args.model, product_mode=product_mode)
    auto_config_tuner = ConfigAutoTuner(
        args=args,
        llm=llm,
        memory_config=MemoryConfig(memory=memory, save_memory_func=save_memory),
    )
    auto_config_tuner.tune(AutoConfigRequest(query=query))


def index_export(path: str):
    from autocoder.common.index_import_export import export_index
    from autocoder.common.printer import Printer

    printer = Printer()
    project_root = os.getcwd()
    if export_index(project_root, path):
        printer.print_in_terminal("index_export_success", path=path)
    else:
        printer.print_in_terminal("index_export_fail", path=path)


def index_import(path: str):
    from autocoder.common.index_import_export import import_index
    from autocoder.common.printer import Printer

    printer = Printer()
    project_root = os.getcwd()
    if import_index(project_root, path):
        printer.print_in_terminal("index_import_success", path=path)
    else:
        printer.print_in_terminal("index_import_fail", path=path)


def index_query(query: str):
    from autocoder.index.entry import build_index_and_filter_files
    from autocoder.pyproject import PyProject
    from autocoder.tsproject import TSProject
    from autocoder.suffixproject import SuffixProject
    from autocoder.default_project import DefaultProject

    config = get_final_config()
    config.query = query
    config.skip_filter_index = False
    llm = get_single_llm(
        config.chat_model or config.model, product_mode=config.product_mode
    )

    if config.project_type == "ts":
        pp = TSProject(args=config, llm=llm)
    elif config.project_type == "py":
        pp = PyProject(args=config, llm=llm)
    elif not config.project_type or config.project_type == "*":
        pp = DefaultProject(args=config, llm=llm, file_filter=None)
    else:
        pp = SuffixProject(args=config, llm=llm, file_filter=None)
    pp.run()
    sources = pp.sources
    source_code_list = build_index_and_filter_files(
        llm=llm, args=config, sources=sources
    )
    return source_code_list


def list_files():
    """
    处理文件列表命令，使用 ListFilesHandler 进行统一处理
    """
    from autocoder.common.file_handler import ListFilesHandler

    handler = ListFilesHandler()
    handler.handle_list_files_command()


def gen_and_exec_shell_command(query: str):
    printer = Printer()
    console = Console()
    # Generate the shell script
    shell_script = generate_shell_command(query)

    # Ask for confirmation using rich
    if Confirm.ask(
        printer.get_message_from_key("confirm_execute_shell_script"), default=False
    ):
        execute_shell_command(shell_script)
    else:
        console.print(
            Panel(
                printer.get_message_from_key("shell_script_not_executed"),
                border_style="yellow",
            )
        )


def lib_command(args: List[str]):
    """
    处理库管理命令，使用 LibHandler 进行统一处理

    Args:
        args: 命令参数列表
    """
    from autocoder.common.file_handler import LibHandler

    handler = LibHandler()
    handler.handle_lib_command(args)


def execute_shell_command(command: str):
    from autocoder.common.shells import execute_shell_command as shell_exec

    shell_exec(command)


def conf_export(path: str):
    from autocoder.common.conf_import_export import export_conf

    export_conf(os.getcwd(), path)


def conf_import(path: str):
    from autocoder.common.conf_import_export import import_conf

    import_conf(os.getcwd(), path)


def generate_new_yaml(query: str):
    memory = get_memory()
    conf = memory.get("conf", {})
    current_files = memory.get("current_files", {}).get("files", [])
    auto_coder_main(["next", "chat_action"])
    latest_yaml_file = get_last_yaml_file("actions")
    if latest_yaml_file:
        yaml_config = {
            "include_file": ["./base/base.yml"],
            "auto_merge": conf.get("auto_merge", "editblock"),
            "human_as_model": conf.get("human_as_model", "false") == "true",
            "skip_build_index": conf.get("skip_build_index", "true") == "true",
            "skip_confirm": conf.get("skip_confirm", "true") == "true",
            "silence": conf.get("silence", "true") == "true",
            "include_project_structure": conf.get("include_project_structure", "false")
            == "true",
            "exclude_files": memory.get("exclude_files", []),
        }
        yaml_config["context"] = ""
        for key, value in conf.items():
            converted_value = convert_config_value(key, value)
            if converted_value is not None:
                yaml_config[key] = converted_value

        yaml_config["urls"] = current_files + get_llm_friendly_package_docs(
            return_paths=True
        )
        # handle image
        v = Image.convert_image_paths_from(query)
        yaml_config["query"] = v

        yaml_content = convert_yaml_config_to_str(yaml_config=yaml_config)

        execute_file = os.path.join("actions", latest_yaml_file)
        with open(os.path.join(execute_file), "w", encoding="utf-8") as f:
            f.write(yaml_content)
        return execute_file, convert_yaml_to_config(execute_file)


def handle_conversation_actions(conversation_config) -> bool:
    """
    处理对话列表和创建新对话的操作

    Args:
        conversation_config: 对话配置对象

    Returns:
        bool: 如果处理了特殊操作（LIST或NEW without input）返回True，否则返回False
    """
    if not conversation_config:
        return False

    console = Console()

    # 处理LIST操作
    if conversation_config.action == ConversationAction.LIST:
        conversation_manager = get_conversation_manager()
        conversations = conversation_manager.list_conversations()
        # 只保留 conversation_id 和 name 字段
        filtered_conversations = []
        for conv in conversations:
            filtered_conv = {
                "conversation_id": conv.get("conversation_id"),
                "name": conv.get("name"),
            }
            filtered_conversations.append(filtered_conv)

        # 格式化 JSON 输出，使用 JSON 格式渲染而不是 Markdown
        json_str = json.dumps(filtered_conversations, ensure_ascii=False, indent=4)
        console.print(
            Panel(
                json_str,
                title="🏁 Task Completion",
                border_style="green",
                title_align="left",
            )
        )
        return True

    # 处理NEW操作且没有用户输入
    if (
        conversation_config.action == ConversationAction.NEW
        and not conversation_config.query.strip()
    ):
        conversation_manager = get_conversation_manager()
        conversation_id = conversation_manager.create_conversation(
            name=conversation_config.query or "New Conversation",
            description=conversation_config.query or "New Conversation",
        )
        conversation_manager.set_current_conversation(conversation_id)
        conversation_message = f"New conversation created: {conversation_manager.get_current_conversation_id()}"

        # 使用safe console print的简单版本
        try:
            console.print(
                Panel(
                    Markdown(conversation_message),
                    title="🏁 Task Completion",
                    border_style="green",
                    title_align="left",
                )
            )
        except Exception:
            # fallback to plain text
            safe_content = conversation_message.replace("[", "\\[").replace("]", "\\]")
            console.print(
                Panel(
                    safe_content,
                    title="🏁 Task Completion",
                    border_style="green",
                    title_align="left",
                )
            )
        return True

    return False


# used in /auto command in terminal
def run_agentic(
    query: str,
    cancel_token: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
):
    """处理/auto指令"""
    agentic = RunAgentic()
    return agentic.run(query, cancel_token, conversation_history)


def run_agentic_filter(query: str, cancel_token: Optional[str] = None):
    """处理/auto指令"""
    agentic = RunAgentic()
    return agentic.filter(query, cancel_token)


# used in autocoder/sdk/core/bridge.py
def run_auto_command(
    query: str,
    pre_commit: bool = False,
    post_commit: bool = False,
    pr: bool = False,
    extra_args: Dict[str, Any] = {},
    cancel_token: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    system_prompt: Optional[str] = None,
    conversation_action: ConversationAction = ConversationAction.NEW,
    conversation_id: Optional[str] = None,
    is_sub_agent: bool = False,
):
    """处理/auto指令"""
    agentic = RunAgentic()
    for event in agentic.run_with_events(
        query,
        pre_commit=pre_commit,
        post_commit=post_commit,
        pr=pr,
        extra_args=extra_args,
        cancel_token=cancel_token,
        conversation_history=conversation_history,
        system_prompt=system_prompt,
        conversation_action=conversation_action,
        conversation_id=conversation_id,
        is_sub_agent=is_sub_agent,
    ):
        yield event


def run_workflow(
    workflow: str,
    prompt: Optional[str] = None,
    model: Optional[str] = None,
    vars_override: Optional[Dict[str, Any]] = None,
):
    """
    运行指定的 workflow

    Args:
        workflow: workflow 名称或文件路径
        prompt: 可选的提示内容，会注入到 workflow 的 vars.query 中
        model: 可选的模型名称，覆盖 workflow 配置中的模型
        vars_override: 可选的变量覆盖字典

    Returns:
        WorkflowResult: workflow 执行结果
    """
    from autocoder.workflow_agents import run_workflow_from_yaml
    from autocoder.events.event_manager_singleton import gengerate_event_file_path

    # 准备变量覆盖
    final_vars = dict(vars_override or {})
    if prompt:
        final_vars["query"] = prompt

    # 获取当前目录作为 source_dir
    source_dir = str(Path.cwd())

    # 调用 workflow 运行器
    result = run_workflow_from_yaml(
        yaml_path=workflow,
        source_dir=source_dir,
        model=model,
        vars_override=final_vars,
        cancel_token=None,
    )

    return result


# used in auto-coder.web
def auto_command(query: str, extra_args: Dict[str, Any] = {}):
    """处理/auto指令"""
    args = get_final_config()
    memory = get_memory()
    if args.enable_agentic_edit:
        from autocoder.run_context import get_run_context, RunMode

        execute_file, _ = generate_new_yaml(query)
        args.file = execute_file
        current_files = memory.get("current_files", {}).get("files", [])
        sources = []
        for file in current_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    sources.append(SourceCode(module_name=file, source_code=f.read()))
            except Exception as e:
                global_logger.error(f"Failed to read file {file}: {e}")

        try:
            llm = get_single_llm(
                args.code_model or args.model, product_mode=args.product_mode
            )
        except ValueError as e:
            console = Console()
            console.print(
                Panel(
                    f"[red]LLM Configuration Error:[/red]\n\n{str(e)}",
                    title="[red]Error[/red]",
                    border_style="red",
                    padding=(1, 2),
                )
            )
            return
        conversation_history = extra_args.get("conversations", [])

        command_infos = parse_query(query)

        # terminal 的总是接着上次对话, 所以这里总是设置为 resume
        conversation_config = AgenticEditConversationConfig(
            action=ConversationAction.RESUME
        )

        task_query = query

        if "new" in command_infos:
            conversation_config.action = ConversationAction.NEW
            task_query = " ".join(command_infos["new"]["args"])

        if "resume" in command_infos:
            conversation_config.action = ConversationAction.RESUME
            conversation_config.conversation_id = command_infos["resume"]["args"][0]
            task_query = " ".join(command_infos["resume"]["args"][1:])

        if "list" in command_infos:
            conversation_config.action = ConversationAction.LIST

        if "command" in command_infos:
            conversation_config.action = ConversationAction.COMMAND
            task_query = render_command_file_with_variables(command_infos)

        conversation_config.query = task_query

        # 处理特殊的conversation操作（LIST和NEW without input）
        if handle_conversation_actions(conversation_config):
            return conversation_config.conversation_id

        conversation_manager = get_conversation_manager()
        if conversation_config.action == ConversationAction.NEW:
            conversation_id = conversation_manager.create_conversation(
                name=conversation_config.query or "New Conversation",
                description=conversation_config.query or "New Conversation",
            )
            conversation_manager.set_current_conversation(conversation_id)
            conversation_config.conversation_id = conversation_id

        if (
            conversation_config.action == ConversationAction.RESUME
            and conversation_config.conversation_id
        ):
            conversation_manager.set_current_conversation(
                conversation_config.conversation_id
            )

        if (
            conversation_config.action == ConversationAction.RESUME
            and not conversation_config.conversation_id
            and conversation_manager.get_current_conversation_id()
        ):
            conversation_config.conversation_id = (
                conversation_manager.get_current_conversation_id()
            )
            conversation_manager.set_current_conversation(
                conversation_config.conversation_id
            )

        if not conversation_config.conversation_id:
            conversation_id = conversation_manager.create_conversation(
                name=conversation_config.query or "New Conversation",
                description=conversation_config.query or "New Conversation",
            )
            conversation_manager.set_current_conversation(conversation_id)
            conversation_config.conversation_id = conversation_id

        cancel_token = extra_args.get("event_file_id", None)
        global_logger.info(f"cancel_token: {cancel_token}")
        if cancel_token:
            global_cancel.register_token(cancel_token)

        if get_run_context().mode == RunMode.WEB:
            runner = FileBasedEventRunner(
                llm=llm,
                args=args,
                conversation_config=conversation_config,
                cancel_token=cancel_token,
            )
            runner.run(AgenticEditRequest(user_input=task_query))

        if get_run_context().mode == RunMode.TERMINAL:
            runner = TerminalRunner(
                llm=llm,
                args=args,
                conversation_config=conversation_config,
                cancel_token=cancel_token,
            )
            runner.run(AgenticEditRequest(user_input=task_query))

        completer.refresh_files()
        return conversation_config.conversation_id

    args = get_final_config()
    # 准备请求参数
    request = AutoCommandRequest(user_input=query)

    # 初始化调优器
    try:
        llm = get_single_llm(
            args.chat_model or args.model, product_mode=args.product_mode
        )
    except ValueError as e:
        console = Console()
        console.print(
            Panel(
                f"[red]LLM Configuration Error:[/red]\n\n{str(e)}",
                title="[red]Error[/red]",
                border_style="red",
                padding=(1, 2),
            )
        )
        return
    tuner = CommandAutoTuner(
        llm,
        args=args,
        memory_config=MemoryConfig(memory=memory, save_memory_func=save_memory),
        command_config=CommandConfig(
            add_files=add_files,
            remove_files=remove_files,
            list_files=list_files,
            conf=configure,
            revert=revert,
            commit=commit,
            help=help,
            exclude_dirs=exclude_dirs,
            exclude_files=exclude_files,
            ask=ask,
            chat=chat,
            coding=coding,
            design=design,
            summon=summon,
            lib=lib_command,
            mcp=mcp,
            models=manage_models,
            index_build=index_build,
            index_query=index_query,
            execute_shell_command=execute_shell_command,
            generate_shell_command=generate_shell_command,
            conf_export=conf_export,
            conf_import=conf_import,
            index_export=index_export,
            index_import=index_import,
        ),
    )

    # 生成建议
    response = tuner.analyze(request)
    printer = Printer()
    # 显示建议
    console = Console()
    console.print(
        Panel(
            Markdown(response.reasoning or ""),
            title=printer.get_message_from_key_with_format(
                "auto_command_reasoning_title"
            ),
            border_style="blue",
            padding=(1, 2),
        )
    )
    completer.refresh_files()
    return None


def render_command_file_with_variables(command_infos: Dict[str, Any]) -> str:
    """
    使用 CommandManager 加载并渲染命令文件

    Args:
        command_infos: parse_query(query) 的返回结果，包含命令和参数信息

    Returns:
        str: 渲染后的文件内容

    Raises:
        ValueError: 当参数不足或文件不存在时
        Exception: 当渲染过程出现错误时
    """
    try:
        # 获取第一个命令的信息
        if not command_infos:
            raise ValueError("command_infos 为空，无法获取命令信息")

        # command 的位置参数作为路径
        first_command = command_infos["command"]

        # 获取位置参数（文件路径）
        args = first_command.get("args", [])
        if not args:
            raise ValueError("未提供文件路径参数")

        file_path = args[0]  # 第一个位置参数作为文件路径

        # 获取关键字参数作为渲染参数
        kwargs = first_command.get("kwargs", {})
        render_variables = {
            "kwargs":kwargs,
            "args":args[1:],
            **kwargs,
        }

        # 初始化 CommandManager
        command_manager = CommandManager()

        # 使用 read_command_file_with_render 直接读取并渲染命令文件
        rendered_content = command_manager.read_command_file_with_render(
            file_path, render_variables
        )
        if rendered_content is None:
            raise ValueError(f"无法读取或渲染命令文件: {file_path}")

        global_logger.info(f"成功渲染命令文件: {file_path}, 使用参数: {render_variables}")
        return rendered_content

    except Exception as e:
        global_logger.error(f"render_command_file_with_variables 执行失败: {str(e)}")
        raise
