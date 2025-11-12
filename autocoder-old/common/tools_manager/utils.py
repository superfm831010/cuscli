"""
Tools Manager Utility Functions

提供工具文件分析和处理的实用函数。
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, List
from loguru import logger


def is_tool_command_file(file_path: str) -> bool:
    """
    检查文件是否是有效的工具命令文件

    Args:
        file_path: 文件路径

    Returns:
        bool: 是否是有效的工具命令文件
    """
    try:
        path = Path(file_path)

        # 检查文件是否存在
        if not path.exists() or not path.is_file():
            return False

        # 检查文件扩展名（支持脚本文件和可执行文件）
        valid_extensions = {'.py', '.sh', '.js', '.rb', '.pl', '.php', '.go', '.rs', ''}
        if path.suffix.lower() not in valid_extensions:
            return False

        # 检查是否可执行或是脚本文件
        if path.suffix == '':
            # 无扩展名文件，检查是否可执行
            return os.access(file_path, os.X_OK)
        else:
            # 脚本文件，检查是否可读
            return os.access(file_path, os.R_OK)

    except Exception as e:
        logger.warning(f"检查工具命令文件时出错 {file_path}: {e}")
        return False


def extract_tool_help(file_path: str) -> str:
    """
    提取工具命令的帮助信息

    Args:
        file_path: 工具命令文件路径

    Returns:
        str: 帮助信息，如果获取失败返回默认信息
    """
    try:
        # 尝试命令行帮助
        help_text = _try_command_line_help(file_path)
        if help_text:
            return help_text
            
        # 回退到文件注释
        return _extract_help_from_file_comments(file_path)
        
    except Exception as e:
        logger.debug(f"帮助信息提取失败 {file_path}: {e}")
        return f"工具命令: {Path(file_path).name}"


def _try_command_line_help(file_path: str) -> Optional[str]:
    """
    尝试通过命令行获取帮助信息
    
    Args:
        file_path: 工具文件路径
        
    Returns:
        Optional[str]: 帮助信息，如果获取失败返回None
    """
    help_commands = [
        [file_path, 'help'],
        [file_path, '-h'], 
        [file_path, '--help']
    ]
    
    for cmd in help_commands:
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=5, 
                cwd=Path(file_path).parent
            )
            if result.returncode == 0 and (result.stdout.strip() or result.stderr.strip()):
                return result.stdout.strip() or result.stderr.strip()
        except Exception:
            continue
    return None


def _extract_help_from_file_comments(file_path: str) -> str:
    """
    从文件注释中提取帮助信息

    Args:
        file_path: 文件路径

    Returns:
        str: 从注释中提取的帮助信息
    """
    try:
        path = Path(file_path)

        # 根据文件扩展名确定注释符号
        comment_patterns = {
            '.py': '#',
            '.sh': '#',
            '.rb': '#',
            '.pl': '#',
            '.php': '#',
            '.js': '//',
            '.go': '//',
            '.rs': '//',
            '': '#'  # 默认使用 # 注释
        }

        comment_char = comment_patterns.get(path.suffix.lower(), '#')

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        help_lines = []
        in_help_section = False
        empty_comment_count = 0

        for line in lines[:50]:  # 只检查前50行
            line = line.strip()

            # 跳过 shebang 行
            if line.startswith('#!'):
                continue

            # 检查是否是注释行
            if line.startswith(comment_char):
                comment_text = line[len(comment_char):].strip()

                # 检查是否是帮助信息的开始
                if any(keyword in comment_text.lower() for keyword in ['usage:', 'help:', 'description:', '用法:', '说明:', '描述:']):
                    in_help_section = True
                    help_lines.append(comment_text)
                    empty_comment_count = 0
                elif in_help_section:
                    if comment_text:
                        help_lines.append(comment_text)
                        empty_comment_count = 0
                    else:
                        # 空注释行，计数但不立即停止
                        empty_comment_count += 1
                        if empty_comment_count >= 2:
                            # 连续两个空注释行，停止提取
                            break
            elif in_help_section:
                # 非注释行，帮助信息结束
                break

        if help_lines:
            return '\n'.join(help_lines)
        else:
            return f"工具命令: {path.name}"

    except Exception as e:
        logger.warning(f"从文件注释提取帮助信息时出错 {file_path}: {e}")
        return f"工具命令: {Path(file_path).name}"


def get_project_name() -> str:
    """
    获取当前项目名称

    Returns:
        str: 项目名称
    """
    try:
        current_dir = Path.cwd()
        return current_dir.name
    except Exception:
        return "unknown"
