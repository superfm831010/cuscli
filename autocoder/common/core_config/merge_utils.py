"""
Configuration merge utilities for global and project scope merging.

This module provides utilities to deep merge configuration dictionaries,
with project-level configuration taking precedence over global configuration.
"""

from typing import Any, Dict
from pathlib import Path
import os


def get_global_config_dir() -> Path:
    """
    Get the global configuration directory path.

    Returns:
        Path: ~/.auto-coder/plugins/chat-auto-coder
    """
    home = Path.home()
    return home / ".auto-coder" / "plugins" / "chat-auto-coder"


def deep_merge_config(
    global_conf: Dict[str, Any], project_conf: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Deep merge two configuration dictionaries with project config taking precedence.

    Merge strategy:
    - Scalars (str/int/bool/float/None): Project value overrides global value
    - Dicts: Recursively merge, with project keys overriding global keys
    - Lists: Project list completely replaces global list (no merging)
    - Type conflicts: Project value takes precedence

    Args:
        global_conf: Global configuration dictionary
        project_conf: Project configuration dictionary

    Returns:
        Merged configuration with project values taking precedence

    Examples:
        >>> global_c = {"a": 1, "b": {"x": 10, "y": 20}, "c": [1, 2]}
        >>> project_c = {"b": {"x": 100}, "d": 4}
        >>> deep_merge_config(global_c, project_c)
        {'a': 1, 'b': {'x': 100, 'y': 20}, 'c': [1, 2], 'd': 4}
    """
    if not isinstance(global_conf, dict):
        global_conf = {}
    if not isinstance(project_conf, dict):
        project_conf = {}

    # Start with a copy of global config
    result = global_conf.copy()

    # Merge project config into result
    for key, project_value in project_conf.items():
        if key not in result:
            # Key only exists in project, add it directly
            result[key] = project_value
        else:
            global_value = result[key]

            # If both are dicts, recursively merge
            if isinstance(global_value, dict) and isinstance(project_value, dict):
                result[key] = deep_merge_config(global_value, project_value)
            else:
                # For all other types (scalars, lists, type conflicts), project wins
                result[key] = project_value

    return result












