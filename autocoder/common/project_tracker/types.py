"""
Type definitions for Project Tracker module
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from enum import Enum

class ExplorationMode(str, Enum):
    """Exploration modes for project tracking"""
    FULL_SCAN = "full_scan"  # Complete project scan
    AC_MODULES_ONLY = "ac_modules_only"  # Only scan AC modules
    TARGETED_SCAN = "targeted_scan"  # Target specific areas
    QUICK_OVERVIEW = "quick_overview"  # Quick project overview

class ModuleInfo(BaseModel):
    """Information about an AC module"""
    path: str
    name: str
    description: str
    dependencies: List[str] = []
    key_features: List[str] = []
    verification_commands: List[str] = []
    last_analyzed: Optional[str] = None

class ExplorationResult(BaseModel):
    """Result of project exploration"""
    success: bool
    mode: ExplorationMode
    modules_found: List[ModuleInfo]
    project_structure: Dict[str, Any]
    key_insights: List[str]
    recommendations: List[str]
    analysis_summary: str
    exploration_time: float
    error_message: Optional[str] = None

class ProjectTrackerRequest(BaseModel):
    """Request for project tracking operation"""
    mode: ExplorationMode = ExplorationMode.FULL_SCAN
    target_paths: Optional[List[str]] = None
    include_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None
    max_depth: Optional[int] = None
    custom_prompt: Optional[str] = None

class ProjectTrackerResponse(BaseModel):
    """Response from project tracking operation"""
    success: bool
    exploration_result: Optional[ExplorationResult] = None
    conversation_id: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0 