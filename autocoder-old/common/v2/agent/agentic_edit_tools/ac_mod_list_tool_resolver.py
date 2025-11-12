import os
from typing import Optional, List
from pydantic import BaseModel
from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import BaseToolResolver
from autocoder.common.v2.agent.agentic_edit_types import ACModListTool, ToolResult
from autocoder.common.tokens import count_directory_tokens
from autocoder.common.ignorefiles.ignore_file_utils import should_ignore, DEFAULT_EXCLUDES
from loguru import logger
import typing

if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class DirectoryInfo(BaseModel):
    """Directory information model"""
    file_count: int
    tokens: int


class ACModuleInfo(BaseModel):
    """Complete AC module information model"""
    path: str
    absolute_path: str
    title: str
    file_count: int
    tokens: int


class CompactACModuleInfo(BaseModel):
    """Compact AC module information model for display"""
    path: str
    title: str
    tokens: int


class ACModListToolResolver(BaseToolResolver):
    """
    Resolver for ACModListTool - lists all directories containing .ac.mod.md files
    """
    
    def __init__(self, agent: Optional['AgenticEdit'], tool: ACModListTool, args):
        super().__init__(agent, tool, args)
        self.tool: ACModListTool = tool
        self._ignore_cache = {}  # Cache for ignore checks to improve performance

    def resolve(self) -> ToolResult:
        """
        Lists all directories containing .ac.mod.md files (AC Modules)
        
        Returns:
            ToolResult: Contains list of AC module directories and their information
        """
        try:
            # Determine search root path
            source_dir = self.args.source_dir or "."
            search_path = self.tool.path if self.tool.path else source_dir
            
            # Make absolute path
            if not os.path.isabs(search_path):
                abs_search_path = os.path.abspath(os.path.join(source_dir, search_path))
            else:
                abs_search_path = search_path
            
            if not os.path.exists(abs_search_path):
                return ToolResult(
                    success=False,
                    message=f"Search path does not exist: {search_path}"
                )
            
            if not os.path.isdir(abs_search_path):
                return ToolResult(
                    success=False,
                    message=f"Search path is not a directory: {search_path}"
                )
            
            logger.info(f"Searching for AC modules in: {abs_search_path}")
            
            # Find all AC modules
            ac_modules = self._find_ac_modules(abs_search_path, source_dir)
            
            if not ac_modules:
                formatted_content = f"Search path: {search_path}\nTotal: 0 modules\n\nNo AC modules found."
                return ToolResult(
                    success=True,
                    message="No AC modules found in the specified path",
                    content=formatted_content
                )
            
            # Format result message and content
            module_count = len(ac_modules)
            message = f"Found {module_count} AC module{'s' if module_count != 1 else ''}"
            
            # Create compact module list with only path, title, tokens
            compact_modules = []
            for module in ac_modules:
                compact_modules.append(CompactACModuleInfo(
                    path=module.path,
                    title=module.title,
                    tokens=module.tokens
                ))
            
            # Format as compact text
            module_lines = []
            for module in compact_modules:
                path_display = module.path if module.path != "." else "(root)"
                # 不显示token数量，因为默认为0
                module_lines.append(f"  • {path_display} - {module.title}")
            
            formatted_content = f"Search path: {search_path}\nTotal: {module_count} modules\n\nModules:\n" + "\n".join(module_lines)
            
            logger.info(f"Found {module_count} AC modules")
            
            return ToolResult(
                success=True,
                message=message,
                content=formatted_content
            )
            
        except Exception as e:
            logger.error(f"Error listing AC modules: {e}")
            return ToolResult(
                success=False,
                message=f"Error listing AC modules: {str(e)}"
            )
    
    def _find_ac_modules(self, search_path: str, source_dir: str) -> List[ACModuleInfo]:
        """
        Recursively find all directories containing .ac.mod.md files
        
        Args:
            search_path: Absolute path to search in
            source_dir: Source directory for relative path calculation
            
        Returns:
            List of ACModuleInfo models containing AC module information
        """
        ac_modules = []
        abs_source_dir = os.path.abspath(source_dir)
        
        try:
            for root, dirs, files in os.walk(search_path):
                # Early exit if current directory should be ignored
                if self._should_ignore_directory(root, abs_source_dir):
                    dirs.clear()  # Don't descend into ignored directories
                    continue
                    
                # Filter out ignored directories before descending into them
                dirs[:] = [d for d in dirs if not self._should_ignore_directory(os.path.join(root, d), abs_source_dir)]
                
                if ".ac.mod.md" in files:
                    # Calculate relative path from source directory
                    rel_path = os.path.relpath(root, abs_source_dir)
                    if rel_path == ".":
                        rel_path = ""
                    
                    # Try to read module title from .ac.mod.md file
                    mod_file_path = os.path.join(root, ".ac.mod.md")
                    module_title = self._extract_module_title(mod_file_path)
                    
                    # Get directory token info (默认返回0以提升性能)
                    dir_info = self._get_directory_info(root)
                    
                    module_info = ACModuleInfo(
                        path=rel_path if rel_path else ".",
                        absolute_path=root,
                        title=module_title,
                        file_count=dir_info.file_count,
                        tokens=dir_info.tokens
                    )
                    
                    ac_modules.append(module_info)
                    logger.debug(f"Found AC module: {rel_path} - {module_title}")
            
            # Sort by path for consistent ordering
            ac_modules.sort(key=lambda x: x.path)
            
        except Exception as e:
            logger.error(f"Error walking directory {search_path}: {e}")
            raise
        
        return ac_modules
    
    def _should_ignore_directory(self, dir_path: str, project_root: str) -> bool:
        """
        Check if a directory should be ignored during traversal
        
        Args:
            dir_path: Directory path to check
            project_root: Project root directory for relative path calculation
            
        Returns:
            True if directory should be ignored, False otherwise
        """
        # Check cache first for performance
        cache_key = (dir_path, project_root)
        if cache_key in self._ignore_cache:
            return self._ignore_cache[cache_key]
        
        # Fast check for common ignore patterns first (performance optimization)
        dir_name = os.path.basename(dir_path)
        if dir_name in DEFAULT_EXCLUDES:
            self._ignore_cache[cache_key] = True
            return True
            
        try:
            # Use ignorefiles module for more sophisticated filtering
            result = should_ignore(dir_path, project_root)
            self._ignore_cache[cache_key] = result
            return result
        except Exception as e:
            # Fallback to basic filtering if ignorefiles module fails
            logger.warning(f"Error checking ignore status for {dir_path}: {e}")
            self._ignore_cache[cache_key] = False
            return False
    
    def _extract_module_title(self, mod_file_path: str) -> str:
        """
        Extract module title from .ac.mod.md file
        
        Args:
            mod_file_path: Path to .ac.mod.md file
            
        Returns:
            Module title or default name
        """
        try:
            with open(mod_file_path, 'r', encoding='utf-8', errors='replace') as f:
                # Read first few lines to find the title (markdown h1)
                for line_num, line in enumerate(f):
                    line = line.strip()
                    if line.startswith("# "):
                        return line[2:].strip()
                    # Only check first 10 lines
                    if line_num >= 9:
                        break
            
            # If no title found, return a default
            return "AC Module"
            
        except Exception as e:
            logger.warning(f"Could not read title from {mod_file_path}: {e}")
            return "AC Module"
    
    def _get_directory_info(self, dir_path: str) -> DirectoryInfo:
        """
        Get basic information about directory (file count and tokens)
        
        Args:
            dir_path: Directory path
            
        Returns:
            DirectoryInfo model with file count and token information
        """
        try:
            # 为了提升性能，默认不统计token数量，直接返回0
            # 只统计文件数量（快速操作），同时应用忽略规则
            file_count = 0
            for root, dirs, files in os.walk(dir_path):
                # Early exit if current directory should be ignored
                if self._should_ignore_directory(root, dir_path):
                    dirs.clear()  # Don't descend into ignored directories
                    continue
                    
                # 跳过忽略的目录
                dirs[:] = [d for d in dirs if not self._should_ignore_directory(os.path.join(root, d), dir_path)]
                file_count += len(files)
            
            return DirectoryInfo(
                file_count=file_count,
                tokens=0  # 默认显示0以提升性能
            )
            
        except Exception as e:
            logger.warning(f"Could not get directory info for {dir_path}: {e}")
            return DirectoryInfo(
                file_count=0,
                tokens=0
            )