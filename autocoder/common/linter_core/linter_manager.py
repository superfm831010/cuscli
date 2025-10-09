"""
Linter manager for coordinating multiple linters and batch operations.
"""

import concurrent.futures
from typing import List, Dict, Optional, Any, Union, Callable
from pathlib import Path
import time
from collections import defaultdict

from .base_linter import BaseLinter
from .linter_factory import LinterFactory
from .models.lint_result import LintResult
from .formatters.base_formatter import BaseLintOutputFormatter
from .formatters.raw_formatter import RawLintOutputFormatter
from .config_loader import LinterConfigLoader


class LinterManager:
    """
    Manager class for coordinating multiple linters and handling batch operations.
    
    This class provides high-level interfaces for linting files and directories,
    managing configurations, and coordinating multiple language linters.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, source_dir: Optional[str] = None):
        """
        Initialize the linter manager.
        
        Args:
            config: Global configuration dictionary. If None, will try to load
                   configuration from files in priority order:
                   1. Explicit config path (if provided via config_path)
                   2. Environment variable AUTOCODER_LINTER_CONFIG
                   3. Project config file (.autocoderlinters/)
                   4. Global user config file (~/.auto-coder/.autocoderlinters/)
                   5. Default configuration
            source_dir: Base directory for configuration file resolution
        """
        self.source_dir = source_dir or "."
        self.global_config = self._load_config(config)
        self.linters: Dict[str, BaseLinter] = {}
        self.max_workers = self.global_config.get('max_workers', 4)
        self.timeout = self.global_config.get('timeout', 300)  # 5 minutes default
        self.output_formatter: BaseLintOutputFormatter = self._initialize_formatter()
        
        # Initialize available linters
        self._initialize_linters()
    
    def _load_config(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Load configuration from user input or configuration files.
        
        Args:
            config: User provided configuration
            
        Returns:
            Dict[str, Any]: Merged configuration
        """
        if config is not None:
            return config
        
        # Use the new centralized configuration loader
        return LinterConfigLoader.load_manager_config(source_dir=self.source_dir)
    
    def _initialize_linters(self) -> None:
        """Initialize available linters based on the factory."""
        for language in LinterFactory.get_supported_languages():
            linter_config = self.global_config.get(f'{language}_config', {})
            linter = LinterFactory.create_linter(language, linter_config)
            
            if linter and linter.is_available():
                self.linters[language] = linter

    def _initialize_formatter(self) -> BaseLintOutputFormatter:
        """Initialize manager-level formatter; default to Raw.

        Manager-level formatter can be used for aggregated formatting of
        multi-file results. Individual linters still own their per-result
        formatting via their own configured formatter.
        """
        candidate = self.global_config.get('formatter') or self.global_config.get('formatter_class')
        if candidate is None:
            return RawLintOutputFormatter()
        if isinstance(candidate, BaseLintOutputFormatter):
            return candidate
        try:
            if issubclass(candidate, BaseLintOutputFormatter):  # type: ignore[arg-type]
                return candidate()  # type: ignore[call-arg]
        except Exception:
            pass
        return RawLintOutputFormatter()
    
    def lint_file(self, file_path: Union[str, Path], 
                  language: Optional[str] = None) -> LintResult:
        """
        Lint a single file.
        
        Args:
            file_path: Path to the file to lint
            language: Optional language override (auto-detected if not provided)
            
        Returns:
            LintResult containing any issues found
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return LintResult(
                linter_name="LinterManager",
                success=False,
                error_message=f"File not found: {file_path}"
            )
        
        # Determine the linter to use
        if language:
            linter = self.linters.get(language.lower())
            if not linter:
                return LintResult(
                    linter_name="LinterManager",
                    success=False,
                    error_message=f"No available linter for language: {language}"
                )
        else:
            linter = self._get_linter_for_file(file_path)
            if not linter:
                return LintResult(
                    linter_name="LinterManager",
                    success=False,
                    error_message=f"No available linter for file: {file_path}"
                )
        
        # Lint the file
        try:
            return linter.lint_file(file_path)
        except Exception as e:
            return LintResult(
                linter_name=linter.name,
                success=False,
                error_message=f"Error linting file {file_path}: {str(e)}"
            )
    
    def lint_files(self, file_paths: List[Union[str, Path]], 
                   parallel: bool = True) -> Dict[str, LintResult]:
        """
        Lint multiple files.
        
        Args:
            file_paths: List of file paths to lint
            parallel: Whether to use parallel processing
            
        Returns:
            Dictionary mapping file paths to their lint results
        """
        results = {}
        
        if parallel and len(file_paths) > 1:
            # Use parallel processing
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_file = {
                    executor.submit(self.lint_file, file_path): str(file_path)
                    for file_path in file_paths
                }
                
                # Collect results
                for future in concurrent.futures.as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        results[file_path] = future.result()
                    except Exception as e:
                        results[file_path] = LintResult(
                            linter_name="LinterManager",
                            success=False,
                            error_message=f"Error processing {file_path}: {str(e)}"
                        )
        else:
            # Sequential processing
            for file_path in file_paths:
                results[str(file_path)] = self.lint_file(file_path)
        
        return results

    def format_results(self, results: Dict[str, LintResult]) -> Dict[str, Any]:
        """Format multi-file results using the manager-level formatter."""
        return self.output_formatter.format_results(results)
    
    def lint_directory(self, directory: Union[str, Path], 
                      recursive: bool = True,
                      include_patterns: Optional[List[str]] = None,
                      exclude_patterns: Optional[List[str]] = None,
                      parallel: bool = True) -> Dict[str, LintResult]:
        """
        Lint all supported files in a directory.
        
        Args:
            directory: Directory to scan for files
            recursive: Whether to scan subdirectories recursively
            include_patterns: Optional list of patterns to include (glob style)
            exclude_patterns: Optional list of patterns to exclude (glob style)
            parallel: Whether to use parallel processing
            
        Returns:
            Dictionary mapping file paths to their lint results
        """
        directory = Path(directory)
        
        if not directory.exists():
            return {
                str(directory): LintResult(
                    linter_name="LinterManager",
                    success=False,
                    error_message=f"Directory not found: {directory}"
                )
            }
        
        # Find files to lint
        files_to_lint = self._find_files_to_lint(
            directory, recursive, include_patterns, exclude_patterns
        )
        
        # Lint the files
        return self.lint_files(files_to_lint, parallel)
    
    def get_summary_report(self, results: Dict[str, LintResult]) -> Dict[str, Any]:
        """
        Generate a summary report from lint results.
        
        Args:
            results: Dictionary of lint results from lint_files or lint_directory
            
        Returns:
            Summary report dictionary
        """
        total_files = len(results)
        successful_files = sum(1 for result in results.values() if result.success)
        failed_files = total_files - successful_files
        
        # Count files with issues
        files_with_issues = sum(
            1 for result in results.values() 
            if result.success and result.has_issues
        )
        
        # Count total issues (files with non-empty lint_output)
        total_issues = sum(
            1 for result in results.values()
            if result.success and result.has_issues
        )
        
        # Calculate execution time
        total_execution_time = sum(
            result.execution_time for result in results.values() if result.success
        )
        
        return {
            'total_files': total_files,
            'successful_files': successful_files,
            'failed_files': failed_files,
            'files_with_issues': files_with_issues,
            'total_issues': total_issues,
            'total_execution_time': total_execution_time,
            'average_execution_time': total_execution_time / max(successful_files, 1)
        }
    

    
    def _get_linter_for_file(self, file_path: Path) -> Optional[BaseLinter]:
        """Get the appropriate linter for a file."""
        if not LinterFactory.is_file_supported(file_path):
            return None
        
        # Get the language for this file extension
        extension = file_path.suffix.lower()
        for language, linter in self.linters.items():
            if extension in linter.supported_extensions:
                return linter
        
        return None
    
    def _find_files_to_lint(self, directory: Path, recursive: bool,
                           include_patterns: Optional[List[str]],
                           exclude_patterns: Optional[List[str]]) -> List[Path]:
        """Find files to lint in a directory."""
        files = []
        supported_extensions = LinterFactory.get_supported_extensions()
        
        # Get all files
        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"
        
        for file_path in directory.glob(pattern):
            if not file_path.is_file():
                continue
            
            # Check if file has supported extension
            if file_path.suffix.lower() not in supported_extensions:
                continue
            
            # Apply include patterns
            if include_patterns:
                if not any(file_path.match(pattern) for pattern in include_patterns):
                    continue
            
            # Apply exclude patterns
            if exclude_patterns:
                if any(file_path.match(pattern) for pattern in exclude_patterns):
                    continue
            
            files.append(file_path)
        
        return files
    
    def get_available_linters(self) -> Dict[str, bool]:
        """Get information about available linters."""
        return {
            language: linter.is_available()
            for language, linter in self.linters.items()
        }
    
    def add_linter(self, language: str, linter: BaseLinter) -> None:
        """Add a custom linter to the manager."""
        if linter.is_available():
            self.linters[language.lower()] = linter
    
    def remove_linter(self, language: str) -> None:
        """Remove a linter from the manager."""
        language = language.lower()
        if language in self.linters:
            del self.linters[language] 