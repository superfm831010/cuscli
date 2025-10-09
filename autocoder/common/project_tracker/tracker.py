"""
Core Project Tracker Implementation

Uses AgenticEdit to perform intelligent project exploration and analysis.
"""

import os
import time
import json
from typing import List, Dict, Any, Optional, Generator
from loguru import logger
from rich.console import Console

from autocoder.common import AutoCoderArgs
from autocoder.common.v2.agent.agentic_edit import AgenticEdit
from autocoder.common.v2.agent.agentic_edit_types import (
    AgenticEditRequest, 
    AgenticEditConversationConfig,
    ConversationAction
)

from autocoder.utils.llms import get_single_llm

from .types import (
    ProjectTrackerRequest, 
    ProjectTrackerResponse, 
    ExplorationResult,
    ExplorationMode,
    ModuleInfo
)

class ProjectTracker:
    """
    Core project tracker that uses AgenticEdit to analyze and explore projects.
    
    This class provides intelligent project exploration capabilities by leveraging
    the AgenticEdit system to understand AC modules, project structure, and provide
    insights for faster development workflows.
    """
    
    def __init__(self, args: AutoCoderArgs, llm=None):
        """
        Initialize the project tracker.
        
        Args:
            args: AutoCoder arguments configuration
            llm: Language model instance (optional, will create if not provided)
        """
        self.args = args
        if llm is None:
            self.llm = get_single_llm(
                args.code_model or args.model, 
                product_mode=args.product_mode
            )
        else:
            self.llm = llm
        
        # Initialize AgenticEdit for exploration
        self.agentic_edit = None
        
    def _create_exploration_prompt(self, request: ProjectTrackerRequest) -> str:
        """
        Create a comprehensive prompt for project exploration based on the request mode.
        
        Args:
            request: Project tracker request with exploration parameters
            
        Returns:
            Formatted prompt string for AgenticEdit
        """
        base_prompt = """
You are an expert project analyst tasked with exploring and understanding this project structure. 
Your goal is to provide comprehensive insights that will help developers quickly understand the 
project and make informed decisions about future modifications.

## Primary Objectives:

1. **AC Module Discovery**: Find and analyze all AC modules (directories with .ac.mod.md files)
2. **Project Structure Analysis**: Understand the overall project organization
3. **Dependency Mapping**: Identify relationships between modules and components
4. **Key Insights**: Provide actionable insights for development efficiency
5. **Recommendations**: Suggest areas for improvement or optimization

## Analysis Instructions:

### Step 1: AC Module Discovery
Use the `ac_mod_list` tool to find all AC modules in the project. For each AC module found:
- Use `ac_mod_read` to read the module documentation
- Extract key information: purpose, features, dependencies, APIs
- Note verification commands and testing approaches

### Step 2: Project Structure Exploration
Use `list_files` and `read_file` tools to explore:
- Main project directories and their purposes
- Configuration files and their contents
- Key implementation files
- Documentation structure

### Step 3: Intelligent Analysis
Analyze the discovered information to:
- Identify patterns in module organization
- Map dependencies between AC modules
- Understand the project's architectural approach
- Identify potential areas for improvement

### Step 4: Generate Insights
Provide specific insights about:
- How AC modules work together
- Common patterns and conventions used
- Areas where new features could be added
- Potential optimization opportunities

## Output Requirements:

Provide a comprehensive analysis that includes:
1. **AC Modules Summary**: List of all AC modules with brief descriptions
2. **Project Architecture**: High-level understanding of project structure
3. **Dependency Graph**: Relationships between modules
4. **Key Features**: Important capabilities and patterns
5. **Development Recommendations**: Suggestions for efficient development
6. **Quick Reference**: Essential information for rapid development

## IMPORTANT: Generate Project Documentation File

After completing your analysis, you MUST use the `write_to_file` tool to create or update the file `.auto-coder/projects/AUTO-CODER.md` with a comprehensive project documentation that includes:

### File Structure for .auto-coder/projects/AUTO-CODER.md:

```markdown
# AutoCoder Project Documentation

*Generated on: [CURRENT_DATE]*

## Project Overview

[Brief description of the AutoCoder project and its purpose]

## Architecture Summary

[High-level architecture description based on your analysis]

## AC Modules Overview

### Core Modules
[List and describe the most important AC modules]

### Support Modules  
[List and describe supporting/utility AC modules]

### Experimental/Development Modules
[List any experimental or development-focused modules]

## Key Components and Patterns

[Describe the main architectural patterns and design principles used]

## Development Workflow

[Describe how development typically works in this project]

## Quick Start for New Developers

[Essential information for developers new to the project]

## Module Dependencies

[Key dependency relationships between AC modules]

## Recommended Development Practices

[Best practices derived from analyzing the codebase]

## Areas for Improvement

[Suggestions for project enhancement]

## Additional Resources

[Links to important documentation, tools, or references]
```

Use the `write_to_file` tool with path `.auto-coder/projects/AUTO-CODER.md` and populate it with comprehensive, well-structured content based on your project analysis.

"""

        if request.mode == ExplorationMode.AC_MODULES_ONLY:
            mode_specific = """
## Focus Mode: AC MODULES ONLY

Focus specifically on AC modules:
- Prioritize AC module discovery and analysis
- Deep dive into module documentation and relationships
- Understand the AC module ecosystem
- Provide detailed insights about module patterns and best practices
"""
        elif request.mode == ExplorationMode.QUICK_OVERVIEW:
            mode_specific = """
## Focus Mode: QUICK OVERVIEW

Provide a rapid but comprehensive overview:
- Quick scan of AC modules (focus on top-level information)
- High-level project structure understanding
- Key architectural insights
- Essential information for getting started quickly
"""
        elif request.mode == ExplorationMode.TARGETED_SCAN:
            target_info = f"Target paths: {request.target_paths}" if request.target_paths else ""
            mode_specific = f"""
## Focus Mode: TARGETED SCAN

Focus on specific areas of the project:
{target_info}
- Concentrate analysis on specified paths or patterns
- Provide detailed insights for targeted areas
- Connect targeted areas to broader project context
"""
        else:  # FULL_SCAN
            mode_specific = """
## Focus Mode: FULL SCAN

Perform comprehensive project analysis:
- Complete AC module discovery and analysis
- Thorough project structure exploration
- Detailed dependency mapping
- Comprehensive insights and recommendations
"""

        custom_instructions = ""
        if request.custom_prompt:
            custom_instructions = f"""
## Additional Instructions:
{request.custom_prompt}
"""

        return f"{base_prompt}\n{mode_specific}\n{custom_instructions}\n"

    def explore_project(self, request: ProjectTrackerRequest) -> ProjectTrackerResponse:
        """
        Perform project exploration using AgenticEdit.
        
        Args:
            request: Project tracking request with exploration parameters
            
        Returns:
            ProjectTrackerResponse with exploration results
        """
        start_time = time.time()
        
        try:
            # Create conversation configuration
            conversation_config = AgenticEditConversationConfig(
                action=ConversationAction.NEW,
                query=f"Project exploration - {request.mode.value}"
            )
            
            # Check LLM is available
            if self.llm is None:
                raise ValueError("LLM is not available for project exploration")
            
            # Initialize AgenticEdit
            self.agentic_edit = AgenticEdit(
                llm=self.llm,
                args=self.args,
                conversation_config=conversation_config
            )
            
            # Create exploration prompt
            exploration_prompt = self._create_exploration_prompt(request)
            
            # Create AgenticEdit request
            agentic_request = AgenticEditRequest(user_input=exploration_prompt)
            
            # Execute exploration
            console = Console()
            console.print(f"[bold cyan]Starting project exploration with mode: {request.mode}[/]")
            
            # Process events with simple printing and collect them
            exploration_events = []
            event_stream = self.agentic_edit.analyze(agentic_request)
            
            for event in event_stream:
                # Collect all events for later processing
                exploration_events.append(event)
                
                # Simple printing based on event type (simplified version of terminal_runner)
                if hasattr(event, '__class__'):
                    event_name = event.__class__.__name__
                    
                    if 'ConversationId' in event_name:
                        conversation_id = getattr(event, 'conversation_id', 'unknown')
                        console.print(f"[dim]Conversation ID: {conversation_id}[/dim]")
                    elif 'TokenUsage' in event_name:
                        console.print("[dim]💰 Token usage recorded[/dim]")
                    elif 'LLMThinking' in event_name:
                        # Show thinking indicator
                        console.print("[grey50]🤔 Thinking...[/grey50]", end="")
                    elif 'LLMOutput' in event_name:
                        # Show brief output indicator
                        console.print("[dim]✏️  Generating response...[/dim]")
                    elif 'ToolCall' in event_name:
                        tool = getattr(event, 'tool', {})
                        if hasattr(tool, '__class__'):
                            tool_name = tool.__class__.__name__
                            console.print(f"[blue]🔧 Tool: {tool_name}[/blue]")
                        else:
                            console.print("[blue]🔧 Tool called[/blue]")
                    elif 'ToolResult' in event_name:
                        result = getattr(event, 'result', None)
                        if result and hasattr(result, 'success'):
                            if result.success:
                                tool_name = getattr(event, 'tool_name', 'Unknown')
                                console.print(f"[green]✅ {tool_name}: Success[/green]")
                            else:
                                tool_name = getattr(event, 'tool_name', 'Unknown')
                                console.print(f"[red]❌ {tool_name}: Failed[/red]")
                        else:
                            console.print("[dim]📋 Tool result received[/dim]")
                    elif 'Completion' in event_name:
                        console.print("[bold green]🏁 Task completion[/bold green]")
                    elif 'Error' in event_name:
                        error_msg = getattr(event, 'message', 'Unknown error')
                        console.print(f"[bold red]🔥 Error: {error_msg}[/bold red]")
                    else:
                        console.print(f"[dim]📝 Event: {event_name}[/dim]")
            
            console.print("[bold cyan]Project exploration completed[/]")
            
            # Process the results
            exploration_result = self._process_exploration_results(
                exploration_events, request.mode, start_time
            )
            
            execution_time = time.time() - start_time
            
            # Get conversation ID for future reference
            conversation_id = self.agentic_edit.conversation_manager.get_current_conversation_id()
            
            return ProjectTrackerResponse(
                success=True,
                exploration_result=exploration_result,
                conversation_id=conversation_id,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Project exploration failed: {str(e)}")
            
            return ProjectTrackerResponse(
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )

    def _process_exploration_results(
        self, 
        events: List[Any], 
        mode: ExplorationMode,
        start_time: float
    ) -> ExplorationResult:
        """
        Process exploration events and extract meaningful results.
        
        Args:
            events: List of events from AgenticEdit exploration
            mode: Exploration mode used
            start_time: Start time of exploration
            
        Returns:
            ExplorationResult with processed information
        """
        modules_found = []
        project_structure = {}
        key_insights = []
        recommendations = []
        analysis_summary = ""
        
        # Process events to extract information
        for event in events:
            try:
                if hasattr(event, 'type') and hasattr(event, 'content'):
                    # Process different event types
                    if 'completion' in str(event.type).lower():
                        # Extract final analysis from completion events
                        content = getattr(event, 'content', '')
                        if content:
                            analysis_summary += content + "\n"
                    
                    elif 'tool_result' in str(event.type).lower():
                        # Process tool results for structured data
                        self._extract_tool_results(event, modules_found, project_structure)
                        
            except Exception as e:
                logger.warning(f"Failed to process event: {e}")
                continue
        
        # Extract insights from analysis summary
        if analysis_summary:
            key_insights, recommendations = self._extract_insights_from_summary(analysis_summary)
        
        exploration_time = time.time() - start_time
        
        return ExplorationResult(
            success=True,
            mode=mode,
            modules_found=modules_found,
            project_structure=project_structure,
            key_insights=key_insights,
            recommendations=recommendations,
            analysis_summary=analysis_summary,
            exploration_time=exploration_time
        )
    
    def _extract_tool_results(self, event: Any, modules_found: List[ModuleInfo], project_structure: Dict[str, Any]):
        """Extract information from tool result events."""
        try:
            # This is a simplified extraction - in a real implementation,
            # you would parse the specific tool results based on their types
            content = getattr(event, 'content', '')
            
            # Look for AC module information
            if '.ac.mod.md' in content:
                # Extract module info (simplified)
                # In practice, you'd parse the actual tool results
                pass
                
        except Exception as e:
            logger.debug(f"Failed to extract tool results: {e}")
    
    def _extract_insights_from_summary(self, summary: str) -> tuple[List[str], List[str]]:
        """Extract insights and recommendations from analysis summary."""
        insights = []
        recommendations = []
        
        # Simple extraction based on common patterns
        lines = summary.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for section headers
            if 'insight' in line.lower() or 'key point' in line.lower():
                current_section = 'insights'
            elif 'recommend' in line.lower() or 'suggest' in line.lower():
                current_section = 'recommendations'
            elif line.startswith('- ') or line.startswith('* '):
                # List item
                item = line[2:].strip()
                if current_section == 'insights' and item:
                    insights.append(item)
                elif current_section == 'recommendations' and item:
                    recommendations.append(item)
        
        return insights, recommendations

    def get_project_overview(self) -> Dict[str, Any]:
        """
        Get a quick project overview without full exploration.
        
        Returns:
            Dictionary with basic project information
        """
        try:
            # Quick scan for AC modules
            ac_modules = []
            source_dir = self.args.source_dir
            if source_dir is None:
                return {"error": "source_dir is not configured"}
                
            for root, dirs, files in os.walk(source_dir):
                if '.ac.mod.md' in files:
                    relative_path = os.path.relpath(root, source_dir)
                    ac_modules.append(relative_path)
            
            return {
                "source_dir": self.args.source_dir,
                "ac_modules_found": len(ac_modules),
                "ac_module_paths": ac_modules,
                "project_type": getattr(self.args, 'project_type', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Failed to get project overview: {e}")
            return {"error": str(e)} 