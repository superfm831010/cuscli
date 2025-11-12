"""
Base classes for formatting linter results.

This layer allows each linter to define how its results are presented
without changing the linting logic. By default, a raw formatter returns
results unchanged (as dictionaries), and consumers may subclass to
produce pretty text, tables, or other formats.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from ..models.lint_result import LintResult


class BaseLintOutputFormatter(ABC):
    """Abstract formatter for lint results.

    Subclasses implement presentation logic for a single result and a
    collection of results. The return type is intentionally flexible to
    support dicts, strings, or other serializable structures.
    """

    @abstractmethod
    def format_result(self, result: LintResult) -> Any:
        """Format a single `LintResult` for presentation."""
        raise NotImplementedError

    def format_results(self, results: Dict[str, LintResult]) -> Dict[str, Any]:
        """Format multiple results.

        Default implementation maps input keys to formatted entries using
        `format_result`. Subclasses may override when a different aggregated
        structure is desired (e.g., a single text blob, table, or summary).
        """
        return {path: self.format_result(result) for path, result in results.items()}
