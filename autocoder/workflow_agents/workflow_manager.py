"""
Workflow Manager - 管理 workflow 文件的查找和加载

提供优先级搜索路径支持，类似 AgentManager。
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from loguru import logger

from autocoder.common.priority_directory_finder import (
    PriorityDirectoryFinder,
    FinderConfig,
    SearchStrategy,
    ValidationMode,
    create_file_filter,
)

# 常量定义
WORKFLOW_DIR_NAME = ".autocoderworkflow"
WORKFLOW_EXTENSIONS = [".yaml", ".yml"]


class WorkflowManager:
    """
    Workflow 文件管理器

    支持从多个目录按优先级查找 workflow YAML 文件：
    1. .autocoderworkflow (项目级，最高优先级)
    2. .auto-coder/.autocoderworkflow (项目级)
    3. ~/.auto-coder/.autocoderworkflow (全局级)
    """

    def __init__(self, project_root: str):
        """
        初始化 WorkflowManager

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root)
        self.workflow_directories: List[str] = []
        self._discover_directories()

    def _get_workflow_search_paths(self) -> List[Path]:
        """
        获取 workflow 搜索路径列表（按优先级排序）

        Returns:
            搜索路径列表
        """
        return [
            self.project_root / WORKFLOW_DIR_NAME,  # 项目级（最高）
            self.project_root / ".auto-coder" / WORKFLOW_DIR_NAME,  # 项目级
            Path.home() / ".auto-coder" / WORKFLOW_DIR_NAME,  # 全局级
        ]

    def _discover_directories(self) -> None:
        """使用优先级目录查找器发现 workflow 目录"""
        try:
            # 创建文件过滤器
            yaml_filter = create_file_filter(
                extensions=WORKFLOW_EXTENSIONS, recursive=False
            )

            # 创建查找器配置，使用 MERGE_ALL 策略
            config = FinderConfig(strategy=SearchStrategy.MERGE_ALL)

            # 按优先级添加目录
            config.add_directory(
                path=str(self.project_root / WORKFLOW_DIR_NAME),
                priority=1,
                validation_mode=ValidationMode.HAS_SPECIFIC_FILES,
                file_filter=yaml_filter,
                description="项目级 workflow 目录",
            )
            config.add_directory(
                path=str(self.project_root / ".auto-coder" / WORKFLOW_DIR_NAME),
                priority=2,
                validation_mode=ValidationMode.HAS_SPECIFIC_FILES,
                file_filter=yaml_filter,
                description="项目 .auto-coder workflow 目录",
            )
            config.add_directory(
                path=f"~/.auto-coder/{WORKFLOW_DIR_NAME}",
                priority=3,
                validation_mode=ValidationMode.HAS_SPECIFIC_FILES,
                file_filter=yaml_filter,
                description="全局 workflow 目录",
            )

            # 执行查找
            finder = PriorityDirectoryFinder(config)
            result = finder.find_directories()

            if result.success and result.selected_directories:
                logger.debug(
                    f"使用优先级查找器找到 {len(result.selected_directories)} 个 workflow 目录"
                )
                self.workflow_directories = result.selected_directories
            else:
                logger.debug("优先级查找器未找到包含 workflow 文件的目录")
                self.workflow_directories = []

        except Exception as e:
            logger.warning(f"使用优先级查找器发现 workflow 目录时出错: {e}")
            # 回退到传统方法
            self._discover_directories_fallback()

    def _discover_directories_fallback(self) -> None:
        """回退到传统的目录发现方法"""
        logger.debug("回退到传统的 workflow 目录查找方法")
        search_paths = self._get_workflow_search_paths()

        self.workflow_directories = []
        for path in search_paths:
            if path.exists() and path.is_dir():
                # 检查是否有 .yaml 或 .yml 文件
                yaml_files = list(path.glob("*.yaml")) + list(path.glob("*.yml"))
                if yaml_files:
                    self.workflow_directories.append(str(path))

    def find_workflow(self, workflow_name: str) -> Optional[str]:
        """
        按优先级查找 workflow 文件

        支持的文件名格式：
        - workflow_name.yaml
        - workflow_name.yml

        Args:
            workflow_name: workflow 名称（不含扩展名）

        Returns:
            找到的 workflow 文件绝对路径，如果未找到则返回 None
        """
        # 按优先级顺序查找
        for directory in self.workflow_directories:
            found_path = self._find_workflow_in_directory(
                Path(directory), workflow_name
            )
            if found_path:
                logger.info(f"找到 workflow: {found_path}")
                return found_path

        logger.warning(f"未找到 workflow: {workflow_name}")
        return None

    def _find_workflow_in_directory(
        self, dir_path: Path, workflow_name: str
    ) -> Optional[str]:
        """
        在指定目录中查找 workflow 文件

        Args:
            dir_path: 目录路径
            workflow_name: workflow 名称

        Returns:
            找到的文件路径，否则返回 None
        """
        for ext in WORKFLOW_EXTENSIONS:
            workflow_path = dir_path / f"{workflow_name}{ext}"
            if workflow_path.exists():
                return str(workflow_path)
        return None

    def list_workflows(self) -> Dict[str, str]:
        """
        列出所有可用的 workflow

        Returns:
            字典，key 为 workflow 名称（不含扩展名），value 为文件路径
        """
        workflows: Dict[str, str] = {}

        # 从低优先级到高优先级遍历，高优先级会覆盖低优先级
        for directory in reversed(self.workflow_directories):
            dir_path = Path(directory)

            # 查找所有 .yaml 和 .yml 文件
            for yaml_file in list(dir_path.glob("*.yaml")) + list(
                dir_path.glob("*.yml")
            ):
                workflow_name = yaml_file.stem
                workflows[workflow_name] = str(yaml_file)

        return workflows

    def get_workflow_directories(self) -> List[str]:
        """
        获取所有 workflow 目录路径

        Returns:
            workflow 目录路径列表，按优先级排序
        """
        return self.workflow_directories.copy()

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典表示

        Returns:
            包含搜索路径和可用 workflow 的字典
        """
        return {
            "project_root": str(self.project_root),
            "search_paths": [str(p) for p in self._get_workflow_search_paths()],
            "workflow_directories": self.workflow_directories,
            "workflows": self.list_workflows(),
        }
