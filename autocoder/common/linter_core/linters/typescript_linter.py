"""
TypeScript linter implementation using tsc and optionally eslint.

Simplified to pass raw output to formatters without parsing.
"""

from __future__ import annotations

import subprocess
import time
from typing import List, Optional, Dict, Any, Union
from pathlib import Path

from ..base_linter import BaseLinter
from ..models.lint_result import LintResult


class TypeScriptLinter(BaseLinter):
    """TypeScript linter using tsc (and optionally eslint) with raw output."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.use_eslint: bool = self.get_config_value('use_eslint', True)
        self.tsc_args: List[str] = self.get_config_value('tsc_args', ['--noEmit', '--strict'])
        self.eslint_args: List[str] = self.get_config_value('eslint_args', [])
        self.tsconfig_path: Optional[str] = self.get_config_value('tsconfig_path', None)
        self.tsc_timeout_secs: int = self.get_config_value('tsc_timeout', 60)
        self.eslint_timeout_secs: int = self.get_config_value('eslint_timeout', 30)

    @property
    def supported_extensions(self) -> List[str]:
        return ['.ts', '.tsx', '.js', '.jsx']

    @property
    def language_name(self) -> str:
        return "TypeScript"

    def is_available(self) -> bool:
        try:
            subprocess.run(['tsc', '--version'], capture_output=True, check=True, timeout=10)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _is_eslint_available(self) -> bool:
        try:
            subprocess.run(['eslint', '--version'], capture_output=True, check=True, timeout=10)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def lint_file(self, file_path: Union[str, Path]) -> LintResult:
        start_time = time.time()
        path = Path(file_path)
        result = LintResult(
            linter_name=self.name,
            files_checked=[str(path)]
        )

        try:
            raw_outputs: List[str] = []

            # Run tsc
            tsc_output = self._run_tsc(path)
            if tsc_output:
                raw_outputs.append(f"=== tsc ===\n{tsc_output}")

            # Run eslint if enabled and available
            eslint_enabled = False
            if self.use_eslint and self._is_eslint_available():
                eslint_output = self._run_eslint(path)
                if eslint_output:
                    raw_outputs.append(f"=== eslint ===\n{eslint_output}")
                eslint_enabled = True

            # Combine all output
            if raw_outputs:
                combined_output = "\n\n".join(raw_outputs)
                result.lint_output = combined_output

            result.metadata['eslint_enabled'] = eslint_enabled
            result.metadata['tools_used'] = ['tsc'] + (['eslint'] if eslint_enabled else [])
            result.success = True
        except Exception as exc:
            result.success = False
            result.error_message = str(exc)
        finally:
            result.execution_time = time.time() - start_time

        return result

    def _run_tsc(self, file_path: Path) -> str:
        try:
            cmd = ['tsc']
            if self.tsconfig_path:
                cmd.extend(['--project', self.tsconfig_path])
            cmd.extend(self.tsc_args)
            cmd.append(str(file_path))

            completed = subprocess.run(cmd, capture_output=True, text=True, timeout=self.tsc_timeout_secs)
            # tsc outputs to stderr
            return completed.stderr.strip()
        except subprocess.TimeoutExpired:
            raise Exception('tsc execution timed out')
        except Exception as exc:
            raise Exception(f'Error running tsc: {str(exc)}')

    def _run_eslint(self, file_path: Path) -> str:
        try:
            cmd = ['eslint']
            cmd.extend(self.eslint_args)
            cmd.append(str(file_path))

            completed = subprocess.run(cmd, capture_output=True, text=True, timeout=self.eslint_timeout_secs)
            return completed.stdout.strip()
        except subprocess.TimeoutExpired:
            raise Exception('eslint execution timed out')
        except Exception as exc:
            raise Exception(f'Error running eslint: {str(exc)}')