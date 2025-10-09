"""
Python linter implementation using flake8 and optionally mypy.

Simplified to pass raw output to formatters without parsing.
"""

from __future__ import annotations

import subprocess
from typing import List, Optional, Dict, Any, Union
from pathlib import Path

from ..base_linter import BaseLinter
from ..models.lint_result import LintResult


class PythonLinter(BaseLinter):
    """Python linter using flake8 (and optionally mypy) with raw output."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.use_mypy: bool = self.get_config_value('use_mypy', True)
        self.flake8_args: List[str] = self.get_config_value('flake8_args', [])
        self.mypy_args: List[str] = self.get_config_value('mypy_args', [])
        self.flake8_timeout_secs: int = self.get_config_value('flake8_timeout', 30)
        self.mypy_timeout_secs: int = self.get_config_value('mypy_timeout', 30)

    @property
    def supported_extensions(self) -> List[str]:
        return ['.py', '.pyx', '.pyi']

    @property
    def language_name(self) -> str:
        return "Python"

    def is_available(self) -> bool:
        try:
            subprocess.run(['flake8', '--version'], capture_output=True, check=True, timeout=10)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _is_mypy_available(self) -> bool:
        try:
            subprocess.run(['mypy', '--version'], capture_output=True, check=True, timeout=10)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def lint_file(self, file_path: Union[str, Path]) -> LintResult:
        path = Path(file_path)
        result = LintResult(
            linter_name=self.name,
            files_checked=[str(path)]
        )

        try:
            raw_outputs: List[str] = []

            # Run flake8
            flake8_output = self._run_flake8(path)
            if flake8_output:
                raw_outputs.append(f"=== flake8 ===\n{flake8_output}")

            # Run mypy if enabled and available
            mypy_enabled = False
            if self.use_mypy and self._is_mypy_available():
                mypy_output = self._run_mypy(path)
                if mypy_output:
                    raw_outputs.append(f"=== mypy ===\n{mypy_output}")
                mypy_enabled = True

            # Combine all output and create issues if there's output
            if raw_outputs:
                combined_output = "\n\n".join(raw_outputs)
                # Use the lint_result property to maintain backward compatibility
                result.lint_result = combined_output
            
            result.metadata['mypy_enabled'] = mypy_enabled
            result.metadata['tools_used'] = ['flake8'] + (['mypy'] if mypy_enabled else [])
            result.success = True
        except Exception as exc:
            result.success = False
            error_msg = f"Error: {str(exc)}"
            result.error_message = error_msg
            result.lint_result = error_msg  # Also set for backward compatibility
            result.metadata['error'] = True

        return result

    def _run_flake8(self, file_path: Path) -> str:
        try:
            cmd = ['flake8']
            cmd.extend(self.flake8_args)
            cmd.append(str(file_path))

            completed = subprocess.run(cmd, capture_output=True, text=True, timeout=self.flake8_timeout_secs)
            return completed.stdout.strip()
        except subprocess.TimeoutExpired:
            raise Exception('flake8 execution timed out')
        except Exception as exc:
            raise Exception(f'Error running flake8: {str(exc)}')

    def _run_mypy(self, file_path: Path) -> str:
        try:
            cmd = ['mypy']
            cmd.extend(self.mypy_args)
            cmd.append(str(file_path))

            completed = subprocess.run(cmd, capture_output=True, text=True, timeout=self.mypy_timeout_secs)
            return completed.stdout.strip()
        except subprocess.TimeoutExpired:
            raise Exception('mypy execution timed out')
        except Exception as exc:
            raise Exception(f'Error running mypy: {str(exc)}')