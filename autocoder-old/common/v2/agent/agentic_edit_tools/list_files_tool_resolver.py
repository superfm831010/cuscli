import os
from typing import Dict, Any, Optional, List, Set, Union

from pydantic import BaseModel, Field
from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import BaseToolResolver
from autocoder.common.v2.agent.agentic_edit_types import ListFilesTool, ToolResult  # Import ToolResult from types
from loguru import logger
import typing
from autocoder.common import AutoCoderArgs

from autocoder.common.ignorefiles.ignore_file_utils import should_ignore

if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class ListErrorInfo(BaseModel):
    """Information about errors encountered during list operations."""
    file_path: str = Field(..., description="Path to the file/directory that caused the error")
    error_type: str = Field(..., description="Type of error (e.g., 'PermissionError', 'FileNotFoundError')")
    error_message: str = Field(..., description="Detailed error message")
    
    class Config:
        """Pydantic configuration."""
        frozen = True
        extra = "forbid"


class ListResultContent(BaseModel):
    """Content structure for list operation results."""
    files: List[str] = Field(..., description="List of files and directories found")
    errors: List[ListErrorInfo] = Field(..., description="List of errors encountered during listing")
    
    class Config:
        """Pydantic configuration."""
        frozen = True
        extra = "forbid"


class ListFilesToolResolver(BaseToolResolver):
    def __init__(self, agent: Optional['AgenticEdit'], tool: ListFilesTool, args: AutoCoderArgs):
        super().__init__(agent, tool, args)
        self.tool: ListFilesTool = tool  # For type hinting

    def list_files_in_dir(self, base_dir: str, recursive: bool, source_dir: str, is_outside_source: bool) -> tuple[Set[str], List[ListErrorInfo]]:
        """Helper function to list files in a directory with error collection.
        
        Returns:
            Tuple of (file set, error information list)
        """
        result = set()
        errors = []
        
        try:
            if recursive:
                for root, dirs, files in os.walk(base_dir):
                    try:
                        # Modify dirs in-place to skip ignored dirs early
                        accessible_dirs = []
                        for d in dirs:
                            dir_path = os.path.join(root, d)
                            if should_ignore(dir_path):
                                continue
                            try:
                                # Test if we can access the directory
                                os.listdir(dir_path)
                                accessible_dirs.append(d)
                            except (PermissionError, OSError) as e:
                                error_info = ListErrorInfo(
                                    file_path=dir_path,
                                    error_type=type(e).__name__,
                                    error_message=f"Cannot access directory: {str(e)}"
                                )
                                errors.append(error_info)
                                logger.warning(f"Cannot access directory {dir_path}: {e}")
                        dirs[:] = accessible_dirs
                        
                        # Process files in current directory
                        for name in files:
                            full_path = os.path.join(root, name)
                            if should_ignore(full_path):
                                continue
                            try:
                                # Test if we can access the file
                                os.stat(full_path)
                                display_path = os.path.relpath(full_path, source_dir) if not is_outside_source else full_path
                                result.add(display_path)
                            except (PermissionError, OSError) as e:
                                error_info = ListErrorInfo(
                                    file_path=full_path,
                                    error_type=type(e).__name__,
                                    error_message=f"Cannot access file: {str(e)}"
                                )
                                errors.append(error_info)
                                logger.warning(f"Cannot access file {full_path}: {e}")
                        
                        # Add accessible directories to result
                        for d in dirs:
                            full_path = os.path.join(root, d)
                            display_path = os.path.relpath(full_path, source_dir) if not is_outside_source else full_path
                            result.add(display_path + "/")
                            
                    except (PermissionError, OSError) as e:
                        error_info = ListErrorInfo(
                            file_path=root,
                            error_type=type(e).__name__,
                            error_message=f"Cannot access directory during walk: {str(e)}"
                        )
                        errors.append(error_info)
                        logger.warning(f"Cannot access directory {root} during walk: {e}")
                        break  # Stop walking this branch
            else:
                try:
                    items = os.listdir(base_dir)
                    for item in items:
                        full_path = os.path.join(base_dir, item)
                        if should_ignore(full_path):
                            continue
                        try:
                            display_path = os.path.relpath(full_path, source_dir) if not is_outside_source else full_path
                            if os.path.isdir(full_path):
                                result.add(display_path + "/")
                            else:
                                result.add(display_path)
                        except (PermissionError, OSError) as e:
                            error_info = ListErrorInfo(
                                file_path=full_path,
                                error_type=type(e).__name__,
                                error_message=f"Cannot access item: {str(e)}"
                            )
                            errors.append(error_info)
                            logger.warning(f"Cannot access item {full_path}: {e}")
                except (PermissionError, OSError) as e:
                    error_info = ListErrorInfo(
                        file_path=base_dir,
                        error_type=type(e).__name__,
                        error_message=f"Cannot list directory: {str(e)}"
                    )
                    errors.append(error_info)
                    logger.warning(f"Cannot list directory {base_dir}: {e}")
        except Exception as e:
            error_info = ListErrorInfo(
                file_path=base_dir,
                error_type=type(e).__name__,
                error_message=f"Unexpected error: {str(e)}"
            )
            errors.append(error_info)
            logger.warning(f"Unexpected error listing files in {base_dir}: {e}")
            
        return result, errors
        

    def list_files_normal(self, list_path_str: str, recursive: bool, source_dir: str, absolute_source_dir: str, absolute_list_path: str) -> Union[ToolResult, tuple[List[str], List[ListErrorInfo]]]:
        """List files directly without using shadow manager with error collection.
        
        Returns:
            ToolResult on error, or tuple of (file list, error information) on success
        """
        # Security check: Allow listing outside source_dir IF the original path is outside?
        is_outside_source = not absolute_list_path.startswith(absolute_source_dir)
        if is_outside_source:
            logger.warning(f"Listing path is outside the project source directory: {list_path_str}")

        # Validate that the directory exists
        if not os.path.exists(absolute_list_path):
            return ToolResult(success=False, message=f"Error: Path not found: {list_path_str}")
        if not os.path.isdir(absolute_list_path):
            return ToolResult(success=False, message=f"Error: Path is not a directory: {list_path_str}")

        # Collect files from the directory
        files_set, errors = self.list_files_in_dir(absolute_list_path, recursive, source_dir, is_outside_source)

        try:
            sorted_files = sorted(files_set)
            return sorted_files, errors
        except Exception as e:
            logger.error(f"Error sorting files in '{list_path_str}': {str(e)}")
            return ToolResult(success=False, message=f"An unexpected error occurred while listing files: {str(e)}")

    def resolve(self) -> ToolResult:
        """Resolve the list files tool by calling the appropriate implementation"""
        list_path_str = self.tool.path
        recursive = self.tool.recursive or False
        source_dir = self.args.source_dir or "."
        absolute_source_dir = os.path.abspath(source_dir)
        absolute_list_path = os.path.abspath(os.path.join(source_dir, list_path_str))

        # Use the normal implementation since shadow_manager is no longer available
        result = self.list_files_normal(list_path_str, recursive, source_dir, absolute_source_dir, absolute_list_path)

        # Handle the case where the implementation returns a ToolResult (error case)
        if isinstance(result, ToolResult):
            return result
            
        # Handle successful results (tuple of files and errors)
        files_list, errors = result
        total_items = len(files_list)
        total_errors = len(errors)
        
        # Prepare error summary for message
        error_summary = ""
        if total_errors > 0:
            error_types = {}
            for error in errors:
                error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
            error_summary = f" Encountered {total_errors} errors: " + ", ".join([f"{count} {error_type}" for error_type, count in error_types.items()])
        
        # Prepare content with both results and errors using Pydantic model
        truncated_files = files_list[:200] if total_items > 200 else files_list
        content_model = ListResultContent(
            files=truncated_files,
            errors=errors
        )
        content = content_model.model_dump()
        
        # Limit results to 200 if needed
        if total_items > 200:
            message = f"Successfully listed contents of '{list_path_str}' (Recursive: {recursive}). Found {total_items} items, showing only the first 200.{error_summary}"
            logger.info(message)
            return ToolResult(success=True, message=message, content=content)
        else:
            message = f"Successfully listed contents of '{list_path_str}' (Recursive: {recursive}). Found {total_items} items.{error_summary}"
            return ToolResult(success=True, message=message, content=content)
