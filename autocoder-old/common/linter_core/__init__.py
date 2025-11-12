"""
Linter Core Module

A comprehensive multi-language linting framework that provides extensible
linting capabilities with support for TypeScript, Python, and easy addition
of new language linters.
"""

from .base_linter import BaseLinter
from .linter_factory import LinterFactory
from .linter_manager import LinterManager
from .models.lint_result import LintResult
from .formatters.base_formatter import BaseLintOutputFormatter
from .formatters.raw_formatter import RawLintOutputFormatter
from .config_loader import LinterConfigLoader, load_linter_config

__all__ = [
    'BaseLinter',
    'LinterFactory', 
    'LinterManager',
    'LintResult',
    'BaseLintOutputFormatter',
    'RawLintOutputFormatter',
    'LinterConfigLoader',
    'load_linter_config'
]

__version__ = "1.0.0" 