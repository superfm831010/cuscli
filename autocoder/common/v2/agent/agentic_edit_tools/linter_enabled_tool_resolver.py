"""
Linter-enabled tool resolver that extends BaseToolResolver with linting capabilities.
"""

from typing import Optional, List
from autocoder.common.v2.agent.agentic_edit_types import BaseTool, ToolResult
from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import BaseToolResolver
from autocoder.common.v2.agent.agentic_edit_tools.linter_config_models import LinterConfig
from autocoder.common import AutoCoderArgs
from autocoder.common.linter_core.config_loader import load_linter_config
import typing
import os
import json
from loguru import logger

if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit
    from autocoder.common.linter_core.linter_manager import LinterManager
    from autocoder.common.v2.agent.agentic_edit_tools.lint_report import LintReport


class LinterEnabledToolResolver(BaseToolResolver):
    """
    Tool resolver with integrated linter support.
    
    This class extends BaseToolResolver to provide linting capabilities
    for tools that modify files.
    """
    
    def __init__(self, agent: Optional['AgenticEdit'], tool: BaseTool, args: AutoCoderArgs):
        """
        Initializes the resolver with linter support.

        Args:
            agent: The AutoCoder agent instance.
            tool: The Pydantic model instance representing the tool call.
            args: Additional arguments needed for execution (e.g., source_dir).
        """
        super().__init__(agent, tool, args)
        
        # Initialize linter
        self.linter_manager: Optional['LinterManager'] = None
        self.linter_config: Optional[LinterConfig] = None
        self._init_linter()

    def _init_linter(self):
        """初始化 Linter 管理器"""
        try:
            # Load and validate linter configuration using the centralized loader
            source_dir = getattr(self.args, 'source_dir', None)
            linter_config_path = getattr(self.args, 'linter_config_path', None)
            
            raw_config = load_linter_config(
                config_path=linter_config_path,
                source_dir=source_dir
            )
            
            self.linter_config = LinterConfig.from_dict(raw_config)
            
            # Check if linter is enabled
            if not self.linter_config.enabled:
                logger.debug("Linter is disabled in configuration")
                return
            
            # Import and initialize LinterManager
            from autocoder.common.linter_core.linter_manager import LinterManager
            
            # Convert to manager-compatible config
            manager_config = self.linter_config.to_manager_config()
            
            self.linter_manager = LinterManager(manager_config, source_dir=source_dir)
            logger.info("Linter manager initialized successfully with validated configuration")
            
        except ImportError as e:
            logger.warning(f"Linter module not available: {e}")
        except ValueError as e:
            logger.error(f"Invalid linter configuration: {e}")
            # Use default disabled config on validation error
            self.linter_config = LinterConfig(enabled=False)
        except Exception as e:
            logger.error(f"Failed to initialize linter: {e}")
            # Use default disabled config on error
            self.linter_config = LinterConfig(enabled=False)
    

    def should_lint(self, file_path: str) -> bool:
        """判断文件是否需要 lint 检查"""
        if not self.linter_manager or not self.linter_config:
            return False
        
        # Use the Pydantic model's method
        should_lint = self.linter_config.should_lint_file(file_path)
        
        if not should_lint:
            logger.debug(f"File {file_path} excluded from linting")
        
        return should_lint
    
    def lint_files(self, file_paths: List[str]) -> Optional['LintReport']:
        """对文件运行 linter 检查"""
        if not self.linter_manager:
            return None
        
        try:
            from autocoder.common.v2.agent.agentic_edit_tools.lint_report import LintReport
            
            # Convert relative paths to absolute paths
            abs_file_paths = []
            source_dir = self.args.source_dir or "."
            for file_path in file_paths:
                if not os.path.isabs(file_path):
                    abs_path = os.path.abspath(os.path.join(source_dir, file_path))
                else:
                    abs_path = file_path
                abs_file_paths.append(abs_path)
            
            # Run linter
            results = self.linter_manager.lint_files(abs_file_paths, parallel=False)
            
            # Create report
            report = LintReport.from_linter_results(results, self.linter_manager)
            
            return report
            
        except Exception as e:
            logger.error(f"Error running linter: {e}")
            return None
    
    def handle_lint_results(self, original_result: ToolResult, lint_report: Optional['LintReport']) -> ToolResult:
        """处理 lint 结果并更新 ToolResult"""
        if not lint_report or not self.linter_config:
            return original_result
        
        # Get configuration from Pydantic model
        mode = self.linter_config.mode
        report_format = self.linter_config.report.format
        include_in_result = self.linter_config.report.include_in_result
        
        # Generate report text based on format
        if report_format == 'detailed':
            report_text = lint_report.to_markdown()
        elif report_format == 'json':
            report_text = json.dumps(lint_report.to_json(), indent=2)
        else:  # simple
            report_text = lint_report.to_simple_text()
        
        # Handle based on mode
        if mode == 'blocking' and lint_report.has_issues():
            # Blocking mode - fail the operation
            return ToolResult(
                success=False,
                message=f"Operation blocked due to lint issues:\n{report_text}",
                content={'lint_report': lint_report.to_json()} if include_in_result else None
            )
        elif mode == 'silent':
            # Silent mode - don't modify the result
            if include_in_result and original_result.content:
                if isinstance(original_result.content, dict):
                    original_result.content['lint_report'] = lint_report.to_json()
            return original_result
        else:  # warning mode (default)
            # Warning mode - append lint results to message
            if lint_report.has_issues():
                new_message = f"{original_result.message}\n\n{report_text}"
            else:
                new_message = f"{original_result.message}\n✅ Lint check passed - No issues found"
            
            # Create new result with updated message and content
            new_content = original_result.content or {}
            if include_in_result:
                if isinstance(new_content, dict):
                    new_content['lint_report'] = lint_report.to_json()
                else:
                    new_content = {'lint_report': lint_report.to_json()}
            
            return ToolResult(
                success=original_result.success,
                message=new_message,
                content=new_content if new_content else None
            )
    
    def resolve(self) -> ToolResult:
        """
        Must be implemented by subclasses.
        
        Returns:
            A ToolResult object indicating success or failure and a message.
        """
        raise NotImplementedError("Subclasses must implement the resolve method")