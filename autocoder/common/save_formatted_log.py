import os
import json
import uuid
from datetime import datetime
from loguru import logger  # Added import
from typing import Optional, Any, Union, Dict
from pathlib import Path


# New helper function for cleaning up logs
def _cleanup_logs(logs_dir: str, max_files: int = 100):
    """
    Cleans up old log files in the specified directory, keeping only the most recent ones.
    Log files are expected to follow the naming convention: <YYYYmmdd_HHMMSS>_<uuid>_<suffix>.md
    """
    logger.debug(f"开始清理日志目录: {logs_dir}，最大保留文件数: {max_files}")
    if not os.path.isdir(logs_dir):
        logger.debug(f"日志目录 {logs_dir} 不存在，无需清理。")
        return

    log_files = []
    for filename in os.listdir(logs_dir):
        if filename.endswith(".md"):
            parts = filename.split("_")
            # Expected format: <YYYYmmdd_HHMMSS>_<uuid>_<suffix>.md
            # parts[0] should be date part "YYYYmmdd" and parts[1] should be time part "HHMMSS"
            if len(parts) >= 3:  # At least date, time, and uuid parts
                # Reconstruct the full timestamp from first two parts
                timestamp_str = parts[0] + "_" + parts[1]
                try:
                    # Validate the timestamp format
                    datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    log_files.append((timestamp_str, os.path.join(logs_dir, filename)))
                except ValueError:
                    logger.debug(
                        f"文件名 {filename} 的时间戳部分 ({timestamp_str}) 格式不正确，跳过。"
                    )
                    continue
            else:
                # Log the parts for better debugging if needed
                logger.debug(
                    f"文件名 {filename} (分割后: {parts}) 不符合预期的下划线分割数量 (至少需要 <date>_<time>_<uuid>_...)，跳过。"
                )

    # Sort by timestamp (oldest first)
    log_files.sort(key=lambda x: x[0])

    if len(log_files) > max_files:
        files_to_delete_count = len(log_files) - max_files
        logger.info(
            f"日志文件数量 ({len(log_files)}) 超过限制 ({max_files})，将删除 {files_to_delete_count} 个最旧的文件。"
        )
        for i in range(files_to_delete_count):
            file_to_delete_timestamp, file_to_delete_path = log_files[i]
            try:
                os.remove(file_to_delete_path)
                logger.info(
                    f"已删除旧日志文件: {file_to_delete_path} (时间戳: {file_to_delete_timestamp})"
                )
            except OSError as e:
                logger.warning(f"删除日志文件 {file_to_delete_path} 失败: {str(e)}")
                logger.exception(e)  # Log stack trace
    else:
        logger.debug(
            f"日志文件数量 ({len(log_files)}) 未超过限制 ({max_files})，无需删除。"
        )


def render_markdown_from_json(data: Any, root_title: str = "Log Entry") -> str:
    """
    将 JSON 数据渲染为 Markdown 格式

    Args:
        data: 要渲染的数据（dict, list 或其他类型）
        root_title: 根标题，默认为 "Log Entry"

    Returns:
        str: 渲染后的 Markdown 文本
    """

    def to_markdown(obj, level=1):
        lines = []
        if isinstance(obj, dict):
            for key, value in obj.items():
                lines.append(f"{'#' * (level + 1)} {key}\n")
                lines.extend(to_markdown(value, level + 1))
        elif isinstance(obj, list):
            for idx, item in enumerate(obj, 1):
                lines.append(f"{'#' * (level + 1)} Item {idx}\n")
                lines.extend(to_markdown(item, level + 1))
        else:
            lines.append(str(obj) + "\n")
        return lines

    md_lines = [f"# {root_title}\n"]
    md_lines.extend(to_markdown(data, 1))
    return "\n".join(md_lines)


