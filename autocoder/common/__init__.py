import pydantic
import ast
import sys
import subprocess
import os
import time
from typing import List, Dict, Any, Optional, Union

class SourceCode(pydantic.BaseModel):
    module_name: str
    source_code: str
    tag: str = ""
    tokens: int = -1
    metadata: Dict[str, Any] = {}

class SourceCodeList():
    def __init__(self, sources: List[SourceCode]):
        self.sources = sources

    def to_str(self):
        return "\n".join([f"##File: {source.module_name}\n{source.source_code}\n" for source in self.sources])
    
class TranslateReadme(pydantic.BaseModel):
    filename: str = pydantic.Field(..., description="需要翻译的文件路径")
    content: str = pydantic.Field(..., description="翻译后的内容")


class Translates(pydantic.BaseModel):
    readmes: List[TranslateReadme]


class TranslateArgs(pydantic.BaseModel):
    """
    示例：把项目中的markdown文档翻译成中文, 只翻译  test/abc.md 文件, 保存到test1目录下,翻译文件名
    此时对应的字段值应该是
    target_lang=中文
    file_suffix=.md
    new_file_mark=cn
    file_list=test/abc.md
    output_dir=test1
    should_translate_file_name=True
    """

    target_lang: str = pydantic.Field(
        ..., description="The target language to translate to"
    )
    file_suffix: str = pydantic.Field(
        ...,
        description="to filter the file by suffix, e.g. py, ts, md, etc. if multiple, use comma to separate",
    )
    new_file_mark: str = pydantic.Field(
        ...,
        description="according to the file suffix, the new file name should be like this: filename-new_file_mark.file_suffix",
    )
    file_list: List[str] = pydantic.Field(
        ..., description="the file list to translate provied"
    )
    output_dir: str = pydantic.Field(
        ..., description="the output directory to save the translated files"
    )
    should_translate_file_name: bool = pydantic.Field(
        ..., description="whether to translate the file name or not"
    )


class ExecuteStep(pydantic.BaseModel):
    code: str = pydantic.Field(
        ...,
        description="The code line to execute, e.g. `print('hello world')` or `ls -l`, shell or python code.",
    )
    lang: str = pydantic.Field(
        ...,
        description="The language to execute the code line, python,shell. default is python",
    )
    total_steps: Optional[int] = pydantic.Field(
        -1, description="The total steps to finish the user's question"
    )
    current_step: Optional[int] = pydantic.Field(
        -1, description="The current step to finish the user's question"
    )
    cwd: Optional[str] = pydantic.Field(
        None, description="The current working directory to execute the command line"
    )
    env: Optional[Dict[str, Any]] = pydantic.Field(
        None, description="The environment variables to execute the command line"
    )
    timeout: Optional[int] = pydantic.Field(
        None, description="The timeout to execute the command line"
    )
    ignore_error: Optional[bool] = pydantic.Field(
        False, description="Ignore the error of the command line"
    )


class ExecuteSteps(pydantic.BaseModel):
    steps: List[ExecuteStep]


class EnvInfo(pydantic.BaseModel):
    os_name: str
    os_version: str
    python_version: str
    conda_env: Optional[str]
    virtualenv: Optional[str]
    has_bash: bool
    default_shell: Optional[str]
    home_dir: Optional[str]
    cwd: Optional[str]


def has_sufficient_content(file_content, min_line_count=10):
    """Check if the file has a minimum number of substantive lines."""
    lines = [
        line
        for line in file_content.split("\n")
        if line.strip() and not line.strip().startswith("#")
    ]
    return len(lines) >= min_line_count


