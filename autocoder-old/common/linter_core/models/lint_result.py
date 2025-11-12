"""
Data models for lint results.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class LintResult:
    """Represents the result of linting a file."""
    
    linter_name: str
    files_checked: List[str] = field(default_factory=list)
    lint_output: str = ""  # Raw output from linter
    execution_time: float = 0.0
    success: bool = True
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Backward compatibility properties
    @property
    def file_name(self) -> str:
        """Get the first file name for backward compatibility."""
        return self.files_checked[0] if self.files_checked else ""
    
    @file_name.setter
    def file_name(self, value: str) -> None:
        """Set the file name for backward compatibility."""
        if not self.files_checked:
            self.files_checked = [value]
        else:
            self.files_checked[0] = value
    
    @property
    def lint_result(self) -> str:
        """Get raw lint result for backward compatibility."""
        return self.lint_output
    
    @lint_result.setter
    def lint_result(self, value: str) -> None:
        """Set raw lint result for backward compatibility."""
        self.lint_output = value
    
    @property
    def has_issues(self) -> bool:
        """Check if the result has any issues."""
        return bool(self.lint_output.strip())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        result_dict = {
            'linter_name': self.linter_name,
            'files_checked': self.files_checked,
            'lint_output': self.lint_output,
            'execution_time': self.execution_time,
            'success': self.success,
            'error_message': self.error_message,
            'metadata': self.metadata
        }
        
        # Add backward compatibility fields
        result_dict['file_name'] = self.file_name
        result_dict['lint_result'] = self.lint_result
        
        return result_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LintResult':
        """Create a result from a dictionary."""
        # Handle backward compatibility with old format
        files_checked = data.get('files_checked', [])
        if not files_checked and 'file_name' in data:
            files_checked = [data['file_name']]
        
        # Handle lint_output vs lint_result
        lint_output = data.get('lint_output', '')
        if not lint_output and 'lint_result' in data:
            lint_output = data['lint_result']
        
        result = cls(
            linter_name=data['linter_name'],
            files_checked=files_checked,
            lint_output=lint_output,
            execution_time=data.get('execution_time', 0.0),
            success=data.get('success', True),
            error_message=data.get('error_message', ''),
            metadata=data.get('metadata', {})
        )
        
        return result
