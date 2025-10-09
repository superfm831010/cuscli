"""
Project Tracker API

Provides a high-level API interface for project tracking and exploration functionality.
"""

import os
from typing import Optional, Dict, Any
from loguru import logger

from autocoder.common import AutoCoderArgs
from autocoder.utils.llms import get_single_llm

from .tracker import ProjectTracker
from .types import (
    ProjectTrackerRequest,
    ProjectTrackerResponse,
    ExplorationMode
)

class ProjectTrackerAPI:
    """
    High-level API for project tracking and exploration.
    
    This class provides a simplified interface for common project tracking operations,
    making it easy to integrate project exploration into various workflows.
    """
    
    def __init__(self, source_dir: Optional[str] = None, args: Optional[AutoCoderArgs] = None):
        """
        Initialize the Project Tracker API.
        
        Args:
            source_dir: Source directory path (optional if args provided)
            args: AutoCoder arguments (optional, will create minimal config if not provided)
        """
        if args is None:
            raise ValueError("args is required")
        else:
            self.args = args
            
        self.tracker = None
        self._llm = None
    
    def _get_tracker(self) -> ProjectTracker:
        """Get or create a ProjectTracker instance."""
        if self.tracker is None:
            if self._llm is None:
                self._llm = get_single_llm(
                    self.args.code_model or self.args.model,
                    product_mode=self.args.product_mode
                )
            self.tracker = ProjectTracker(self.args, self._llm)
        return self.tracker
    
    def quick_scan(self, custom_prompt: Optional[str] = None) -> ProjectTrackerResponse:
        """
        Perform a quick project scan for rapid overview.
        
        Args:
            custom_prompt: Optional custom instructions for the scan
            
        Returns:
            ProjectTrackerResponse with quick scan results
        """
        request = ProjectTrackerRequest(
            mode=ExplorationMode.QUICK_OVERVIEW,
            custom_prompt=custom_prompt
        )
        
        tracker = self._get_tracker()
        return tracker.explore_project(request)
    
    def full_exploration(self, custom_prompt: Optional[str] = None) -> ProjectTrackerResponse:
        """
        Perform comprehensive project exploration.
        
        Args:
            custom_prompt: Optional custom instructions for exploration
            
        Returns:
            ProjectTrackerResponse with full exploration results
        """
        request = ProjectTrackerRequest(
            mode=ExplorationMode.FULL_SCAN,
            custom_prompt=custom_prompt
        )
        
        tracker = self._get_tracker()
        return tracker.explore_project(request)
    
    def analyze_ac_modules(self, custom_prompt: Optional[str] = None) -> ProjectTrackerResponse:
        """
        Focus specifically on AC module analysis.
        
        Args:
            custom_prompt: Optional custom instructions for AC module analysis
            
        Returns:
            ProjectTrackerResponse with AC module analysis results
        """
        request = ProjectTrackerRequest(
            mode=ExplorationMode.AC_MODULES_ONLY,
            custom_prompt=custom_prompt
        )
        
        tracker = self._get_tracker()
        return tracker.explore_project(request)
    
    def targeted_exploration(
        self, 
        target_paths: list[str], 
        custom_prompt: Optional[str] = None
    ) -> ProjectTrackerResponse:
        """
        Perform targeted exploration of specific paths.
        
        Args:
            target_paths: List of paths to focus exploration on
            custom_prompt: Optional custom instructions for targeted exploration
            
        Returns:
            ProjectTrackerResponse with targeted exploration results
        """
        request = ProjectTrackerRequest(
            mode=ExplorationMode.TARGETED_SCAN,
            target_paths=target_paths,
            custom_prompt=custom_prompt
        )
        
        tracker = self._get_tracker()
        return tracker.explore_project(request)
    
    def get_project_overview(self) -> Dict[str, Any]:
        """
        Get basic project information without AI analysis.
        
        Returns:
            Dictionary with basic project overview
        """
        tracker = self._get_tracker()
        return tracker.get_project_overview()
    
    def explore_for_requirements(self, user_requirements: str) -> ProjectTrackerResponse:
        """
        Explore project specifically to understand how to implement user requirements.
        
        This method creates a custom prompt that focuses on finding relevant modules,
        patterns, and approaches that would be useful for implementing the given requirements.
        
        Args:
            user_requirements: Description of what the user wants to implement
            
        Returns:
            ProjectTrackerResponse with exploration focused on requirements
        """
        custom_prompt = f"""
## User Requirements Analysis

The user wants to implement the following:
{user_requirements}

Please focus your exploration on:

1. **Relevant AC Modules**: Find AC modules that might be related to these requirements
2. **Implementation Patterns**: Identify common patterns and approaches used in the project
3. **Similar Features**: Look for existing implementations that are similar to the requirements
4. **Dependencies**: Understand what dependencies and tools are available
5. **Best Practices**: Identify best practices and conventions used in the project
6. **Integration Points**: Find where new functionality should be integrated

## Specific Analysis Goals:

- Which AC modules provide functionality similar to the requirements?
- What patterns and conventions should be followed?
- Where would be the best place to implement these requirements?
- What existing code can be leveraged or extended?
- What tools and utilities are available to help with implementation?

Provide specific, actionable insights that will help the user implement their requirements 
efficiently and in a way that fits well with the existing project structure.
"""
        
        return self.full_exploration(custom_prompt=custom_prompt)

# Convenience functions for direct usage
def quick_project_scan(source_dir: Optional[str] = None) -> ProjectTrackerResponse:
    """
    Convenience function for quick project scanning.
    
    Args:
        source_dir: Source directory path (defaults to current directory)
        
    Returns:
        ProjectTrackerResponse with quick scan results
    """
    api = ProjectTrackerAPI(source_dir=source_dir)
    return api.quick_scan()

def explore_project_for_requirements(
    user_requirements: str, 
    source_dir: Optional[str] = None
) -> ProjectTrackerResponse:
    """
    Convenience function for requirement-focused project exploration.
    
    Args:
        user_requirements: Description of what user wants to implement
        source_dir: Source directory path (defaults to current directory)
        
    Returns:
        ProjectTrackerResponse with requirement-focused exploration
    """
    api = ProjectTrackerAPI(source_dir=source_dir)
    return api.explore_for_requirements(user_requirements)

def get_basic_project_info(source_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function for basic project information.
    
    Args:
        source_dir: Source directory path (defaults to current directory)
        
    Returns:
        Dictionary with basic project information
    """
    api = ProjectTrackerAPI(source_dir=source_dir)
    return api.get_project_overview() 