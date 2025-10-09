"""
Simple data models for lint results.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class LintResult:
    """Simple result from linting a file."""
    
    file_path: str
    success: bool
    output: str = ""  # Raw output from the linter tool
    error: Optional[str] = None  # Error message if linting failed
    tool: str = ""  # Tool that generated this result (e.g., "flake8", "mypy")
    
    @property
    def has_issues(self) -> bool:
        """Check if there are any issues (non-empty output usually means issues)."""
        return bool(self.output.strip())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'file_path': self.file_path,
            'success': self.success,
            'output': self.output,
            'error': self.error,
            'tool': self.tool,
            'has_issues': self.has_issues
        }