def save_formatted_log(
    project_root,
    json_text,
    suffix,
    conversation_id: Optional[str] = None,
    log_subdir: str = "agentic",
):
    """
    Save a JSON log as a formatted markdown file under project_root/.auto-coder/logs/{log_subdir}.
    Filename: <YYYYmmdd_HHMMSS>_<uuid>_<suffix>.md
    Also cleans up old logs in the directory, keeping the latest 100.
    Args:
        project_root (str): The root directory of the project.
        json_text (str): The JSON string to be formatted and saved.
        suffix (str): The suffix for the filename.
        conversation_id (str, optional): If provided, use this as unique_id and search for existing files to overwrite.
        log_subdir (str): The subdirectory under .auto-coder/logs/ to save the file. Default is "agentic".
    """
    # Prepare directory (logs_dir is needed for cleanup first)
    logs_dir = os.path.join(project_root, ".auto-coder", "logs", log_subdir)

    # Cleanup old logs BEFORE saving the new one
    try:
        _cleanup_logs(logs_dir)  # Default to keep 100 files
    except Exception as e:
        logger.warning(f"日志清理过程中发生错误: {str(e)}")
        logger.exception(e)
        # Log cleanup failure should not prevent the main functionality

    # Parse JSON
    try:
        data = json.loads(json_text)
    except Exception as e:
        logger.error(f"无效的 JSON 格式: {str(e)}")  # Log error before raising
        logger.exception(e)  # Log stack trace
        raise ValueError(f"Invalid JSON provided: {e}")

    # Filter out system role entries
    def filter_system_role(obj):
        """Recursively filter out entries where role equals 'system'"""
        if isinstance(obj, dict):
            # If this dict has role='system', skip it entirely
            if obj.get("role") == "system":
                return None
            # Otherwise, recursively filter all values
            filtered_dict = {}
            for key, value in obj.items():
                filtered_value = filter_system_role(value)
                if filtered_value is not None:
                    filtered_dict[key] = filtered_value
            return filtered_dict if filtered_dict else None
        elif isinstance(obj, list):
            # Filter list items, keeping only non-None results
            filtered_list = []
            for item in obj:
                filtered_item = filter_system_role(item)
                if filtered_item is not None:
                    filtered_list.append(filtered_item)
            return filtered_list if filtered_list else None
        else:
            # For primitive types, return as-is
            return obj

    # Apply the filter
    data = filter_system_role(data)
    if data is None:
        logger.warning("过滤后的数据为空，将保存空日志")
        data = {}

    # Use the shared markdown rendering function
    md_content = render_markdown_from_json(data, root_title="Log Entry")

    # Ensure directory exists
    # _cleanup_logs checks if dir exists but does not create it.
    # os.makedirs needs to be called to ensure the directory for the new log file.
    os.makedirs(logs_dir, exist_ok=True)

    # Prepare filename
    now = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Handle conversation_id logic
    if conversation_id is not None:
        unique_id = conversation_id

        # Search for existing files with this conversation_id
        existing_file = None
        if os.path.isdir(logs_dir):
            for filename in os.listdir(logs_dir):
                if (
                    filename.endswith(".md")
                    and conversation_id in filename
                    and suffix in filename
                ):
                    existing_file = os.path.join(logs_dir, filename)
                    logger.info(
                        f"找到包含 conversation_id ({conversation_id}) 的现有文件: {filename}，将覆盖该文件"
                    )
                    break

        if existing_file:
            filepath = existing_file
        else:
            filename = f"{now}_{unique_id}_{suffix}.md"
            filepath = os.path.join(logs_dir, filename)
            logger.info(
                f"未找到包含 conversation_id ({conversation_id}) 的文件，将创建新文件: {filename}"
            )
    else:
        unique_id = str(uuid.uuid4())
        filename = f"{now}_{unique_id}_{suffix}.md"
        filepath = os.path.join(logs_dir, filename)

    # Save file
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)
        logger.info(f"日志已保存至: {filepath}")
    except IOError as e:
        logger.error(f"保存日志文件 {filepath} 失败: {str(e)}")
        logger.exception(e)  # Log stack trace
        raise  # Re-throw the exception so the caller knows saving failed

    return filepath


def save_stream_formatted_log(
    project_root: Union[str, Path],
    payload: Dict[str, Any],
    log_filename: str = "conversation.md",
) -> str:
    """
    将单条对话消息以流式追加方式写入日志文件，支持按日切割

    Args:
        project_root: 项目根目录
        payload: 消息载荷，包含以下字段：
            - conversation_id: 对话ID
            - timestamp: ISO8601格式时间戳
            - role: 角色（user/assistant）
            - content: 消息内容
            - message_id: 消息ID
            - metadata: 可选的元数据
            - llm_metadata: 可选的LLM元数据
        log_filename: 日志文件名，默认为 "conversation.md"

    Returns:
        str: 最终写入的文件路径
    """
    try:
        # 准备日志目录
        logs_dir = Path(project_root) / ".auto-coder" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        log_file = logs_dir / log_filename
        today = datetime.now().date()

        # 按日切割：如果文件存在且修改日期不是今天，进行轮转
        if log_file.exists():
            mtime_dt = datetime.fromtimestamp(log_file.stat().st_mtime)
            mtime = mtime_dt.date()
            if mtime != today:
                # 生成归档文件名，使用完整的 datetime 以确保唯一性
                archive_name = f"conversation_{mtime_dt.strftime('%Y%m%d')}.md"
                archive_file = logs_dir / archive_name

                # 如果归档文件已存在，添加完整时间戳后缀确保唯一性
                if archive_file.exists():
                    # 使用实际的修改时间（小时分钟秒）作为后缀
                    archive_name = (
                        f"conversation_{mtime_dt.strftime('%Y%m%d_%H%M%S')}.md"
                    )
                    archive_file = logs_dir / archive_name
                    # 如果还存在（极少见），追加微秒
                    if archive_file.exists():
                        archive_name = f"conversation_{mtime_dt.strftime('%Y%m%d_%H%M%S')}_{mtime_dt.microsecond}.md"
                        archive_file = logs_dir / archive_name

                # 重命名旧文件
                log_file.rename(archive_file)
                logger.info(f"日志文件已归档: {archive_file}")

        # 构造消息数据结构
        message_data = {
            "conversation_id": payload.get("conversation_id", ""),
            "timestamp": payload.get("timestamp", ""),
            "message": {
                "role": payload.get("role", ""),
                "message_id": payload.get("message_id", ""),
                "content": payload.get("content", ""),
            },
        }

        # 添加可选的元数据（仅当非空时）
        if payload.get("metadata"):
            message_data["message"]["metadata"] = payload["metadata"]
        if payload.get("llm_metadata"):
            message_data["message"]["llm_metadata"] = payload["llm_metadata"]

        # 渲染为 Markdown
        md_content = render_markdown_from_json(message_data, root_title="Message")

        # 追加写入，每条消息后添加分隔线
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(md_content)
            f.write("\n\n---\n\n")

        logger.debug(f"对话消息已追加至: {log_file}")
        return str(log_file)

    except Exception as e:
        logger.warning(f"流式保存对话日志失败: {e}")
        logger.exception(e)
        # 不阻断主流程，返回空字符串
        return ""
