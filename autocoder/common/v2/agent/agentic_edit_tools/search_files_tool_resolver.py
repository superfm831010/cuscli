import os
import re
import glob
from typing import Dict, Any, Optional, List, Union

from pydantic import BaseModel, Field
from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import BaseToolResolver
from autocoder.common.v2.agent.agentic_edit_types import SearchFilesTool, ToolResult
from autocoder.common import AutoCoderArgs
from autocoder.common.ignorefiles.ignore_file_utils import should_ignore
from loguru import logger
import typing
import json

# Import token counter and wrap_llm_hint modules
from autocoder.common.tokens import count_string_tokens
from autocoder.common.wrap_llm_hint.utils import add_hint_to_text

if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class SearchParameters(BaseModel):
    """Strongly typed search parameters for file searching operations.
    
    This class ensures type safety and validation for all search-related parameters.
    """
    search_path_str: str = Field(..., description="Original search path string for error messages")
    regex_pattern: str = Field(..., description="Regular expression pattern to search for")
    file_pattern: str = Field(..., description="Glob pattern for file filtering (e.g., '*.py')")
    source_dir: str = Field(..., description="Source directory path")
    absolute_source_dir: str = Field(..., description="Absolute path to source directory")
    absolute_search_path: str = Field(..., description="Absolute path to search directory")
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Make the class immutable
        extra = "forbid"  # Prevent extra fields


class SearchErrorInfo(BaseModel):
    """Information about errors encountered during search operations."""
    file_path: str = Field(..., description="Path to the file/directory that caused the error")
    error_type: str = Field(..., description="Type of error (e.g., 'PermissionError', 'FileNotFoundError')")
    error_message: str = Field(..., description="Detailed error message")
    
    class Config:
        """Pydantic configuration."""
        frozen = True
        extra = "forbid"


class SearchMatchInfo(BaseModel):
    """Information about a single search match."""
    path: str = Field(..., description="Relative path to the file containing the match")
    line_number: int = Field(..., description="Line number where the match was found (1-indexed)")
    match_line: str = Field(..., description="The line content that matched the pattern")
    context: str = Field(..., description="Context lines around the match")
    
    class Config:
        """Pydantic configuration."""
        frozen = True
        extra = "forbid"


class SearchResultContent(BaseModel):
    """Content structure for search operation results."""
    matches: List[SearchMatchInfo] = Field(..., description="List of search matches found")
    errors: List[SearchErrorInfo] = Field(..., description="List of errors encountered during search")
    
    class Config:
        """Pydantic configuration."""
        frozen = True
        extra = "forbid"


