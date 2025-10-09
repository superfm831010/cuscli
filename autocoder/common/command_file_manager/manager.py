"""
命令管理器

整个模块的主入口，提供高层次的API接口，用于列出、读取和分析命令文件。
支持多目录查找、合并结果和repos功能。
"""

import os
from loguru import logger
from typing import Dict, List, Optional, Set, Tuple, Any
from byzerllm.utils import format_str_jinja2

from autocoder.common.command_file_manager.models import (
    CommandFile, JinjaVariable, CommandFileAnalysisResult, ListCommandsResult
)
from autocoder.common.command_file_manager.utils import (
    extract_jinja2_variables, extract_jinja2_variables_with_metadata,
    analyze_command_file, is_command_file
)
from autocoder.common.priority_directory_finder import (
    PriorityDirectoryFinder, FinderConfig, SearchStrategy, 
    ValidationMode, create_file_filter
)


class CommandManager:
    """命令管理器，提供高层次的API接口，支持多目录查找和合并结果"""
    
    def __init__(self, commands_dir: Optional[str] = None):
        """
        初始化命令管理器
        
        Args:
            commands_dir: 命令文件目录路径，如果为None则使用优先级目录查找器按优先级查找和合并:
                        1. 项目/.autocodercommands 
                        2. 项目/.auto-coder/.autocodercommands
                        3. ~/.auto-coder/.autocodercommands
                        4. ~/.auto-coder/.autocodercommands/repos/{项目名}/
        """
        if commands_dir is None:
            # 使用多目录查找和合并
            self.commands_directories = self._find_commands_directories()
            # 保持向后兼容性，设置主目录
            self.commands_dir = self.commands_directories[0] if self.commands_directories else os.path.join(os.getcwd(), ".autocodercommands")
        else:
            # 如果指定了单个目录，则只使用该目录
            self.commands_dir = os.path.abspath(commands_dir)
            self.commands_directories = [self.commands_dir]
        
        # 确保主目录存在
        if not os.path.exists(self.commands_dir):
            logger.warning(f"主命令目录不存在: {self.commands_dir}")
            os.makedirs(self.commands_dir, exist_ok=True)
            logger.info(f"已创建主命令目录: {self.commands_dir}")
    
    def _find_commands_directories(self) -> List[str]:
        """
        使用优先级目录查找器查找所有命令目录，支持多目录合并和repos功能
        
        Returns:
            List[str]: 找到的命令目录路径列表，按优先级排序
        """
        try:
            # 创建文件过滤器，只查找.md文件
            md_filter = create_file_filter(extensions=[".md"], recursive=True)
            
            # 创建查找器配置，使用MERGE_ALL策略合并所有目录
            config = FinderConfig(strategy=SearchStrategy.MERGE_ALL)
            
            # 按优先级添加标准目录配置
            current_dir = os.getcwd()
            project_name = os.path.basename(current_dir)
            
            # 1. 项目级目录 (优先级最高)
            config.add_directory(
                path=os.path.join(current_dir, ".autocodercommands"),
                priority=1,
                validation_mode=ValidationMode.HAS_SPECIFIC_FILES,
                file_filter=md_filter,
                description="项目级命令目录"
            )
            
            # 2. 项目.auto-coder目录
            config.add_directory(
                path=os.path.join(current_dir, ".auto-coder", ".autocodercommands"),
                priority=2,
                validation_mode=ValidationMode.HAS_SPECIFIC_FILES,
                file_filter=md_filter,
                description="项目.auto-coder命令目录"
            )
            
            # 3. 全局目录
            config.add_directory(
                path="~/.auto-coder/.autocodercommands",
                priority=3,
                validation_mode=ValidationMode.HAS_SPECIFIC_FILES,
                file_filter=md_filter,
                description="全局命令目录"
            )
            
            # 4. repos目录 (优先级最低，但仍会被合并)
            repos_dir = f"~/.auto-coder/.autocodercommands/repos/{project_name}"
            config.add_directory(
                path=repos_dir,
                priority=4,
                validation_mode=ValidationMode.HAS_SPECIFIC_FILES,
                file_filter=md_filter,
                description=f"项目特定repos命令目录: {project_name}"
            )
            
            # 执行查找
            finder = PriorityDirectoryFinder(config)
            result = finder.find_directories()
            
            if result.success and result.selected_directories:
                logger.info(f"使用优先级查找器找到 {len(result.selected_directories)} 个命令目录")
                for i, dir_path in enumerate(result.selected_directories):
                    logger.info(f"  {i+1}. {dir_path}")
                return result.selected_directories
            else:
                # 回退到默认目录
                default_dir = os.path.join(current_dir, ".autocodercommands")
                logger.info(f"优先级查找器未找到有效目录，使用默认: {default_dir}")
                return [default_dir]
                
        except Exception as e:
            logger.warning(f"使用优先级查找器时发生错误: {e}")
            # 回退到默认目录
            default_dir = os.path.join(os.getcwd(), ".autocodercommands")
            logger.info(f"回退到默认目录: {default_dir}")
            return [default_dir]
    
    def list_command_files(self, recursive: bool = True) -> ListCommandsResult:
        """
        列出所有命令目录中的命令文件，支持多目录合并和优先级覆盖
        
        Args:
            recursive: 是否递归搜索子目录
            
        Returns:
            ListCommandsResult: 列出结果，按优先级合并去重
        """
        result = ListCommandsResult(success=True)
        file_priority_map = {}  # 文件名 -> (目录优先级, 完整路径)
        
        # 按优先级顺序遍历所有目录（优先级高的先处理，后续同名文件会被忽略）
        for dir_index, commands_dir in enumerate(self.commands_directories):
            if not os.path.exists(commands_dir):
                continue
                
            try:
                if recursive:
                    for root, _, files in os.walk(commands_dir):
                        for file in files:
                            if is_command_file(file):
                                file_path = os.path.join(root, file)
                                rel_path = os.path.relpath(file_path, commands_dir)
                                
                                # 检查是否已有同名文件，优先级高的保留
                                if rel_path not in file_priority_map:
                                    file_priority_map[rel_path] = (dir_index, file_path)
                                    logger.debug(f"添加命令文件: {rel_path} (来源: {commands_dir})")
                                else:
                                    existing_priority, existing_path = file_priority_map[rel_path]
                                    logger.debug(f"跳过命令文件: {rel_path} (已存在优先级更高的版本: {existing_path})")
                else:
                    for item in os.listdir(commands_dir):
                        item_path = os.path.join(commands_dir, item)
                        if os.path.isfile(item_path) and is_command_file(item):
                            if item not in file_priority_map:
                                file_priority_map[item] = (dir_index, item_path)
                                logger.debug(f"添加命令文件: {item} (来源: {commands_dir})")
                            else:
                                existing_priority, existing_path = file_priority_map[item]
                                logger.debug(f"跳过命令文件: {item} (已存在优先级更高的版本: {existing_path})")
                                
            except Exception as e:
                logger.error(f"列出目录 {commands_dir} 中的命令文件时出错: {str(e)}")
                result.add_error(commands_dir, f"列出命令文件时出错: {str(e)}")
        
        # 添加所有去重后的文件到结果中
        for rel_path in sorted(file_priority_map.keys()):
            result.add_command_file(rel_path)
        
        logger.info(f"从 {len(self.commands_directories)} 个目录中找到 {len(file_priority_map)} 个唯一命令文件")
        return result
    
    def read_command_file(self, file_name: str) -> Optional[CommandFile]:
        """
        读取指定的命令文件，按优先级从多个目录中查找
        
        Args:
            file_name: 命令文件名或相对路径
            
        Returns:
            Optional[CommandFile]: 命令文件对象，如果文件不存在则返回None
        """
        # 按优先级顺序查找文件
        for commands_dir in self.commands_directories:
            file_path = os.path.join(commands_dir, file_name)
            
            if os.path.isfile(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    logger.debug(f"找到命令文件: {file_path}")
                    return CommandFile(
                        file_path=file_path,
                        file_name=os.path.basename(file_path),
                        content=content
                    )
                except Exception as e:
                    logger.error(f"读取命令文件时出错: {str(e)}")
                    continue
        
        logger.warning(f"在所有目录中都未找到命令文件: {file_name}")
        logger.debug(f"搜索的目录: {self.commands_directories}")
        return None
    
    def read_command_file_with_render(self, file_name: str, render_variables: Dict[str, Any] = {}) -> Optional[str]:
        """
        读取指定的命令文件并使用 Jinja2 进行渲染
        
        Args:
            file_name: 命令文件名或相对路径
            render_variables: 用于 Jinja2 渲染的变量字典，如果为 None 则使用空字典
            
        Returns:
            Optional[str]: 渲染后的文件内容，如果文件不存在或渲染失败则返回None
        """
        if render_variables is None:
            render_variables = {}
            
        # 首先读取命令文件
        command_file = self.read_command_file(file_name)
        if command_file is None:
            return None
        
        try:
            # 使用 format_str_jinja2 进行渲染
            rendered_content = format_str_jinja2(command_file.content, **render_variables)
            
            logger.info(f"成功渲染命令文件: {file_name}, 使用变量: {render_variables}")
            return rendered_content
            
        except Exception as e:
            logger.error(f"渲染命令文件时出错: {file_name}, 错误: {str(e)}")
            return None
    
    def analyze_command_file(self, file_name: str) -> Optional[CommandFileAnalysisResult]:
        """
        分析指定的命令文件，提取其中的Jinja2变量
        
        Args:
            file_name: 命令文件名或相对路径
            
        Returns:
            Optional[CommandFileAnalysisResult]: 分析结果，如果文件不存在则返回None
        """
        command_file = self.read_command_file(file_name)
        if command_file is None:
            return None
        
        try:
            return analyze_command_file(command_file.file_path, command_file.content)
        except Exception as e:
            logger.error(f"分析命令文件时出错: {str(e)}")
            return None
    
    def get_all_variables(self, recursive: bool = False) -> Dict[str, Set[str]]:
        """
        获取所有命令文件中的变量，支持多目录合并
        
        Args:
            recursive: 是否递归搜索子目录
            
        Returns:
            Dict[str, Set[str]]: 文件路径到变量集合的映射
        """
        result: Dict[str, Set[str]] = {}
        
        list_result = self.list_command_files(recursive)
        if not list_result.success:
            logger.error("获取命令文件列表失败")
            return result
        
        for file_name in list_result.command_files:
            command_file = self.read_command_file(file_name)
            if command_file is None:
                continue
            
            try:
                variables = extract_jinja2_variables(command_file.content)
                result[file_name] = variables
            except Exception as e:
                logger.error(f"提取文件 {file_name} 的变量时出错: {str(e)}")
        
        return result
    
    def get_command_file_path(self, file_name: str) -> Optional[str]:
        """
        获取命令文件的完整路径，按优先级从多个目录中查找
        
        Args:
            file_name: 命令文件名或相对路径
            
        Returns:
            Optional[str]: 命令文件的完整路径，如果不存在则返回None
        """
        # 按优先级顺序查找文件
        for commands_dir in self.commands_directories:
            file_path = os.path.join(commands_dir, file_name)
            if os.path.isfile(file_path):
                return file_path
        
        # 如果没找到，返回主目录中的路径（保持向后兼容性）
        return os.path.join(self.commands_dir, file_name)
    
    def get_all_command_directories(self) -> List[str]:
        """
        获取所有命令目录路径
        
        Returns:
            List[str]: 所有命令目录路径列表，按优先级排序
        """
        return self.commands_directories.copy()
    
    def _get_absolute_path(self, file_path: str) -> str:
        """
        获取文件的绝对路径
        
        Args:
            file_path: 文件相对路径或绝对路径
            
        Returns:
            str: 文件的绝对路径
        """
        if os.path.isabs(file_path):
            return file_path
        else:
            return os.path.join(self.commands_dir, file_path)
