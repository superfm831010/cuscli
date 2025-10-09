"""
Main Linter class that provides a simple interface for code checking.
"""

import concurrent.futures
from typing import Dict, List, Optional, Union, Any
from pathlib import Path

from .base_linter import BaseLinter
from .models.lint_result import LintResult
from .linters import PythonLinter, TypeScriptLinter


class Linter:
    """Simple interface for linting files across multiple languages."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the linter.
        
        Args:
            config: Optional configuration with keys:
                - max_workers: Maximum parallel workers (default: 4)
                - python: Python linter config
                - typescript: TypeScript linter config
        """
        self.config = config or {}
        self.max_workers = self.config.get('max_workers', 4)
        
        # Initialize available linters
        self._linters: Dict[str, BaseLinter] = {}
        self._init_linters()
    
    def _init_linters(self) -> None:
        """Initialize all available linters."""
        # Python linter
        python_config = self.config.get('python', {})
        python_linter = PythonLinter(python_config)
        if python_linter.is_available():
            self._linters['python'] = python_linter
        
        # TypeScript linter
        ts_config = self.config.get('typescript', {})
        ts_linter = TypeScriptLinter(ts_config)
        if ts_linter.is_available():
            self._linters['typescript'] = ts_linter
    
    def check_file(self, file_path: Union[str, Path]) -> Optional[LintResult]:
        """
        Check a single file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            LintResult if the file can be checked, None otherwise
        """
        path = Path(file_path)
        
        if not path.exists():
            return LintResult(
                file_path=str(path),
                success=False,
                error=f"File not found: {path}"
            )
        
        # Find appropriate linter
        for linter in self._linters.values():
            if linter.can_check(path):
                return linter.check_file(path)
        
        return None  # No linter available for this file type
    
    def check_files(self, file_paths: List[Union[str, Path]], 
                   parallel: bool = True) -> Dict[str, LintResult]:
        """
        Check multiple files.
        
        Args:
            file_paths: List of file paths to check
            parallel: Whether to use parallel processing
            
        Returns:
            Dictionary mapping file paths to their results
        """
        results = {}
        
        if parallel and len(file_paths) > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_file = {
                    executor.submit(self.check_file, fp): str(fp) 
                    for fp in file_paths
                }
                
                for future in concurrent.futures.as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        result = future.result()
                        if result:
                            results[file_path] = result
                    except Exception as e:
                        results[file_path] = LintResult(
                            file_path=file_path,
                            success=False,
                            error=str(e)
                        )
        else:
            for file_path in file_paths:
                result = self.check_file(file_path)
                if result:
                    results[str(file_path)] = result
        
        return results
    
    def check_directory(self, directory: Union[str, Path], 
                       recursive: bool = True,
                       extensions: Optional[List[str]] = None) -> Dict[str, LintResult]:
        """
        Check all supported files in a directory.
        
        Args:
            directory: Directory to check
            recursive: Whether to check subdirectories
            extensions: Specific extensions to check (None = all supported)
            
        Returns:
            Dictionary mapping file paths to their results
        """
        path = Path(directory)
        if not path.exists():
            return {
                str(path): LintResult(
                    file_path=str(path),
                    success=False,
                    error=f"Directory not found: {path}"
                )
            }
        
        # Get all supported extensions if not specified
        if extensions is None:
            extensions = []
            for linter in self._linters.values():
                extensions.extend(linter.extensions)
        
        # Find files
        files = []
        pattern = "**/*" if recursive else "*"
        for ext in set(extensions):
            files.extend(path.glob(f"{pattern}{ext}"))
        
        return self.check_files(files)
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return list(self._linters.keys())
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of all supported file extensions."""
        extensions = []
        for linter in self._linters.values():
            extensions.extend(linter.extensions)
        return list(set(extensions))
    
    def is_available(self, language: str) -> bool:
        """Check if a specific language linter is available."""
        return language in self._linters