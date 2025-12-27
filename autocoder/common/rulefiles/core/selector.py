# -*- coding: utf-8 -*-
"""
RuleSelector

基于 LLM 的智能规则选择器，支持规则摘要生成和索引创建。
"""

import os
import platform
import shutil
import subprocess
import tempfile
import concurrent.futures
from typing import Dict, List, Optional, Union
from loguru import logger

# 导入第三方依赖
import byzerllm
from autocoder.common import AutoCoderArgs

# 导入数据模型
from ..models.rule_file import RuleFile
from ..models.rule_relevance import RuleRelevance
from ..models.summary import AlwaysApplyRuleSummary
from ..models.index import ConditionalRulesIndex
from ..models.init_rule import InitRule


class RuleSelector:
    """
    根据LLM的判断和规则元数据选择适用的规则。
    """

    def __init__(
        self,
        llm: Optional[Union[byzerllm.ByzerLLM, byzerllm.SimpleByzerLLM]],
        args: Optional[AutoCoderArgs] = None,
    ):
        """
        初始化RuleSelector。

        Args:
            llm: ByzerLLM 实例，用于判断规则是否适用。如果为 None，则只选择 always_apply=True 的规则。
            args: 传递给 Agent 的参数，可能包含用于规则选择的上下文信息。
        """
        self.llm = llm
        self.args = args

    @byzerllm.prompt()
    def _build_selection_prompt(self, rule: RuleFile, context: str = "") -> str:
        """
        判断规则是否适用于当前任务。

        规则描述:
        {{ rule.description }}

        规则内容摘要 (前200字符):
        {{ rule.content[:200] }}

        {% if context %}
        任务上下文:
        {{ context }}
        {% endif %}

        基于以上信息，判断这条规则 (路径: {{ rule.file_path }}) 是否与当前任务相关并应该被应用？

        请以JSON格式返回结果:
        ```json
        {
            "is_relevant": true或false,
            "reason": "判断理由"
        }
        ```
        """
        # 注意：确保 rule 对象和 context 字典能够被 Jinja2 正确访问。
        # Pydantic模型可以直接在Jinja2中使用其属性。
        return {"rule": rule, "context": context}  # type: ignore

    def _evaluate_rule(
        self, rule: RuleFile, context: str
    ) -> tuple[RuleFile, bool, Optional[str]]:
        """
        评估单个规则是否适用于当前上下文。

        Args:
            rule: 要评估的规则
            context: 上下文信息

        Returns:
            tuple: (规则, 是否选中, 理由)
        """
        # 如果规则设置为总是应用，直接返回选中
        if rule.always_apply:
            return (rule, True, "规则设置为总是应用")

        # 如果没有LLM，无法评估non-always规则
        if self.llm is None:
            return (rule, False, "未提供LLM，无法评估non-always规则")

        try:
            prompt = self._build_selection_prompt.prompt(rule=rule, context=context)
            logger.debug(
                f"为规则 '{os.path.basename(rule.file_path)}' 生成的判断 Prompt (片段): {prompt[:200]}..."
            )

            result = None
            try:
                # 使用with_return_type方法获取结构化结果
                result = (
                    self._build_selection_prompt.with_llm(self.llm)
                    .with_return_type(RuleRelevance)
                    .run(rule=rule, context=context)
                )
                if result and result.is_relevant:
                    return (rule, True, result.reason)
                else:
                    return (rule, False, result.reason if result else "未提供理由")
            except Exception as e:
                logger.warning(
                    f"LLM 未能为规则 '{os.path.basename(rule.file_path)}' 提供有效响应: {e}"
                )
                return (rule, False, f"LLM评估出错: {str(e)}")

        except Exception as e:
            logger.error(
                f"评估规则 '{os.path.basename(rule.file_path)}' 时出错: {e}",
                exc_info=True,
            )
            return (rule, False, f"评估过程出错: {str(e)}")

    def select_rules(self, context: str) -> List[RuleFile]:
        """
        选择适用于当前上下文的规则。使用线程池并发评估规则。

        Args:
            context: 包含用于规则选择的上下文信息 (例如，用户指令、目标文件等)。

        Returns:
            List[RuleFile]: 选定的规则列表。
        """
        # 导入函数以避免循环依赖
        from ..api import get_parsed_rules

        rules = get_parsed_rules()
        selected_rules: List[RuleFile] = []
        logger.info(f"开始选择规则，总规则数: {len(rules)}")

        # 预先分类处理always_apply规则
        always_apply_rules = []
        need_llm_rules = []

        for rule in rules:
            if rule.always_apply:
                always_apply_rules.append(rule)
            elif self.llm is not None:
                need_llm_rules.append(rule)

        # 添加always_apply规则
        for rule in always_apply_rules:
            selected_rules.append(rule)
            logger.debug(
                f"规则 '{os.path.basename(rule.file_path)}' (AlwaysApply=True) 已自动选择。"
            )

        # 如果没有需要LLM评估的规则，直接返回结果
        if not need_llm_rules:
            logger.info(f"规则选择完成，选中规则数: {len(selected_rules)}")
            return selected_rules

        # 使用线程池并发评估规则
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # 提交所有评估任务
            future_to_rule = {
                executor.submit(self._evaluate_rule, rule, context): rule
                for rule in need_llm_rules
            }

            # 收集评估结果
            for future in concurrent.futures.as_completed(future_to_rule):
                rule, is_selected, reason = future.result()
                if is_selected:
                    selected_rules.append(rule)
                    logger.info(
                        f"规则 '{os.path.basename(rule.file_path)}' (AlwaysApply=False) 已被 LLM 选择，原因: {reason}"
                    )
                else:
                    logger.debug(
                        f"规则 '{os.path.basename(rule.file_path)}' (AlwaysApply=False) 未被 LLM 选择，原因: {reason}"
                    )

        logger.info(f"规则选择完成，选中规则数: {len(selected_rules)}")
        return selected_rules

    def get_selected_rules_content(self, context: str) -> Dict[str, str]:
        """
        获取选定规则的文件路径和内容字典。

        Args:
            context: 传递给 select_rules 的上下文。

        Returns:
            Dict[str, str]: 选定规则的 {file_path: content} 字典。
        """
        selected_rules = self.select_rules(context=context)
        # 使用 os.path.basename 获取文件名作为 key，如果需要的话
        # return {os.path.basename(rule.file_path): rule.content for rule in selected_rules}
        # 保持 file_path 作为 key
        return {rule.file_path: rule.content for rule in selected_rules}

    @byzerllm.prompt()
    def _build_always_apply_summary_prompt(self, rules: List[RuleFile]) -> str:
        """
        Merge all always-apply rules into a unified rule description.

        Below is the list of all always-apply rules ({{ rules|length }} rules in total):

        {% for rule in rules %}
        ## Rule {{ loop.index }}: {{ rule.file_path }}
        {% if rule.description %}
        **Description**: {{ rule.description }}
        {% endif %}
        {% if rule.globs %}
        **Applicable Files**: {{ rule.globs|join(', ') }}
        {% endif %}

        **Content**:
        {{ rule.content }}

        ---
        {% endfor %}

        Please merge all the above rules into a unified and concise rule description. Requirements:
        1. Keep all important rule points
        2. Remove duplicate content while preserving complementary information
        3. Organize content by logical grouping
        4. Generate a unified rule document that is easy to understand and follow

        ***Do not include any extraneous content, please start outputting the rule content directly.***
        ```
        """
        return {"rules": rules}  # type: ignore

    @byzerllm.prompt()
    def _build_conditional_rules_index_prompt(self, rules: List[RuleFile]) -> str:
        """
        Generate an index directory for all conditional rules.

        Below is the list of all conditional rules ({{ rules|length }} rules in total):

        {% for rule in rules %}
        ## Rule {{ loop.index }}: {{ rule.file_path }}
        {% if rule.description %}
        **Description**: {{ rule.description }}
        {% endif %}
        {% if rule.globs %}
        **Applicable Files**: {{ rule.globs|join(', ') }}
        {% endif %}

        **Content**:
        {{ rule.content }}

        ---
        {% endfor %}

        Please generate a detailed index directory for all the above conditional rules. Requirements:
        1. Provide concise descriptions and usage explanations for each rule to help users understand the purpose of the rules
        2. Explain when these rules should be selected and used
        3. Generate an easy-to-navigate and searchable directory structure that must include file paths

        ***Do not include any extraneous content, please start outputting the rule content directly.***
        """
        return {"rules": rules}  # type: ignore

    def generate_always_apply_summary(self) -> Optional[AlwaysApplyRuleSummary]:
        """
        生成所有必须应用规则的合并摘要。

        Returns:
            AlwaysApplyRuleSummary: 合并后的规则摘要，如果没有 LLM 则返回 None
        """
        if self.llm is None:
            logger.warning("未提供 LLM，无法生成必须应用规则摘要")
            return None

        # 导入函数以避免循环依赖
        from ..api import get_parsed_rules

        # 获取所有解析后的规则
        all_rules = get_parsed_rules()
        always_apply_rules = [rule for rule in all_rules if rule.always_apply]

        if not always_apply_rules:
            logger.info("未找到必须应用的规则")
            return AlwaysApplyRuleSummary(
                summary="未找到必须应用的规则。", rule_count=0, covered_areas=[]
            )

        logger.info(f"开始生成必须应用规则摘要，规则数量: {len(always_apply_rules)}")

        try:
            # 由于 prompt 现在不返回 JSON，我们需要直接获取字符串结果
            result_str = self._build_always_apply_summary_prompt.with_llm(self.llm).run(
                rules=always_apply_rules
            )
            if result_str:
                # 创建摘要对象
                result = AlwaysApplyRuleSummary(
                    summary=result_str,
                    rule_count=len(always_apply_rules),
                    covered_areas=[],  # 暂时为空，可以后续通过 LLM 分析生成
                )

                logger.info(f"成功生成必须应用规则摘要")
                return result
            else:
                logger.warning("LLM 未能生成有效的规则摘要")
                return None
        except Exception as e:
            logger.error(f"生成必须应用规则摘要时出错: {e}", exc_info=True)
            return None

    def generate_conditional_rules_index(self) -> Optional[ConditionalRulesIndex]:
        """
        生成所有条件规则的索引目录。

        Returns:
            ConditionalRulesIndex: 条件规则索引，如果没有 LLM 则返回 None
        """
        if self.llm is None:
            logger.warning("未提供 LLM，无法生成条件规则索引")
            return None

        # 导入函数以避免循环依赖
        from ..api import get_parsed_rules

        # 获取所有解析后的规则
        all_rules = get_parsed_rules()
        conditional_rules = [rule for rule in all_rules if not rule.always_apply]

        if not conditional_rules:
            logger.info("未找到条件规则")
            return ConditionalRulesIndex(
                index_content="未找到条件规则。", rule_count=0, categories=[]
            )

        logger.info(f"开始生成条件规则索引，规则数量: {len(conditional_rules)}")

        try:
            # 由于 prompt 现在不返回 JSON，我们需要直接获取字符串结果
            result_str = self._build_conditional_rules_index_prompt.with_llm(
                self.llm
            ).run(rules=conditional_rules)
            if result_str:
                # 创建索引对象
                result = ConditionalRulesIndex(
                    index_content=result_str,
                    rule_count=len(conditional_rules),
                    categories=[],  # 暂时为空，可以后续通过 LLM 分析生成
                )

                logger.info(f"成功生成条件规则索引")
                return result
            else:
                logger.warning("LLM 未能生成有效的规则索引")
                return None
        except Exception as e:
            logger.error(f"生成条件规则索引时出错: {e}", exc_info=True)
            return None

    def generate_init_rule(
        self, project_root: Optional[str] = None
    ) -> Optional[InitRule]:
        """
        使用 subagent 机制探索项目结构并生成初始化规则。

        Args:
            project_root: 项目根目录路径，如果为 None 则使用当前目录

        Returns:
            InitRule: 生成的初始化规则，如果失败则返回 None
        """
        if project_root is None:
            project_root = os.getcwd()

        logger.info(f"使用 subagent 机制开始生成初始化规则: {project_root}")

        try:
            # 探索项目结构
            project_info = self._explore_project_structure(project_root)
            logger.info(f"项目探索完成，检测到技术栈: {project_info['technologies']}")

            # 获取模型名称
            model_name = self._get_model_name()
            if not model_name:
                logger.error("无法获取模型名称，无法使用 subagent 机制")
                return None

            # 使用 subagent 机制生成规则
            success = self._generate_init_rule_with_subagent(
                project_info, model_name, project_root
            )

            if not success:
                logger.error("subagent 执行失败")
                return None

            # 检查生成的文件并读取内容
            rules_dir = self._find_rules_directory(project_root)
            if not rules_dir:
                logger.error("未找到 .autocoderrules 目录")
                return None

            init_file_path = os.path.join(rules_dir, "init.md")
            if not os.path.exists(init_file_path):
                logger.error(f"未找到生成的 init.md 文件: {init_file_path}")
                return None

            # 读取生成的内容
            with open(init_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if not content.strip():
                logger.error("生成的 init.md 文件为空")
                return None

            # 确定项目类型
            project_type = self._determine_project_type(project_info["technologies"])

            # 提取命令列表
            commands = self._extract_commands_from_content(content)

            # 创建 InitRule 对象
            result = InitRule(
                content=content,
                project_type=project_type,
                commands=commands,
                technologies=project_info["technologies"],
                file_path=init_file_path,
            )

            logger.info(f"成功使用 subagent 生成初始化规则，项目类型: {project_type}")
            return result

        except Exception as e:
            logger.error(f"使用 subagent 生成初始化规则时出错: {e}", exc_info=True)
            return None

    def _explore_project_structure(self, project_root: str) -> Dict:
        """探索项目结构，检测技术栈和配置文件"""
        project_info = {
            "root_files": [],
            "main_directories": [],
            "technologies": [],
            "package_json": None,
            "setup_py": None,
            "requirements_txt": None,
            "go_mod": None,
            "pyproject_toml": None,
            "tsconfig_json": None,
        }

        try:
            # 获取根目录文件
            if os.path.exists(project_root):
                root_items = os.listdir(project_root)

                # 分离文件和目录
                for item in root_items:
                    item_path = os.path.join(project_root, item)
                    if os.path.isfile(item_path):
                        project_info["root_files"].append(item)
                    elif os.path.isdir(item_path) and not item.startswith("."):
                        project_info["main_directories"].append(item)

                # 检测配置文件并读取内容
                config_files = {
                    "package.json": "package_json",
                    "setup.py": "setup_py",
                    "requirements.txt": "requirements_txt",
                    "go.mod": "go_mod",
                    "pyproject.toml": "pyproject_toml",
                    "tsconfig.json": "tsconfig_json",
                }

                for filename, key in config_files.items():
                    file_path = os.path.join(project_root, filename)
                    if os.path.exists(file_path):
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()
                                project_info[key] = content[:1000]  # 限制内容长度
                        except Exception as e:
                            logger.warning(f"读取 {filename} 时出错: {e}")

                # 检测技术栈
                project_info["technologies"] = self._detect_technologies(project_info)

        except Exception as e:
            logger.error(f"探索项目结构时出错: {e}")

        return project_info

    def _detect_technologies(self, project_info: Dict) -> List[str]:
        """根据配置文件检测技术栈"""
        technologies = []

        # Python
        if (
            project_info["setup_py"]
            or project_info["requirements_txt"]
            or project_info["pyproject_toml"]
        ):
            technologies.append("Python")

        # JavaScript/TypeScript
        if project_info["package_json"]:
            technologies.append("JavaScript")
            try:
                import json

                package_data = json.loads(project_info["package_json"])
                dependencies = {
                    **package_data.get("dependencies", {}),
                    **package_data.get("devDependencies", {}),
                }

                if "typescript" in dependencies or project_info["tsconfig_json"]:
                    technologies.append("TypeScript")

                if "react" in dependencies:
                    technologies.append("React")

                if "vue" in dependencies:
                    technologies.append("Vue")

                if "express" in dependencies:
                    technologies.append("Node.js")

            except Exception as e:
                logger.warning(f"解析 package.json 时出错: {e}")

        # Go
        if project_info["go_mod"]:
            technologies.append("Go")

        # 其他检测
        if "src" in project_info["main_directories"]:
            if not technologies:  # 如果还没检测到技术栈，根据目录结构猜测
                technologies.append("General")

        return technologies if technologies else ["Unknown"]

    def _determine_project_type(self, technologies: List[str]) -> str:
        """根据技术栈确定项目类型"""
        if "React" in technologies:
            return "React Application"
        elif "Vue" in technologies:
            return "Vue Application"
        elif "TypeScript" in technologies:
            return "TypeScript Project"
        elif "JavaScript" in technologies:
            return "JavaScript Project"
        elif "Python" in technologies:
            return "Python Project"
        elif "Go" in technologies:
            return "Go Project"
        else:
            return "General Project"

    def _extract_commands_from_content(self, content: str) -> List[str]:
        """从生成的内容中提取命令列表"""
        commands = []
        lines = content.split("\n")
        in_commands_section = False

        for line in lines:
            line = line.strip()
            if line.lower().startswith("# bash commands"):
                in_commands_section = True
                continue
            elif line.startswith("#") and in_commands_section:
                in_commands_section = False
            elif in_commands_section and line.startswith("-"):
                # 提取命令名称
                command_part = line[1:].strip()
                if ":" in command_part:
                    command_name = command_part.split(":")[0].strip()
                    commands.append(command_name)

        return commands

    def _get_model_name(self) -> Optional[str]:
        """
        获取当前可用的模型名称

        Returns:
            当前模型名称，如果没有则返回 None
        """
        try:
            # 尝试从 args 中获取模型信息
            if self.args and hasattr(self.args, "model") and self.args.model:
                return self.args.model

            # 尝试从 llm 实例获取模型名称
            if self.llm:
                if (
                    hasattr(self.llm, "default_model_name")
                    and self.llm.default_model_name
                ):
                    return self.llm.default_model_name
                elif hasattr(self.llm, "model_name") and self.llm.model_name:
                    return self.llm.model_name
                elif hasattr(self.llm, "model") and self.llm.model:
                    return self.llm.model

            # 尝试从环境变量获取
            env_model = os.getenv("AUTO_CODER_MODEL")
            if env_model:
                return env_model

            # 默认模型
            return "v3_chat"

        except Exception as e:
            logger.warning(f"获取模型名称时出错: {str(e)}")
            return "v3_chat"

    def _generate_init_rule_with_subagent(
        self, project_info: Dict, model_name: str, project_root: str
    ) -> bool:
        """
        使用 subagent 机制生成初始化规则

        Args:
            project_info: 项目信息
            model_name: 模型名称
            project_root: 项目根目录

        Returns:
            是否成功
        """
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".md", delete=False, encoding="utf-8"
            ) as temp_file:
                temp_file_path = temp_file.name

                # 构建指令内容
                instruction_content = self._build_subagent_instruction(
                    project_info, project_root
                )
                temp_file.write(instruction_content)

            logger.info(f"创建临时指令文件: {temp_file_path}")

            try:
                # 切换到项目根目录执行命令
                original_cwd = os.getcwd()
                os.chdir(project_root)

                # 构建并执行 auto-coder.run 命令（跨平台兼容）
                # 使用 shutil.which 获取命令完整路径，确保 Windows 兼容性
                autocoder_cmd = shutil.which("auto-coder.run")
                if not autocoder_cmd and platform.system() == "Windows":
                    autocoder_cmd = shutil.which("auto-coder.run.exe")
                if not autocoder_cmd:
                    autocoder_cmd = "auto-coder.run"

                cmd_args = [autocoder_cmd, "--model", model_name]
                logger.info(f"执行 subagent 命令: {' '.join(cmd_args)}")

                # 读取临时文件内容
                with open(temp_file_path, "r", encoding="utf-8") as f:
                    input_content = f.read()

                # 构建环境变量（Windows UTF-8 兼容）
                env = os.environ.copy()
                if platform.system() == "Windows":
                    env.update(
                        {
                            "PYTHONIOENCODING": "utf-8",
                            "LANG": "zh_CN.UTF-8",
                            "LC_ALL": "zh_CN.UTF-8",
                        }
                    )

                # 执行命令（使用 input 参数替代 cat | 管道）
                result = subprocess.run(
                    cmd_args,
                    input=input_content,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=env,
                    timeout=300,  # 5分钟超时
                )

                if result.returncode == 0:
                    logger.info("subagent 命令执行成功")
                    if result.stdout:
                        logger.info(f"命令输出: {result.stdout}")
                    return True
                else:
                    logger.error(f"subagent 命令执行失败，返回码: {result.returncode}")
                    if result.stderr:
                        logger.error(f"错误输出: {result.stderr}")
                    if result.stdout:
                        logger.error(f"标准输出: {result.stdout}")
                    return False

            finally:
                # 恢复原始工作目录
                os.chdir(original_cwd)

                # 清理临时文件
                try:
                    os.unlink(temp_file_path)
                    logger.info(f"已清理临时文件: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"清理临时文件时出错: {e}")

        except subprocess.TimeoutExpired:
            logger.error("subagent 命令执行超时")
            return False
        except Exception as e:
            logger.error(f"执行 subagent 命令时出错: {e}", exc_info=True)
            return False

    def _build_subagent_instruction(self, project_info: Dict, project_root: str) -> str:
        """
        构建 subagent 的指令内容

        Args:
            project_info: 项目信息
            project_root: 项目根目录

        Returns:
            指令内容
        """
        # 构建项目信息描述
        project_description = ""

        if project_info.get("package_json"):
            project_description += f"\n**发现 package.json 文件**:\n```json\n{project_info['package_json'][:500]}...\n```\n"

        if project_info.get("setup_py"):
            project_description += f"\n**发现 setup.py 文件**:\n```python\n{project_info['setup_py'][:500]}...\n```\n"

        if project_info.get("requirements_txt"):
            project_description += f"\n**发现 requirements.txt 文件**:\n```\n{project_info['requirements_txt'][:300]}...\n```\n"

        if project_info.get("go_mod"):
            project_description += f"\n**发现 go.mod 文件**:\n```\n{project_info['go_mod'][:300]}...\n```\n"

        if project_info.get("pyproject_toml"):
            project_description += f"\n**发现 pyproject.toml 文件**:\n```toml\n{project_info['pyproject_toml'][:500]}...\n```\n"

        if project_info.get("tsconfig_json"):
            project_description += f"\n**发现 tsconfig.json 文件**:\n```json\n{project_info['tsconfig_json'][:300]}...\n```\n"

        root_files = ", ".join(project_info.get("root_files", [])[:10])
        main_directories = ", ".join(project_info.get("main_directories", [])[:10])
        technologies = ", ".join(project_info.get("technologies", []))

        instruction = f"""请分析当前项目结构并在 .autocoderrules 目录下生成一个 init.md 文件，包含项目的开发规则和指导。

## 项目信息

**项目根目录**: {project_root}
**根目录文件**: {root_files}
**主要目录**: {main_directories}
**检测到的技术栈**: {technologies}

{project_description}

## 任务要求

请根据上述项目信息，在 `.autocoderrules` 目录下创建一个 `init.md` 文件，内容应该包括：

### 1. Bash commands
列出常用的构建、测试、运行命令，格式如下：
```
# Bash commands
- command_name: 命令描述
- another_command: 另一个命令描述
```

### 2. Code style  
根据检测到的技术栈，提供相应的编码规范，例如：
```
# Code style
- 使用一致的代码格式化规则
- 遵循对应语言的最佳实践
```

### 3. Workflow
提供开发工作流建议：
```
# Workflow
- 开发流程建议
- 测试和部署流程
```

### 4. Technology-specific rules
针对具体技术栈的特殊规则：
```
# Technology-specific rules
- 技术栈特定的规则
- 框架相关的最佳实践
```

## 注意事项

1. 如果 `.autocoderrules` 目录不存在，请先创建该目录
2. 根据实际检测到的技术栈生成相应的规则
3. 确保生成的规则实用且具体
4. 命令应该是项目中实际可能用到的
5. 规则应该帮助开发者快速上手项目开发

请立即开始分析项目并生成 init.md 文件。
"""

        return instruction

    def _find_rules_directory(self, project_root: str) -> Optional[str]:
        """
        查找现有的 .autocoderrules 目录

        Args:
            project_root: 项目根目录

        Returns:
            找到的规则目录路径，如果没找到则返回 None
        """
        try:
            # 按优先级顺序查找
            possible_dirs = [
                os.path.join(project_root, ".autocoderrules"),
                os.path.join(project_root, ".auto-coder", ".autocoderrules"),
                os.path.join(project_root, ".auto-coder", "autocoderrules"),
            ]

            for rules_dir in possible_dirs:
                if os.path.exists(rules_dir) and os.path.isdir(rules_dir):
                    logger.info(f"找到现有的规则目录: {rules_dir}")
                    return rules_dir

            # 如果没有找到现有目录，返回默认的第一个位置
            default_dir = possible_dirs[0]
            logger.info(f"未找到现有规则目录，返回默认位置: {default_dir}")
            return default_dir

        except Exception as e:
            logger.error(f"查找规则目录时出错: {e}")
            return None
