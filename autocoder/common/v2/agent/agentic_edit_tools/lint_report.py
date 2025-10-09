"""
Lint report data structure for AgenticEdit tools integration.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from autocoder.common.linter_core.models.lint_result import LintResult
from autocoder.common.linter_core.linter_manager import LinterManager


@dataclass
class LintReport:
    """Lint 检查报告 - 基于 linter_core 的简化实现"""
    results: Dict[str, LintResult]  # 原始检查结果
    summary: Dict[str, Any]         # LinterManager.get_summary_report() 的结果
    
    @classmethod
    def from_linter_results(cls, results: Dict[str, LintResult], 
                          manager: LinterManager) -> 'LintReport':
        """从 LinterManager 的结果创建报告"""
        summary = manager.get_summary_report(results)
        return cls(results=results, summary=summary)
    
    def to_markdown(self) -> str:
        """生成 Markdown 格式报告"""
        lines = ["## Lint Report\n"]
        
        # 汇总信息
        lines.append("### Summary")
        lines.append(f"- Total files: {self.summary['total_files']}")
        lines.append(f"- Files with issues: {self.summary['files_with_issues']}")
        lines.append(f"- Failed files: {self.summary['failed_files']}")
        lines.append(f"- Execution time: {self.summary['total_execution_time']:.2f}s\n")
        
        # 详细结果
        if self.has_issues():
            lines.append("### Issues Found")
            for file_path, result in self.results.items():
                if result.has_issues:
                    lines.append(f"#### {file_path}")
                    lines.append("```")
                    lines.append(result.lint_output)
                    lines.append("```\n")
        
        return "\n".join(lines)
    
    def to_simple_text(self) -> str:
        """生成简单文本格式报告"""
        if not self.has_issues():
            return f"✅ Lint check passed - No issues found in {self.summary['total_files']} file(s)"
        
        lines = [f"❌ Lint issues detected in {self.summary['files_with_issues']} of {self.summary['total_files']} file(s):"]
        for file_path, result in self.results.items():
            if result.has_issues:
                lines.append(f"\n{file_path}:")
                lines.append(result.lint_output)
        
        return "\n".join(lines)
    
    def to_json(self) -> dict:
        """生成 JSON 格式报告"""
        return {
            'summary': self.summary,
            'results': {
                path: result.to_dict() 
                for path, result in self.results.items()
            }
        }
    
    def has_issues(self) -> bool:
        """检查是否有任何问题"""
        return self.summary.get('files_with_issues', 0) > 0
    
    def get_files_with_issues(self) -> List[str]:
        """获取有问题的文件列表"""
        return [
            path for path, result in self.results.items() 
            if result.has_issues
        ]