class SearchFilesToolResolver(BaseToolResolver):
    """Resolver for searching files with regex patterns.
    
    This class provides functionality to search for text patterns within files
    using regular expressions, with support for file pattern filtering and
    security checks to prevent access outside the project directory.
    """
    
    # Constants for search configuration
    MAX_SEARCH_RESULTS = 200
    CONTEXT_LINES_BEFORE = 2
    CONTEXT_LINES_AFTER = 3
    DEFAULT_FILE_PATTERN = "*"
    DEFAULT_SOURCE_DIR = "."
    
    def __init__(self, agent: Optional['AgenticEdit'], tool: SearchFilesTool, args: AutoCoderArgs):
        """Initialize the search files tool resolver.
        
        Args:
            agent: Optional AgenticEdit instance
            tool: SearchFilesTool configuration
            args: AutoCoder arguments containing source directory
        """
        super().__init__(agent, tool, args)
        self.tool: SearchFilesTool = tool

    def search_in_dir(self, base_dir: str, regex_pattern: str, file_pattern: str, 
                     source_dir: str, is_shadow: bool = False, 
                     compiled_regex: Optional[re.Pattern] = None) -> tuple[List[SearchMatchInfo], List[SearchErrorInfo]]:
        """Search for regex patterns in files within a directory.
        
        Args:
            base_dir: Directory to search in
            regex_pattern: Regular expression pattern to search for
            file_pattern: Glob pattern for file filtering (e.g., '*.py')
            source_dir: Source directory for calculating relative paths
            is_shadow: Whether this is a shadow directory search (legacy parameter)
            compiled_regex: Pre-compiled regex pattern for efficiency
            
        Returns:
            Tuple of (search match objects, error information list)
        """
        search_results = []
        errors = []
        search_glob_pattern = os.path.join(base_dir, "**", file_pattern)

        logger.info(
            f"Searching for regex '{regex_pattern}' in files matching '{file_pattern}' "
            f"under '{base_dir}' (shadow: {is_shadow}) with ignore rules applied."
        )

        if compiled_regex is None:
            compiled_regex = re.compile(regex_pattern)

        try:
            matching_files = glob.glob(search_glob_pattern, recursive=True)
        except (PermissionError, OSError) as e:
            error_info = SearchErrorInfo(
                file_path=base_dir,
                error_type=type(e).__name__,
                error_message=f"Cannot access directory for glob search: {str(e)}"
            )
            errors.append(error_info)
            logger.warning(f"Cannot access directory {base_dir}: {e}")
            return search_results, errors
        
        for filepath in matching_files:
            if not self._should_process_file(filepath):
                continue
                
            file_matches, file_errors = self._search_in_file_with_errors(filepath, compiled_regex, source_dir)
            search_results.extend(file_matches)
            errors.extend(file_errors)

        return search_results, errors
    
    def _should_process_file(self, filepath: str) -> bool:
        """Check if a file should be processed for searching.
        
        Args:
            filepath: Path to the file to check
            
        Returns:
            True if the file should be processed, False otherwise
        """
        abs_path = os.path.abspath(filepath)
        return os.path.isfile(filepath) and not should_ignore(abs_path)
    
    def _search_in_file(self, filepath: str, compiled_regex: re.Pattern, 
                       source_dir: str) -> List[SearchMatchInfo]:
        """Search for regex matches within a single file.
        
        Args:
            filepath: Path to the file to search
            compiled_regex: Compiled regular expression pattern
            source_dir: Source directory for calculating relative paths
            
        Returns:
            List of SearchMatchInfo objects for this file
        """
        file_matches, _ = self._search_in_file_with_errors(filepath, compiled_regex, source_dir)
        return file_matches
    
    def _search_in_file_with_errors(self, filepath: str, compiled_regex: re.Pattern, 
                                   source_dir: str) -> tuple[List[SearchMatchInfo], List[SearchErrorInfo]]:
        """Search for regex matches within a single file, collecting errors.
        
        Args:
            filepath: Path to the file to search
            compiled_regex: Compiled regular expression pattern
            source_dir: Source directory for calculating relative paths
            
        Returns:
            Tuple of (SearchMatchInfo objects, error information list)
        """
        file_matches = []
        errors = []
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
                
            for line_index, line in enumerate(lines):
                if compiled_regex.search(line):
                    match_info = self._create_match_info(
                        filepath, line_index, line, lines, source_dir
                    )
                    file_matches.append(match_info)
                    
        except (PermissionError, OSError, UnicodeDecodeError) as e:
            error_info = SearchErrorInfo(
                file_path=filepath,
                error_type=type(e).__name__,
                error_message=f"Cannot read file: {str(e)}"
            )
            errors.append(error_info)
            logger.warning(f"Could not read or process file {filepath}: {e}")
        except Exception as e:
            error_info = SearchErrorInfo(
                file_path=filepath,
                error_type=type(e).__name__,
                error_message=f"Unexpected error: {str(e)}"
            )
            errors.append(error_info)
            logger.warning(f"Unexpected error processing file {filepath}: {e}")
            
        return file_matches, errors
    
    def _create_match_info(self, filepath: str, line_index: int, line: str, 
                          all_lines: List[str], source_dir: str) -> SearchMatchInfo:
        """Create a match information object.
        
        Args:
            filepath: Path to the file containing the match
            line_index: Zero-based index of the matching line
            line: The matching line content
            all_lines: All lines in the file for context
            source_dir: Source directory for calculating relative paths
            
        Returns:
            SearchMatchInfo object containing match information
        """
        context_start = max(0, line_index - self.CONTEXT_LINES_BEFORE)
        context_end = min(len(all_lines), line_index + self.CONTEXT_LINES_AFTER)
        
        context_lines = [
            f"{j + 1}: {all_lines[j]}" 
            for j in range(context_start, context_end)
        ]
        context = "".join(context_lines)
        
        relative_path = os.path.relpath(filepath, source_dir)
        
        return SearchMatchInfo(
            path=relative_path,
            line_number=line_index + 1,
            match_line=line.strip(),
            context=context.strip()
        )

    def search_files_normal(self, search_path_str: str, regex_pattern: str, 
                           file_pattern: str, source_dir: str, 
                           absolute_source_dir: str, absolute_search_path: str) -> Union[ToolResult, tuple[List[SearchMatchInfo], List[SearchErrorInfo]]]:
        """Search files directly in the specified directory or file.
        
        Args:
            search_path_str: Original search path string (for error messages)
            regex_pattern: Regular expression pattern to search for
            file_pattern: Glob pattern for file filtering
            source_dir: Source directory path
            absolute_source_dir: Absolute path to source directory
            absolute_search_path: Absolute path to search directory or file
            
        Returns:
            ToolResult on error, or tuple of (SearchMatchInfo objects, error information) on success
        """
        # Perform security and validation checks
        validation_result = self._validate_search_path(
            search_path_str, absolute_source_dir, absolute_search_path
        )
        if validation_result:
            return validation_result

        try:
            compiled_regex = re.compile(regex_pattern)
            
            # Check if the path is a file or directory
            if os.path.isfile(absolute_search_path):
                # Search in single file
                logger.info(f"Searching for regex '{regex_pattern}' in file '{absolute_search_path}'")
                if not self._should_process_file(absolute_search_path):
                    return [], []
                search_results, errors = self._search_in_file_with_errors(absolute_search_path, compiled_regex, source_dir)
            else:
                # Search in directory
                search_results, errors = self.search_in_dir(
                    absolute_search_path, regex_pattern, file_pattern, 
                    source_dir, is_shadow=False, compiled_regex=compiled_regex
                )
            
            return search_results, errors

        except re.error as e:
            error_msg = f"Invalid regex pattern: {e}"
            logger.error(f"Invalid regex pattern '{regex_pattern}': {e}")
            return ToolResult(success=False, message=error_msg)
            
        except Exception as e:
            error_msg = f"An unexpected error occurred during search: {str(e)}"
            logger.error(f"Error during file search: {str(e)}")
            return ToolResult(success=False, message=error_msg)
    
    def _validate_search_path(self, search_path_str: str, absolute_source_dir: str, 
                             absolute_search_path: str) -> Optional[ToolResult]:
        """Validate the search path for security and existence.
        
        Args:
            search_path_str: Original search path string (for error messages)
            absolute_source_dir: Absolute path to source directory
            absolute_search_path: Absolute path to search directory or file
            
        Returns:
            ToolResult with error if validation fails, None if validation passes
        """
        # Security check: prevent access outside project directory
        if not absolute_search_path.startswith(absolute_source_dir):
            return ToolResult(
                success=False, 
                message=f"Error: Access denied. Attempted to search outside the project directory: {search_path_str}"
            )

        # Check if path exists
        if not os.path.exists(absolute_search_path):
            return ToolResult(
                success=False, 
                message=f"Error: Search path not found: {search_path_str}"
            )
            
        return None

    def resolve(self) -> ToolResult:
        """Resolve the search files tool by executing the search operation.
        
        Returns:
            ToolResult containing search results or error information
        """
        search_params = self._extract_search_parameters()
        
        result = self.search_files_normal(
            search_params.search_path_str,
            search_params.regex_pattern,
            search_params.file_pattern,
            search_params.source_dir,
            search_params.absolute_source_dir,
            search_params.absolute_search_path
        )

        return self._format_search_result(result)
    
    def _extract_search_parameters(self) -> SearchParameters:
        """Extract and prepare search parameters from tool configuration.
        
        Returns:
            SearchParameters instance with strongly typed parameters
        """
        search_path_str = self.tool.path
        regex_pattern = self.tool.regex
        file_pattern = self.tool.file_pattern or self.DEFAULT_FILE_PATTERN
        source_dir = self.args.source_dir or self.DEFAULT_SOURCE_DIR
        absolute_source_dir = os.path.abspath(source_dir)
        absolute_search_path = os.path.abspath(
            os.path.join(source_dir, search_path_str)
        )
        
        return SearchParameters(
            search_path_str=search_path_str,
            regex_pattern=regex_pattern,
            file_pattern=file_pattern,
            source_dir=source_dir,
            absolute_source_dir=absolute_source_dir,
            absolute_search_path=absolute_search_path
        )
    
    def _format_search_result(self, result: Union[ToolResult, tuple[List[SearchMatchInfo], List[SearchErrorInfo]]]) -> ToolResult:
        """Format the search result into a standardized ToolResult.
        
        Args:
            result: Raw search result (either ToolResult or tuple of SearchMatchInfo objects and errors)
            
        Returns:
            Formatted ToolResult
        """
        # If result is already a ToolResult (error case), return it directly
        if isinstance(result, ToolResult):
            return result
            
        # Handle successful search results (tuple of matches and errors)
        search_results, errors = result
        total_results = len(search_results)
        total_errors = len(errors)
        
        # Prepare error summary for message
        error_summary = ""
        if total_errors > 0:
            error_types = {}
            for error in errors:
                error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
            error_summary = f" Encountered {total_errors} errors: " + ", ".join([f"{count} {error_type}" for error_type, count in error_types.items()])
        
        # Prepare content with both results and errors using Pydantic model
        truncated_matches = search_results[:self.MAX_SEARCH_RESULTS] if total_results > self.MAX_SEARCH_RESULTS else search_results
        content_model = SearchResultContent(
            matches=truncated_matches,
            errors=errors
        )
        content = content_model.model_dump()
        
        # Convert content to JSON string to count tokens
        content_str = json.dumps(content, ensure_ascii=False, indent=2)
        token_count = count_string_tokens(content_str)
        
        # Check if content exceeds 5k tokens
        MAX_TOKENS = 5000
        if token_count > MAX_TOKENS:
            # Truncate to first 1000 characters
            truncated_content_str = content_str[:1000]
            
            # Add hint about truncation
            hint_message = "Search results truncated due to exceeding 5k tokens. Try narrowing your search by using more specific regex patterns or file patterns to reduce output."
            truncated_content_str = add_hint_to_text(truncated_content_str, hint_message)
            
            # Log the truncation
            logger.warning(f"Search results truncated from {token_count} tokens to first 1000 characters")
            
            # Create truncation message
            if total_results > self.MAX_SEARCH_RESULTS:
                message = (
                    f"Search completed. Found {total_results} matches (showing first {self.MAX_SEARCH_RESULTS}), "
                    f"but results were truncated due to size (original: {token_count} tokens).{error_summary}"
                )
            else:
                message = (
                    f"Search completed. Found {total_results} matches, "
                    f"but results were truncated due to size (original: {token_count} tokens).{error_summary}"
                )
            
            return ToolResult(success=True, message=message, content=truncated_content_str)
        
        # Normal case - content within token limit
        if total_results > self.MAX_SEARCH_RESULTS:
            message = (
                f"Search completed. Found {total_results} matches, "
                f"showing only the first {self.MAX_SEARCH_RESULTS}.{error_summary}"
            )
            logger.info(message)
            return ToolResult(success=True, message=message, content=content)
        else:
            message = f"Search completed. Found {total_results} matches.{error_summary}"
            logger.info(message)
            return ToolResult(success=True, message=message, content=content)
