# -*- coding: utf-8 -*-
"""
Skills Manager 模块

负责读取项目级别和全局级别的 Skills README.md 文件。
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import os


@dataclass
class SkillInfo:
    """单个 Skill 的信息"""

    name: str
    description: str
    path: str  # 相对于 skills 目录的路径
    is_global: bool = False  # 是否是全局 skill


@dataclass
class SkillIndex:
    """Skills 索引，从 README.md 解析得到"""

    skills: list[SkillInfo] = field(default_factory=list)
    raw_content: str = ""  # 原始 README.md 内容
    source_path: str = ""  # README.md 的路径
    is_global: bool = False  # 是否是全局 skills

    def get_skill_names(self) -> list[str]:
        """获取所有 skill 名称"""
        return [skill.name for skill in self.skills]

    def get_skill_by_name(self, name: str) -> Optional[SkillInfo]:
        """根据名称获取 skill"""
        for skill in self.skills:
            if skill.name == name:
                return skill
        return None


class SkillManager:
    """
    Skills 管理器

    负责读取和管理项目级别及全局级别的 Skills。

    Skills 存储位置：
    - 项目级别: {project_root}/.autocoderskills/
    - 全局级别: ~/.auto-coder/.autocoderskills/
    """

    PROJECT_SKILLS_DIR = ".autocoderskills"
    GLOBAL_SKILLS_BASE = ".auto-coder"
    README_FILENAME = "README.md"

    def __init__(self, project_root: Optional[str] = None):
        """
        初始化 SkillManager

        Args:
            project_root: 项目根目录路径，如果不提供则使用当前工作目录
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.global_skills_dir = (
            Path.home() / self.GLOBAL_SKILLS_BASE / self.PROJECT_SKILLS_DIR
        )
        self.project_skills_dir = self.project_root / self.PROJECT_SKILLS_DIR

    def get_project_skills_dir(self) -> Path:
        """获取项目级别 skills 目录路径"""
        return self.project_skills_dir

    def get_global_skills_dir(self) -> Path:
        """获取全局 skills 目录路径"""
        return self.global_skills_dir

    def read_project_readme(self) -> Optional[SkillIndex]:
        """
        读取项目级别的 README.md

        Returns:
            SkillIndex 对象，如果文件不存在则返回 None
        """
        readme_path = self.project_skills_dir / self.README_FILENAME
        return self._read_readme(readme_path, is_global=False)

    def read_global_readme(self) -> Optional[SkillIndex]:
        """
        读取全局的 README.md

        Returns:
            SkillIndex 对象，如果文件不存在则返回 None
        """
        readme_path = self.global_skills_dir / self.README_FILENAME
        return self._read_readme(readme_path, is_global=True)

    def read_all_readmes(self) -> tuple[Optional[SkillIndex], Optional[SkillIndex]]:
        """
        读取项目级别和全局的 README.md

        Returns:
            (project_index, global_index) 元组
        """
        return self.read_project_readme(), self.read_global_readme()

    def get_merged_skills(self) -> list[SkillInfo]:
        """
        获取合并后的所有 skills 列表

        项目级别的 skill 优先级高于全局 skill（同名时项目级别覆盖全局）

        Returns:
            合并后的 SkillInfo 列表
        """
        project_index, global_index = self.read_all_readmes()

        skills_dict: dict[str, SkillInfo] = {}

        # 先添加全局 skills
        if global_index:
            for skill in global_index.skills:
                skills_dict[skill.name] = skill

        # 再添加项目 skills（会覆盖同名的全局 skill）
        if project_index:
            for skill in project_index.skills:
                skills_dict[skill.name] = skill

        return list(skills_dict.values())

    def _read_readme(self, readme_path: Path, is_global: bool) -> Optional[SkillIndex]:
        """
        读取并解析 README.md 文件

        Args:
            readme_path: README.md 文件路径
            is_global: 是否是全局 skills

        Returns:
            SkillIndex 对象，如果文件不存在则返回 None
        """
        if not readme_path.exists():
            return None

        try:
            content = readme_path.read_text(encoding="utf-8")
            skills = self._parse_readme_content(content, is_global)
            return SkillIndex(
                skills=skills,
                raw_content=content,
                source_path=str(readme_path),
                is_global=is_global,
            )
        except Exception:
            return None

    def _parse_readme_content(self, content: str, is_global: bool) -> list[SkillInfo]:
        """
        解析 README.md 内容，提取 skill 信息

        支持的格式：
        | Skill | Description |
        |-------|-------------|
        | [skill-name](./skill-name/) | Description text |

        Args:
            content: README.md 文件内容
            is_global: 是否是全局 skills

        Returns:
            SkillInfo 列表
        """
        import re

        skills = []

        # 匹配 markdown 表格中的 skill 链接
        # 格式: | [skill-name](./skill-name/) | description |
        pattern = r"\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|\s*([^|]+)\|"

        for match in re.finditer(pattern, content):
            name = match.group(1).strip()
            path = match.group(2).strip()
            description = match.group(3).strip()

            skills.append(
                SkillInfo(
                    name=name,
                    description=description,
                    path=path,
                    is_global=is_global,
                )
            )

        return skills

    def project_skills_exists(self) -> bool:
        """检查项目级别 skills 目录是否存在"""
        return self.project_skills_dir.exists()

    def global_skills_exists(self) -> bool:
        """检查全局 skills 目录是否存在"""
        return self.global_skills_dir.exists()

    def ensure_project_skills_dir(self) -> Path:
        """确保项目级别 skills 目录存在，如果不存在则创建"""
        self.project_skills_dir.mkdir(parents=True, exist_ok=True)
        return self.project_skills_dir

    def ensure_global_skills_dir(self) -> Path:
        """确保全局 skills 目录存在，如果不存在则创建"""
        self.global_skills_dir.mkdir(parents=True, exist_ok=True)
        return self.global_skills_dir

    def read_skill_content(
        self, skill_name: str, prefer_global: bool = False
    ) -> Optional[str]:
        """
        读取指定 skill 的 SKILL.md 内容

        Args:
            skill_name: skill 名称
            prefer_global: 是否优先读取全局 skill

        Returns:
            SKILL.md 的内容，如果不存在则返回 None
        """
        if prefer_global:
            search_order = [self.global_skills_dir, self.project_skills_dir]
        else:
            search_order = [self.project_skills_dir, self.global_skills_dir]

        for skills_dir in search_order:
            skill_path = skills_dir / skill_name / "SKILL.md"
            if skill_path.exists():
                try:
                    return skill_path.read_text(encoding="utf-8")
                except Exception:
                    continue

        return None

    def list_skill_directories(
        self, include_global: bool = True
    ) -> list[tuple[str, bool]]:
        """
        列出所有 skill 目录

        Args:
            include_global: 是否包含全局 skills

        Returns:
            (skill_name, is_global) 元组列表
        """
        skills = []

        # 列出项目级别 skills
        if self.project_skills_dir.exists():
            for item in self.project_skills_dir.iterdir():
                if item.is_dir() and (item / "SKILL.md").exists():
                    skills.append((item.name, False))

        # 列出全局 skills
        if include_global and self.global_skills_dir.exists():
            for item in self.global_skills_dir.iterdir():
                if item.is_dir() and (item / "SKILL.md").exists():
                    # 避免重复（项目级别优先）
                    if not any(s[0] == item.name for s in skills):
                        skills.append((item.name, True))

        return skills