def remove_comments_and_docstrings(source):
    """Remove comments and docstrings from the Python source code."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)
        ) and ast.get_docstring(node):
            node.body = node.body[1:]  # Remove docstring
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Str):
            node.value.s = ""  # Remove comments
    return ast.unparse(tree)


def split_code_into_segments(source_code, max_tokens=1024):
    """Split the source code into segments of length up to max_tokens."""
    segments = []
    while len(source_code) > max_tokens:
        split_point = source_code.rfind("\n", 0, max_tokens)
        if split_point == -1:  # If no newline is found,
            split_point = max_tokens  # split at max_tokens
        segments.append(source_code[:split_point])
        source_code = source_code[split_point:]
    segments.append(source_code)
    return segments


def detect_env() -> EnvInfo:
    os_name = sys.platform
    os_version = ""
    if os_name == "win32":
        os_version = sys.getwindowsversion().major
    elif os_name == "darwin":
        os_version = (
            subprocess.check_output(["sw_vers", "-productVersion"])
            .decode("utf-8")
            .strip()
        )
    elif os_name == "linux":
        os_version = subprocess.check_output(["uname", "-r"]).decode("utf-8").strip()

    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )

    conda_env = os.environ.get("CONDA_DEFAULT_ENV")
    virtualenv = os.environ.get("VIRTUAL_ENV")
    
    # Get default shell
    if os_name == "win32":
        default_shell = os.environ.get("COMSPEC", "cmd.exe")
    else:
        default_shell = os.environ.get("SHELL", "/bin/sh")

    # Get home directory
    home_dir = os.path.expanduser("~")
    
    # Get current working directory
    cwd = os.getcwd()

    has_bash = True
    try:
        subprocess.check_output(["bash", "--version"])
    except:
        has_bash = False

    return EnvInfo(
        os_name=os_name,
        os_version=str(os_version),
        python_version=python_version,
        conda_env=conda_env,
        virtualenv=virtualenv,
        has_bash=has_bash,
        default_shell=default_shell,
        home_dir=home_dir,
        cwd=cwd,
    )


def chat_with_llm_step_by_step(
    llm, conversations, response_class, max_steps=30, anti_quota_limit=1
):
    if max_steps == -1:
        max_steps = 30

    result = []
    t = llm.chat_oai(
        conversations=conversations,
        response_class=response_class,
        enable_default_sys_message=True,
    )
    total_steps = max_steps
    current_step = 0

    while current_step < total_steps and t[0].value:
        result.append(t[0].value)
        conversations.append({"role": "assistant", "content": t[0].response.output})
        print(
            f"{conversations[-1]['role']}: {conversations[-1]['content']}\n", flush=True
        )

        conversations.append({"role": "user", "content": "继续"})
        print(
            f"{conversations[-1]['role']}: {conversations[-1]['content']}\n", flush=True
        )
        t = llm.chat_oai(
            conversations=conversations,
            response_class=response_class,
            enable_default_sys_message=True,
        )
        current_step += 1
        time.sleep(anti_quota_limit)

    return result, conversations


class AutoCoderArgs(pydantic.BaseModel):
    request_id: Optional[str] = None
    source_dir: Optional[str] = "."
    git_url: Optional[str] = None
    target_file: Optional[str] = None
    query: Optional[str] = None
    template: Optional[str] = None
    project_type: Optional[str] = None
    execute: Optional[bool] = None
    package_name: str = ""
    script_path: str = ""
        
    model: str = ""
    chat_model: str = ""
    model_max_length: int = 2000
    model_max_input_length: int = 6000
    vl_model: str = ""
    sd_model: str = ""
    emb_model: str = ""
    code_model: str = ""
    generate_rerank_model: str = ""
    context_prune_model: str = ""
    conversation_prune_model: str = ""
    inference_model: str = ""
    system_prompt: str = ""
    planner_model: str = ""
    voice2text_model: str = ""
    text2voice_model: str = ""
    commit_model: str = ""
    
    skip_build_index: bool = False
    skip_filter_index: bool = False

    index_model: str = ""
    index_filter_model: str = ""
    index_filter_model_max_input_length: int = 50*1024
    index_model_max_length: int = 0
    index_model_max_input_length: int = 0
    index_model_anti_quota_limit: int = 0

    enable_agentic_filter: bool = True
    enable_agentic_edit: bool = True
    enable_agentic_auto_approve: bool = False
    enable_agentic_dangerous_command_check: bool = False
    agentic_max_rounds: int = 10000
    agentic_mode:str = "act" #plan|act
    agentic_connection_retries: int = 10
    

    index_filter_level: int = 0
    index_filter_enable_relevance_verification: bool = True
    index_filter_workers: int = 1
    index_filter_file_num: int = 10
    index_build_workers: int = 1
    
    designer_model: str = ""
    file: Optional[str] = None
    ray_address: str = ""
    anti_quota_limit: int = 1    
    print_request: bool = False
    py_packages: str = ""
    
    search: Union[str, List[str]] = ""
    search_engine: str = ""
    search_engine_token: str = ""
        
    rag_url: str = ""
    rag_token: str = ""
    rag_type: str = "storage"
    rag_storage_type: str = "duckdb"  # 向量化存储类型 byzer-storage | duckdb
    rag_params_max_tokens: int = 500000 
    rag_doc_filter_relevance: int = 2
    rag_context_window_limit: int = 120000
    rag_duckdb_vector_dim: int = 1024  # DuckDB 向量化存储的维度
    rag_duckdb_query_similarity: float = 0.1  # DuckDB 向量化检索 相似度 阈值
    rag_duckdb_query_top_k: int = 10000  # DuckDB 向量化检索 返回 TopK个结果(且大于相似度)
    rag_index_build_workers: int = 10
    rag_emb_dim: int = 1024
    rag_emb_text_size: int = 1024
    # rag 本地图床地址
    local_image_host: str = ""
    rag_recall_max_queries: int = 5

    include_rules: bool = True
    checker_llm_temperature: Optional[float] = None
    checker_llm_top_p: Optional[float] = None
    checker_llm_seed: Optional[int] = None
    checker_llm_config: Optional[Dict[str, Any]] = None
    checker_chunk_overlap_multiplier: Optional[float] = None
    checker_chunk_token_limit: Optional[int] = None
    checker_llm_repeat: Optional[int] = None
    checker_llm_consensus_ratio: Optional[float] = None

    
    # 回答用户问题时，使用哪种对话历史策略
    # single_round: 单轮对话
    # multi_round: 多轮对话
    rag_qa_conversation_strategy: str = "multi_round"

    verify_file_relevance_score: int = 6
    enable_rag_search: Union[bool, str] = False
    enable_rag_context: Union[bool, str] = False
    collection: Optional[str] = None
    collections: Optional[str] = None

    auto_merge: Union[bool, str] = False
    human_as_model: bool = False
    human_model_num: int = 1

    image_file: str = ""
    image_mode: str = "direct"
    image_max_iter: int = 1
    
    urls: Union[str, List[str]] = ""
    urls_use_model: bool = False    
    command: Optional[str] = None
    doc_command: Optional[str] = None
    required_exts: Optional[str] = None
    hybrid_index_max_output_tokens: int = 1000000

    enable_multi_round_generate: bool = False

    monitor_mode: bool = False
    enable_hybrid_index: bool = False
    rag_build_name: Optional[str] = None
    disable_auto_window: bool = False
    filter_batch_size: int = 5
    disable_segment_reorder: bool = False    
    tokenizer_path: Optional[str] = None
    skip_confirm: bool = False
    silence: bool = False
    exclude_files: Union[str, List[str]] = ""
    output: str = ""
    single_file: bool = False
    query_prefix: Optional[str] = None
    query_suffix: Optional[str] = None
    from_yaml: Optional[str] = None
    base_dir: Optional[str] = None
    context: Optional[str] = None
    editblock_similarity: float = 0.9
    include_project_structure: bool = False
    new_session: bool = False    

    prompt_review: Optional[str] = None

    agent_designer_mode: str = "svg"

    full_text_ratio: float = 0.7
    segment_ratio: float = 0.2
    buff_ratio: float = 0.1

    disable_inference_enhance: bool = True
    inference_deep_thought: bool = False
    inference_slow_without_deep_thought: bool = False
    inference_compute_precision: int = 64
    without_contexts: bool = False
    skip_events: bool = False
    data_cells_max_num: int = 2000
    generate_times_same_model: int = 1
    rank_times_same_model: int = 1
    
    # block:给定每个文件修改的代码块 file: 给定每个文件修改前后内容
    rank_strategy: str = "file"

    action: Union[List[str], Dict[str, Any]] = []
    cancel_token: Optional[str] = None
    enable_global_memory: bool = False  
    product_mode: str = "lite"

    keep_reasoning_content: bool = False
    keep_only_reasoning_content: bool = False

    in_code_apply: bool = False
    model_filter_path: Optional[str] = None

    conversation_prune_safe_zone_tokens: Union[str, int, float] = 0.7
    conversation_prune_group_size: int = 4
    conversation_prune_strategy: str = "summarize"

    context_prune_strategy: str = "extract"
    context_prune: bool = True
    context_prune_safe_zone_tokens: Union[str, int, float] = 40*1024
    context_prune_sliding_window_size: int = 1000
    context_prune_sliding_window_overlap: int = 100

    # Range-based conversation pruning settings
    enable_range_pruning: bool = False           # 是否启用区间裁剪
    range_preserve_pairs: bool = True            # 是否保证user/assistant成对裁剪
    range_storage_dir: Optional[str] = None      # 存储目录，None使用默认目录
    range_backup_enabled: bool = True            # 是否启用备份
    range_max_backup_files: int = 10             # 最大备份文件数

    auto_command_max_iterations: int = 10

    
    use_shell_commands: bool = True
    
    skip_commit: bool = False

    enable_beta: bool = False

    how_to_reproduce: Optional[str] = None

    dynamic_urls: List[str] = []

    add_updated_urls: List[str] = []

    enable_task_history: bool = False

    event_file: Optional[str] = None

    enable_active_context: bool = False
    enable_active_context_in_generate: bool = False

    generate_max_rounds: int = 5

    revert_commit_id: Optional[str] = None

    enable_auto_fix_lint: bool = False
    enable_auto_fix_compile: bool = False
    enable_auto_fix_merge: bool = False

    auto_fix_lint_max_attempts: int = 5
    auto_fix_compile_max_attempts: int = 5
    auto_fix_merge_max_attempts: int = 5

    enable_auto_select_rules: bool = True
    
    ignore_clean_shadows: bool = False

    firecrawl_api_key: Optional[str] = None
    metaso_api_key: Optional[str] = None
    bochaai_api_key: Optional[str] = None

    # Timeout (in seconds) for calling subagents via RunNamedSubagentsToolResolver
    # Default to 30 minutes
    call_subagent_timeout: float = 30 * 60

    class Config:
        protected_namespaces = ()
