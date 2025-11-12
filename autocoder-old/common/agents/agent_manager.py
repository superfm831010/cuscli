import shlex
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from loguru import logger
import byzerllm

from .agent_parser import AgentParser, Agent

# 导入优先级目录查找器
from autocoder.common.priority_directory_finder import (
    PriorityDirectoryFinder, FinderConfig, SearchStrategy, 
    ValidationMode, create_file_filter
)


class AgentManager:
    """Manager for loading and accessing agent definitions with multi-directory support."""
    
    def __init__(self, project_root: str):
        """
        Initialize AgentManager.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.agents: Dict[str, Agent] = {}
        self.agents_directories: List[str] = []
        self._load_agents()
    
    def _get_agents_search_paths(self) -> List[Path]:
        """
        Get the list of directories to search for agents, in priority order.
        
        Returns:
            List of Path objects in priority order:
            1. Project directory/.autocoderagents
            2. Project directory/.auto-coder/.autocoderagents  
            3. ~/.auto-coder/.autocoderagents
        """
        search_paths = []
        
        # 1. Project directory/.autocoderagents (highest priority)
        project_agents_dir = self.project_root / ".autocoderagents"
        search_paths.append(project_agents_dir)
        
        # 2. Project directory/.auto-coder/.autocoderagents
        project_autocoder_dir = self.project_root / ".auto-coder" / ".autocoderagents"
        search_paths.append(project_autocoder_dir)
        
        # 3. ~/.auto-coder/.autocoderagents (lowest priority)
        home_autocoder_dir = Path.home() / ".auto-coder" / ".autocoderagents"
        search_paths.append(home_autocoder_dir)
        
        return search_paths
    
    def _load_agents(self) -> None:
        """
        使用优先级目录查找器加载 agent 定义。
        采用 MERGE_ALL 策略，合并所有目录中的 agent 定义，支持优先级覆盖和repos功能。
        """
        try:
            # 创建文件过滤器，只查找.md文件
            md_filter = create_file_filter(extensions=[".md"], recursive=False)
            
            # 创建查找器配置，使用MERGE_ALL策略合并所有目录
            config = FinderConfig(strategy=SearchStrategy.MERGE_ALL)
            
            # 获取项目名用于repos目录
            project_name = self.project_root.name
            
            # 按优先级添加目录配置
            config.add_directory(
                path=str(self.project_root / ".autocoderagents"),
                priority=1,
                validation_mode=ValidationMode.HAS_SPECIFIC_FILES,
                file_filter=md_filter,
                description="项目级agent目录"
            )
            config.add_directory(
                path=str(self.project_root / ".auto-coder" / ".autocoderagents"),
                priority=2,
                validation_mode=ValidationMode.HAS_SPECIFIC_FILES,
                file_filter=md_filter,
                description="项目.auto-coder agent目录"
            )
            config.add_directory(
                path="~/.auto-coder/.autocoderagents",
                priority=3,
                validation_mode=ValidationMode.HAS_SPECIFIC_FILES,
                file_filter=md_filter,
                description="全局agent目录"
            )
            # 添加repos目录支持
            repos_dir = f"~/.auto-coder/.autocoderagents/repos/{project_name}"
            config.add_directory(
                path=repos_dir,
                priority=4,
                validation_mode=ValidationMode.HAS_SPECIFIC_FILES,
                file_filter=md_filter,
                description=f"项目特定repos agent目录: {project_name}"
            )
            
            # 执行查找
            finder = PriorityDirectoryFinder(config)
            result = finder.find_directories()
            
            if result.success and result.selected_directories:
                logger.info(f"使用优先级查找器找到 {len(result.selected_directories)} 个agent目录")
                self.agents_directories = result.selected_directories
                
                # 按优先级顺序加载agents，高优先级覆盖低优先级
                for agents_dir in self.agents_directories:
                    logger.info(f"加载agent目录: {agents_dir}")
                    self._load_agents_from_directory(Path(agents_dir))
            else:
                logger.info("优先级查找器未找到包含agent文件的目录")
                self.agents_directories = []
                
        except Exception as e:
            logger.error(f"使用优先级查找器加载agents时出错: {e}")
            # 回退到传统方法
            self._load_agents_fallback()
    
    def _load_agents_from_directory(self, agents_dir: Path) -> None:
        """Load agents from a specific directory with priority-based override logic."""
        if not agents_dir.exists():
            logger.debug(f"Agents directory not found: {agents_dir}")
            return
            
        if not agents_dir.is_dir():
            logger.warning(f"Expected directory but found file: {agents_dir}")
            return
        
        # Find all .md files in the agents directory
        md_files = list(agents_dir.glob("*.md"))
        
        if md_files:
            logger.debug(f"Found {len(md_files)} agent files in {agents_dir}")
        
        for md_file in md_files:
            try:
                agent = AgentParser.parse_agent_file(md_file)
                
                # Validate agent
                errors = AgentParser.validate_agent(agent)
                if errors:
                    logger.error(f"Validation errors for {md_file.name}: {'; '.join(errors)}")
                    continue
                
                # 检查是否已有同名agent，实现优先级覆盖逻辑
                if agent.name in self.agents:
                    old_agent_path = self.agents[agent.name].file_path
                    # 由于我们按优先级顺序加载，后加载的优先级更低，所以跳过
                    logger.debug(f"跳过agent '{agent.name}' from {md_file} (已存在优先级更高的版本: {old_agent_path})")
                    continue
                    
                self.agents[agent.name] = agent
                logger.debug(f"Loaded agent '{agent.name}' from {md_file}")
                
            except Exception as e:
                logger.error(f"Failed to parse agent file {md_file.name}: {e}")
    
    def _load_agents_fallback(self) -> None:
        """回退到传统的agent加载方法"""
        logger.info("回退到传统的agent目录查找方法")
        search_paths = self._get_agents_search_paths()
        
        # Load agents from all directories, with higher priority directories loaded last
        # This way higher priority agents will overwrite lower priority ones
        for agents_dir in reversed(search_paths):  # Start with lowest priority
            self._load_agents_from_directory(agents_dir)
    
    def get_agent(self, name: str) -> Optional[Agent]:
        """
        Get an agent by name.
        
        Args:
            name: Name of the agent
            
        Returns:
            Agent object if found, None otherwise
        """
        return self.agents.get(name)
    
    def list_agents(self) -> List[Agent]:
        """
        Get a list of all loaded agents.
        
        Returns:
            List of Agent objects
        """
        return list(self.agents.values())
    
    def get_agent_names(self) -> List[str]:
        """
        Get a list of all agent names.
        
        Returns:
            List of agent names
        """
        return list(self.agents.keys())
    
    @byzerllm.prompt()
    def render_sub_agents_section(self, current_model: Optional[str] = None) -> str:
        """
        {% if not agents_available %}
        {% else %}                        
        ## Available Named Sub Agents

        The following specialized agents are available for delegation:

        {% for agent in sorted_agents %}
        ### {{ agent.name }}
        **Description**: {{ agent.description }}
        {% if agent.tools %}
        **Available Tools**: {{ agent.tools | join(', ') }}
        {% endif %}
        
        {% endfor %}        
        ## How to Use

        Use the `run_named_subagents` tool to run multiple agent commands:

        ### Example: Parallel Execution
        
        <run_named_subagents>
        <subagents>
        mode: parallel
        subagents:
        {% for agent in example_agents %}
            - name: {{ agent.name }}
              task: {{ agent.example_task }}
        {% endfor %}
        </subagents>
        </run_named_subagents>
        

        ### Example: Serial Execution
        
        <run_named_subagents>
        <subagents>
        mode: serial
        subagents:
            - name: agent_name
              task: your task description here
        </subagents>
        </run_named_subagents>
                                
        {% endif %}
        """
        if not self.agents:
            return {
                "agents_available": False
            }
        
        # Sort agents by name for consistent output
        sorted_agents = sorted(self.agents.values(), key=lambda a: a.name)
        
        # Prepare agent data for template
        agents_data = []
        for agent in sorted_agents:
            model_to_use = agent.model or current_model
            if not model_to_use:
                raise ValueError(f"Agent {agent.name} has no model specified and no current model provided")

            # Use shlex.quote for safe shell escaping
            safe_task = shlex.quote("YOUR_TASK_HERE")
            safe_model = shlex.quote(model_to_use)
            safe_prompt = shlex.quote(agent.content)
            command = f'echo {safe_task} | auto-coder.run --model {safe_model} --system-prompt {safe_prompt}'
            
            agents_data.append({
                "name": agent.name,
                "description": agent.description,
                "tools": agent.tools if agent.tools else None,
                "command": command
            })
        
        # Prepare example agents data
        example_agents_data = []
        example_agents = sorted_agents[:2] if len(sorted_agents) >= 2 else sorted_agents
        for agent in example_agents:
            example_agents_data.append({
                "name": agent.name,
                "example_task": f"Task for {agent.name}"
            })
        
        return {
            "agents_available": True,
            "sorted_agents": agents_data,
            "example_agents": example_agents_data
        } # type: ignore
    
    def reload_agents(self) -> None:
        """Reload all agents from the directory."""
        self.agents.clear()
        self._load_agents()
    
    def get_all_agents_directories(self) -> List[str]:
        """
        获取所有agent目录路径
        
        Returns:
            List[str]: 所有agent目录路径列表，按优先级排序
        """
        return self.agents_directories.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the agent manager state to a dictionary.
        
        Returns:
            Dictionary representation of all agents
        """
        search_paths = self._get_agents_search_paths()
        return {
            'project_root': str(self.project_root),
            'search_paths': [str(path) for path in search_paths],
            'agents_directories': self.agents_directories,
            'agents': {name: agent.to_dict() for name, agent in self.agents.items()}
        }
