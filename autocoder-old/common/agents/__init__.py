"""
AutoCoder Agents Module

This module provides functionality to read and parse agent definitions from .md files
in the .autocoderagents directory.
"""

from .agent_manager import AgentManager
from .agent_parser import AgentParser, Agent

__all__ = ['AgentManager', 'AgentParser', 'Agent']
