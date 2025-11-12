"""
Simple base class for language-specific linters.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
from pathlib import Path

from .models.lint_result import LintResult


class BaseLinter(ABC):
    """Base class for all language linters."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize with optional configuration."""
        self.config = config or {}
    
    @property
    def name(self) -> str:
        """Name of the linter."""
        return self.__class__.__name__
    
    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """Supported file extensions (e.g., ['.py', '.pyi'])."""
        pass
    
    @property
    @abstractmethod
    def language_name(self) -> str:
        """Human-readable language name."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the linter tools are available."""
        pass
    
    @abstractmethod
    def lint_file(self, file_path: Union[str, Path]) -> LintResult:
        """
        Lint a single file and return the result.
        
        Args:
            file_path: Path to the file to lint
            
        Returns:
            LintResult with the linting output
        """
        pass
    
    def can_lint_file(self, file_path: Union[str, Path]) -> bool:
        """Check if this linter can handle the given file."""
        path = Path(file_path)
        return path.suffix.lower() in self.supported_extensions
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default) 