"""
Workflow Runner - 便捷的入口函数

提供简单易用的 API 来运行 workflow。
"""

from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from loguru import logger

from autocoder.common import AutoCoderArgs
from autocoder.utils.llms import get_single_llm
from autocoder.workflow_agents.types import WorkflowResult, StepStatus
from autocoder.workflow_agents.loader import load_workflow_from_yaml
from autocoder.workflow_agents.executor import SubagentWorkflowExecutor
from autocoder.workflow_agents.workflow_manager import WorkflowManager
from autocoder.workflow_agents.exceptions import (
    WorkflowError,
    WorkflowFileNotFoundError,
    WorkflowParseError,
    WorkflowValidationError,
)
from autocoder.inner.agentic import RunAgentic

# 状态图标映射
STATUS_ICONS = {
    StepStatus.SUCCESS: "✅",
    StepStatus.FAILED: "❌",
    StepStatus.SKIPPED: "⏭️",
}


def run_workflow_from_yaml(
    yaml_path: str,
    source_dir: Optional[str] = None,
    model: Optional[str] = None,
    product_mode: str = "lite",
    vars_override: Optional[Dict[str, Any]] = None,
    skip_build_index: bool = True,
    skip_filter_index: bool = True,
    cancel_token: Optional[str] = None,
) -> WorkflowResult:
    """
    从 YAML 文件运行 workflow 的便捷函数

    支持两种方式指定 workflow 文件：
    1. 完整路径：如 "/path/to/workflow.yaml"
    2. workflow 名称：如 "my-workflow"，会按优先级在以下目录查找：
       - .autocoderworkflow/
       - .auto-coder/.autocoderworkflow/
       - ~/.auto-coder/.autocoderworkflow/

    Args:
        yaml_path: YAML workflow 配置文件路径或 workflow 名称
        source_dir: 项目源码目录，默认为当前目录
        model: LLM 模型名称，默认使用 workflow 中配置的模型
        product_mode: 产品模式，默认为 'lite'
        vars_override: 覆盖 YAML 中的变量
        skip_build_index: 是否跳过索引构建，默认 True
        skip_filter_index: 是否跳过索引过滤，默认 True
        cancel_token: 取消令牌，用于支持任务取消

    Returns:
        WorkflowResult 对象，包含执行状态和所有步骤的结果

    Example:
        >>> # 使用完整路径
        >>> result = run_workflow_from_yaml(
        ...     yaml_path="workflow.yaml",
        ...     source_dir="/path/to/project",
        ...     vars_override={"query": "实现用户登录功能"}
        ... )

        >>> # 使用 workflow 名称（自动查找）
        >>> result = run_workflow_from_yaml(
        ...     yaml_path="my-workflow",  # 会在优先级目录中查找
        ...     source_dir="/path/to/project"
        ... )

        >>> if result.success:
        ...     print("Workflow 执行成功！")
        ...     for step_result in result.step_results:
        ...         print(f"步骤 {step_result.step_id}: {step_result.status}")
    """
    try:
        # 确定 source_dir
        if source_dir is None:
            source_dir = str(Path.cwd())

        # 解析 yaml_path - 支持完整路径或 workflow 名称
        resolved_path = _resolve_workflow_path(yaml_path, source_dir)
        if not resolved_path:
            # 获取已搜索的路径用于错误提示
            manager = WorkflowManager(project_root=source_dir)
            searched_paths = [str(p) for p in manager._get_workflow_search_paths()]

            error = WorkflowFileNotFoundError(
                workflow_name=yaml_path, searched_paths=searched_paths
            )
            error_msg = str(error)
            logger.error(error_msg)
            return WorkflowResult(
                success=False, context={}, step_results=[], error=error_msg
            )

        # 加载 workflow 配置
        logger.info(f"加载 workflow 配置: {resolved_path}")
        workflow_spec = load_workflow_from_yaml(resolved_path)

        # 覆盖变量
        if vars_override:
            workflow_spec.spec.vars.update(vars_override)
            logger.debug(f"覆盖变量: {list(vars_override.keys())}")

        # 创建执行上下文（args 和 llm）
        args, llm = _create_workflow_context(
            workflow_spec=workflow_spec,
            source_dir=source_dir,
            model=model,
            product_mode=product_mode,
            skip_build_index=skip_build_index,
            skip_filter_index=skip_filter_index,
        )

        # 创建执行器并运行
        executor = SubagentWorkflowExecutor(workflow_spec, args, llm, cancel_token)
        result = executor.run()

        return result

    except WorkflowError as e:
        # 我们自己定义的异常，已经有友好的错误信息
        error_msg = str(e)
        logger.error(f"Workflow 错误:\n{error_msg}")
        return WorkflowResult(
            success=False, context={}, step_results=[], error=error_msg
        )
    except Exception as e:
        # 未预期的异常
        error_msg = f"运行 workflow 时发生未预期的错误: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return WorkflowResult(
            success=False, context={}, step_results=[], error=error_msg
        )


