"""
Default raw formatter that returns lint results as dictionaries, unchanged.
"""

from __future__ import annotations

from typing import Any

from ..models.lint_result import LintResult
from .base_formatter import BaseLintOutputFormatter


class RawLintOutputFormatter(BaseLintOutputFormatter):
    """Return lint results as plain dictionaries with embedded summary."""

    def format_result(self, result: LintResult) -> Any:
        return result.to_dict()
