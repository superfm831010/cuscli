from autocoder.utils import get_last_yaml_file
import os
import uuid
import byzerllm
from autocoder.common import AutoCoderArgs
from autocoder.common.autocoderargs_parser import AutoCoderArgsParser
from typing import List, Optional
import yaml
from autocoder.auto_coder import AutoCoderArgs, load_include_files, Template
from autocoder.common import git_utils
import hashlib

# 该文件要给 chat,rag, web 等上层交互层使用


def convert_yaml_to_config(yaml_file: str):

    args = AutoCoderArgs()
    with open(yaml_file, "r",encoding="utf-8") as f:
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


def convert_yaml_config_to_str(yaml_config):
    yaml_content = yaml.safe_dump(
        yaml_config,
        allow_unicode=True,
        default_flow_style=False,
        default_style=None,
    )
    return yaml_content


def get_llm_friendly_package_docs(memory,
                                  package_name: Optional[str] = None, return_paths: bool = False
                                  ) -> List[str]:
    """
    Legacy function for backward compatibility.
    Use LLMFriendlyPackageManager class for new code.
    """
    from autocoder.common.llm_friendly_package import LLMFriendlyPackageManager
    
    project_root = os.getcwd()
    base_persist_dir = os.path.join(project_root, ".auto-coder", "plugins", "chat-auto-coder")
    
    manager = LLMFriendlyPackageManager(
        project_root=project_root,
        base_persist_dir=base_persist_dir
    )
    return manager.get_docs(package_name, return_paths)


def convert_config_value(key, value):
    # 定义需要使用 token 解析的字段
    token_fields = {
        'conversation_prune_safe_zone_tokens',
        'context_prune_safe_zone_tokens',
        'context_prune_sliding_window_size',
        'context_prune_sliding_window_overlap',
        'rag_params_max_tokens',
        'rag_context_window_limit',
        'rag_duckdb_vector_dim',
        'rag_duckdb_query_top_k',
        'rag_emb_dim',
        'rag_emb_text_size',
        'hybrid_index_max_output_tokens',
        'data_cells_max_num',
    }
    
    field_info = AutoCoderArgs.model_fields.get(key)
    if field_info:
        # 对于需要 token 解析的字段，使用 AutoCoderArgsParser
        if key in token_fields:
            try:
                parser = AutoCoderArgsParser()
                return parser.parse_token_field(key, value)
            except Exception as e:
                print(f"Warning: Failed to parse token field '{key}' with value '{value}': {e}")
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


def get_llm(memory, model:Optional[str]=None):
    latest_yaml_file = get_last_yaml_file("actions")

    conf = memory.get("conf", {})
    current_files = memory["current_files"]["files"]
    execute_file = None

    if latest_yaml_file:
        try:
            execute_file = os.path.join("actions", latest_yaml_file)
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
                memory=memory,
                return_paths=True
            )

            # 临时保存yaml文件，然后读取yaml文件，转换为args
            temp_yaml = os.path.join("actions", f"{uuid.uuid4()}.yml")
            try:
                with open(temp_yaml, "w",encoding="utf-8") as f:
                    f.write(convert_yaml_config_to_str(
                        yaml_config=yaml_config))
                args = convert_yaml_to_config(temp_yaml)
            finally:
                if os.path.exists(temp_yaml):
                    os.remove(temp_yaml)

            llm = byzerllm.ByzerLLM.from_default_model(model or
                                                       args.code_model or args.model)
            return llm
        except Exception as e:
            print(f"Failed to commit: {e}")
            if execute_file:
                os.remove(execute_file)
            return None