def _create_workflow_context(
    workflow_spec: Any,
    source_dir: str,
    model: Optional[str],
    product_mode: str,
    skip_build_index: bool,
    skip_filter_index: bool,
) -> Tuple[AutoCoderArgs, Any]:
    """
    创建 workflow 执行所需的上下文（args 和 llm）

    Args:
        workflow_spec: workflow 规格
        source_dir: 源码目录
        model: 模型名称（可选）
        product_mode: 产品模式
        skip_build_index: 是否跳过索引构建
        skip_filter_index: 是否跳过索引过滤

    Returns:
        (args, llm) 元组
    """
    # 使用 workflow 中配置的模型，如果没有则使用传入的参数
    workflow_model = workflow_spec.spec.globals.model
    final_model = model if model else workflow_model

    run_agentic = RunAgentic()
    args = run_agentic._get_final_config()
    args.source_dir = source_dir
    args.model = final_model
    args.product_mode = product_mode
    args.skip_build_index = skip_build_index
    args.skip_filter_index = skip_filter_index

    # 获取 LLM
    logger.info(f"初始化 LLM: model={final_model}, product_mode={product_mode}")
    llm = get_single_llm(model_names=final_model, product_mode=product_mode)

    return args, llm


def _resolve_workflow_path(yaml_path: str, source_dir: str) -> Optional[str]:
    """
    解析 workflow 路径

    如果是完整路径则直接返回，否则在优先级目录中查找。

    Args:
        yaml_path: workflow 路径或名称
        source_dir: 项目源码目录

    Returns:
        解析后的完整路径，如果未找到则返回 None
    """
    path = Path(yaml_path)

    # 如果是绝对路径或相对路径且文件存在，直接返回
    if path.is_absolute():
        return str(path) if path.exists() else None

    # 如果是相对于当前目录的路径且存在
    if path.exists():
        return str(path.resolve())

    # 否则，作为 workflow 名称在优先级目录中查找
    workflow_name = path.stem  # 去除扩展名
    manager = WorkflowManager(project_root=source_dir)
    return manager.find_workflow(workflow_name)


def list_available_workflows(source_dir: Optional[str] = None) -> Dict[str, str]:
    """
    列出所有可用的 workflow

    Args:
        source_dir: 项目源码目录，默认为当前目录

    Returns:
        字典，key 为 workflow 名称，value 为文件路径
    """
    if source_dir is None:
        source_dir = str(Path.cwd())

    manager = WorkflowManager(project_root=source_dir)
    return manager.list_workflows()


def print_workflow_result(result: WorkflowResult) -> None:
    """
    打印 workflow 执行结果的便捷函数

    Args:
        result: WorkflowResult 对象
    """
    print("\n" + "=" * 60)
    if result.success:
        print("✅ Workflow 执行成功")
    else:
        print(f"❌ Workflow 执行失败: {result.error}")
    print("=" * 60)

    print(f"\n步骤执行情况 (共 {len(result.step_results)} 个步骤):")
    for step_result in result.step_results:
        status_icon = STATUS_ICONS.get(step_result.status, "❓")

        print(f"\n  {status_icon} 步骤: {step_result.step_id}")
        print(f"     状态: {step_result.status.value}")

        if step_result.error:
            print(f"     错误: {step_result.error}")

        if step_result.attempt_result:
            preview = step_result.attempt_result[:100]
            if len(step_result.attempt_result) > 100:
                preview += "..."
            print(f"     结果: {preview}")

        if step_result.outputs:
            print(f"     输出: {list(step_result.outputs.keys())}")

    print("\n" + "=" * 60)
