import os
import time
import signal
import psutil
from typing import Optional, Dict, List, Any, Tuple
from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import BaseToolResolver
from autocoder.common.v2.agent.agentic_edit_types import BackgroundTaskTool, ToolResult
from autocoder.common import AutoCoderArgs
from autocoder.common.shell_commands import get_background_process_notifier, get_background_processes, get_background_process_info
from loguru import logger
import typing

if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class BackgroundTaskToolResolver(BaseToolResolver):
    """统一的后台任务管理工具解析器"""
    
    def __init__(self, agent: Optional['AgenticEdit'], tool: BackgroundTaskTool, args: AutoCoderArgs):
        super().__init__(agent, tool, args)
        self.tool: BackgroundTaskTool = tool

    def resolve(self) -> ToolResult:
        """
        根据 action 参数执行相应的后台任务操作
        
        Returns:
            ToolResult: 操作结果
        """
        try:
            # 获取当前会话ID
            conversation_id = self.agent.conversation_config.conversation_id if self.agent else None
            if not conversation_id:
                return ToolResult(
                    success=False,
                    message="无法获取当前会话ID",
                    content={"action": self.tool.action, "error": "missing_agent_or_config"}
                )
            
            # 根据 action 参数调用相应的方法
            if self.tool.action == "list":
                return self._handle_list_action(conversation_id)
            elif self.tool.action == "monitor":
                return self._handle_monitor_action(conversation_id)
            elif self.tool.action == "cleanup":
                return self._handle_cleanup_action(conversation_id)
            elif self.tool.action == "kill":
                return self._handle_kill_action(conversation_id)
            else:
                return ToolResult(
                    success=False,
                    message=f"不支持的操作类型: {self.tool.action}。支持的操作: list, monitor, cleanup, kill",
                    content={"action": self.tool.action, "error": "unsupported_action"}
                )
                
        except Exception as e:
            logger.error(f"BackgroundTaskTool execution failed: {str(e)}")
            return ToolResult(
                success=False,
                message=f"后台任务操作失败: {str(e)}",
                content={"action": self.tool.action, "error": str(e)}
            )
    
    def _handle_list_action(self, conversation_id: str) -> ToolResult:
        """处理列出任务的操作"""
        try:
            # 获取后台进程通知器
            notifier = get_background_process_notifier()
            
            # 获取全局后台进程列表
            bg_processes = get_background_processes()
            if not bg_processes:
                bg_processes = {}
            
            # 收集任务信息
            running_tasks = []
            completed_tasks = []
            
            # 从通知器获取注册的任务信息
            with notifier._lock:
                registrations = dict(notifier._registrations)
                reported = set(notifier._reported)
                pending_messages = dict(notifier._pending_messages)
            
            # 处理注册的任务
            for key, reg in registrations.items():
                if reg.conversation_id != conversation_id:
                    continue
                    
                pid, start_time = key
                
                # 应用任务类型过滤（兼容不同的工具命名）
                if self.tool.task_type:
                    category = self._classify_tool_name(reg.tool_name)
                    if category != self.tool.task_type:
                        continue
                
                # 获取进程信息
                process_info = bg_processes.get(pid, {})
                status = process_info.get("status", "unknown")
                
                task_info = {
                    "task_id": reg.task_id,
                    "pid": pid,
                    "process_uniq_id": process_info.get("process_uniq_id") if process_info else None,
                    "tool_name": reg.tool_name,
                    "status": status,
                    "command": reg.command,
                    "cwd": reg.cwd,
                    "agent_name": reg.agent_name,
                    "task": reg.task,
                    "start_time": reg.start_time,
                    "running_time": time.time() - reg.start_time
                }
                
                if status == "completed":
                    task_info["exit_code"] = process_info.get("exit_code")
                    task_info["end_time"] = process_info.get("end_time")
                    completed_tasks.append(task_info)
                else:
                    running_tasks.append(task_info)
            
            # 从待处理消息中获取已完成的任务
            if conversation_id in pending_messages:
                for msg in pending_messages[conversation_id]:
                    # 应用任务类型过滤（暂时不考虑）
                    # if self.tool.task_type:
                    #     if self.tool.task_type == "command" and msg.tool_name != "ExecuteCommandTool":
                    #         continue
                    #     elif self.tool.task_type == "subagent" and msg.tool_name != "RunNamedSubagentsTool":
                    #         continue
                    
                    task_info = {
                        "task_id": msg.task_id,
                        "pid": msg.pid,
                        "tool_name": msg.tool_name,
                        "status": msg.status,
                        "command": msg.command,
                        "cwd": msg.cwd,
                        "agent_name": msg.agent_name,
                        "task": msg.task,
                        "exit_code": msg.exit_code,
                        "running_time": msg.duration_sec,
                        "completed_at": msg.completed_at
                    }
                    completed_tasks.append(task_info)
            
            # 格式化输出
            output_lines = []
            
            if running_tasks:
                output_lines.append(f"正在运行的后台任务 ({len(running_tasks)}个):")
                output_lines.append("")
                
                for i, task in enumerate(running_tasks, 1):
                    id_info = f"ID: {task['process_uniq_id']}" if task.get('process_uniq_id') else f"PID: {task['pid']}"
                    output_lines.append(f"{i}. [{task['tool_name']}] {id_info} | 状态: {task['status']} | 运行时间: {self._format_duration(task['running_time'])}")
                    
                    if self._classify_tool_name(task['tool_name']) == 'command':
                        output_lines.append(f"   命令: {task['command']}")
                        if task['cwd']:
                            output_lines.append(f"   工作目录: {task['cwd']}")
                    elif self._classify_tool_name(task['tool_name']) == 'subagent':
                        if task['agent_name']:
                            output_lines.append(f"   代理: {task['agent_name']}")
                        if task['task']:
                            # 限制任务描述长度
                            task_desc = task['task'][:100] + "..." if len(task['task']) > 100 else task['task']
                            output_lines.append(f"   任务: {task_desc}")
                    
                    output_lines.append("")
            else:
                output_lines.append("当前没有正在运行的后台任务")
                output_lines.append("")
            
            if self.tool.show_completed and completed_tasks:
                output_lines.append(f"已完成的任务 ({len(completed_tasks)}个):")
                output_lines.append("")
                
                for i, task in enumerate(completed_tasks, 1):
                    status_icon = "✅" if task['status'] == 'completed' else "❌"
                    duration = task.get('running_time', 0)
                    exit_code = task.get('exit_code', 'N/A')
                    
                    id_info = f"ID: {task.get('process_uniq_id')}" if task.get('process_uniq_id') else f"PID: {task['pid']}"
                    output_lines.append(f"{i}. [{task['tool_name']}] {id_info} | 状态: {task['status']} {status_icon} | 退出码: {exit_code} | 运行时间: {self._format_duration(duration)}")
                    
                    if self._classify_tool_name(task['tool_name']) == 'command':
                        output_lines.append(f"   命令: {task['command']}")
                    elif self._classify_tool_name(task['tool_name']) == 'subagent':
                        if task['agent_name']:
                            output_lines.append(f"   代理: {task['agent_name']}")
                        if task['task']:
                            task_desc = task['task'][:100] + "..." if len(task['task']) > 100 else task['task']
                            output_lines.append(f"   任务: {task_desc}")
                    
                    output_lines.append("")
            
            # 构建结果
            result_content = {
                "action": "list",
                "running_tasks": running_tasks,
                "completed_tasks": completed_tasks if self.tool.show_completed else [],
                "summary": {
                    "running_count": len(running_tasks),
                    "completed_count": len(completed_tasks),
                    "total_count": len(running_tasks) + len(completed_tasks)
                }
            }
            
            message = "\n".join(output_lines).strip()
            if not message:
                message = "当前没有后台任务"
            
            return ToolResult(
                success=True,
                message=message,
                content=result_content
            )
            
        except Exception as e:
            logger.error(f"List action failed: {str(e)}")
            return ToolResult(
                success=False,
                message=f"获取后台任务列表失败: {str(e)}",
                content={"action": "list", "error": str(e)}
            )
    
    def _handle_monitor_action(self, conversation_id: str) -> ToolResult:
        """处理监控任务输出的操作"""
        try:
            # 验证参数
            if not self.tool.task_id and not self.tool.pid and not self.tool.process_uniq_id:
                return ToolResult(
                    success=False,
                    message="monitor 操作必须提供 task_id、pid 或 process_uniq_id 参数",
                    content={
                        "action": "monitor",
                        "tasks": [],
                        "output_type": self.tool.output_type,
                        "lines_requested": self.tool.lines,
                        "task_count": 0,
                        "error": "missing_required_params"
                    }
                )
            
            # 获取后台进程通知器和进程信息
            notifier = get_background_process_notifier()
            bg_processes = get_background_processes()
            if not bg_processes:
                bg_processes = {}
            
            # 查找目标任务
            target_tasks = []
            
            if self.tool.task_id:
                # 通过 task_id 查找
                target_tasks = self._find_tasks_by_task_id(notifier, conversation_id, self.tool.task_id)
            elif self.tool.pid:
                # 通过 pid 查找
                target_tasks = self._find_tasks_by_pid(notifier, conversation_id, self.tool.pid)
            elif self.tool.process_uniq_id:
                # 通过 process_uniq_id 查找
                target_tasks = self._find_tasks_by_process_uniq_id(notifier, conversation_id, self.tool.process_uniq_id)
            
            if not target_tasks:
                if self.tool.task_id:
                    identifier = f"task_id={self.tool.task_id}"
                elif self.tool.pid:
                    identifier = f"pid={self.tool.pid}"
                else:
                    identifier = f"process_uniq_id={self.tool.process_uniq_id}"
                return ToolResult(
                    success=False,
                    message=f"未找到指定的任务: {identifier}",
                    content={
                        "action": "monitor",
                        "tasks": [],
                        "output_type": self.tool.output_type,
                        "lines_requested": self.tool.lines,
                        "task_count": 0,
                        "error": "task_not_found"
                    }
                )
            
            # 收集所有任务的输出
            output_sections = []
            
            for task_info in target_tasks:
                pid = task_info['pid']
                task_id = task_info['task_id']
                
                # 获取进程信息
                process_info = bg_processes.get(pid)
                if not process_info:
                    output_sections.append(f"任务 {task_id} (PID: {pid}) - 进程信息不可用")
                    continue
                
                # 构建任务头部信息
                process_uniq_id = process_info.get('process_uniq_id') if process_info else task_info.get('process_uniq_id')
                id_display = f"ID: {process_uniq_id}" if process_uniq_id else f"PID: {pid}"
                header_lines = [
                    f"任务 {task_id} ({id_display}) 输出:",
                    f"工具: {task_info['tool_name']}",
                    f"状态: {process_info.get('status', 'unknown')}",
                ]
                
                if task_info['tool_name'] == 'execute_command':
                    header_lines.append(f"命令: {task_info['command']}")
                elif task_info['tool_name'] == 'run_named_subagents':
                    if task_info.get('agent_name'):
                        header_lines.append(f"代理: {task_info['agent_name']}")
                    if task_info.get('task'):
                        task_desc = task_info['task'][:100] + "..." if len(task_info['task']) > 100 else task_info['task']
                        header_lines.append(f"任务: {task_desc}")
                
                if task_info.get('cwd'):
                    header_lines.append(f"工作目录: {task_info['cwd']}")
                
                header_lines.append("")
                
                # 获取输出内容
                stdout_content, stderr_content = self._get_process_output(process_info, pid)
                
                # 根据 output_type 参数决定显示哪些输出
                if self.tool.output_type in ["stdout", "both"] and stdout_content:
                    stdout_lines = self._format_output_lines(stdout_content, self.tool.lines, "STDOUT")
                    header_lines.extend(stdout_lines)
                    header_lines.append("")
                
                if self.tool.output_type in ["stderr", "both"] and stderr_content:
                    stderr_lines = self._format_output_lines(stderr_content, self.tool.lines, "STDERR")
                    header_lines.extend(stderr_lines)
                    header_lines.append("")
                
                # 如果没有输出内容
                if not stdout_content and not stderr_content:
                    header_lines.append("暂无输出内容")
                    header_lines.append("")
                
                output_sections.append("\n".join(header_lines))
            
            # 构建最终输出
            if len(target_tasks) == 1:
                message = output_sections[0].strip()
            else:
                message = "\n".join([
                    f"找到 {len(target_tasks)} 个匹配的任务:",
                    "=" * 80,
                    "\n".join(output_sections)
                ]).strip()
            
            # 构建结果内容
            result_content = {
                "action": "monitor",
                "tasks": target_tasks,
                "output_type": self.tool.output_type,
                "lines_requested": self.tool.lines,
                "task_count": len(target_tasks)
            }
            
            return ToolResult(
                success=True,
                message=message,
                content=result_content
            )
            
        except Exception as e:
            logger.error(f"Monitor action failed: {str(e)}")
            return ToolResult(
                success=False,
                message=f"监控后台任务失败: {str(e)}",
                content={"action": "monitor", "error": str(e), "task_count": 0}
            )
    
    def _handle_cleanup_action(self, conversation_id: str) -> ToolResult:
        """处理清理任务的操作"""
        try:
            # 获取后台进程通知器
            notifier = get_background_process_notifier()
            bg_processes = get_background_processes()
            if not bg_processes:
                bg_processes = {}
            
            # 收集要清理的任务
            tasks_to_cleanup = []
            
            with notifier._lock:
                registrations = dict(notifier._registrations)
                reported = set(notifier._reported)
                pending_messages = dict(notifier._pending_messages)
            
            current_time = time.time()
            
            # 检查已报告的任务（已完成的注册任务）
            for key in list(reported):
                # 这些任务已经完成并报告，可以安全清理
                if key in registrations:
                    reg = registrations[key]
                    if reg.conversation_id == conversation_id:
                        # 应用过滤条件
                        if self._should_cleanup_task(reg, None, current_time):
                            tasks_to_cleanup.append({
                                "type": "reported_registration",
                                "key": key,
                                "task_id": reg.task_id,
                                "pid": key[0],
                                "tool_name": reg.tool_name,
                                "status": "completed"
                            })
            
            # 检查待处理消息中的已完成任务
            if conversation_id in pending_messages:
                messages_to_remove = []
                for i, msg in enumerate(pending_messages[conversation_id]):
                    # 应用过滤条件
                    if self._should_cleanup_message(msg, current_time):
                        tasks_to_cleanup.append({
                            "type": "pending_message",
                            "index": i,
                            "task_id": msg.task_id,
                            "pid": msg.pid,
                            "tool_name": msg.tool_name,
                            "status": msg.status
                        })
                        messages_to_remove.append(i)
            
            # 如果指定了特定的 task_ids，只清理这些任务
            if self.tool.task_ids:
                tasks_to_cleanup = [
                    task for task in tasks_to_cleanup 
                    if task["task_id"] in self.tool.task_ids
                ]
            
            if not tasks_to_cleanup:
                return ToolResult(
                    success=True,
                    message="没有找到符合条件的任务需要清理",
                    content={
                        "action": "cleanup",
                        "cleaned_count": 0,
                        "cleaned_tasks": [],
                        "remaining_active": self._count_active_tasks(notifier, conversation_id)
                    }
                )
            
            # 执行清理操作
            cleaned_tasks = []
            memory_freed = 0
            
            with notifier._lock:
                # 清理已报告的注册任务
                for task in tasks_to_cleanup:
                    if task["type"] == "reported_registration":
                        key = task["key"]
                        if key in notifier._reported:
                            notifier._reported.remove(key)
                        if key in notifier._registrations:
                            del notifier._registrations[key]
                        # 更新 pid_to_key 映射
                        pid = key[0]
                        if pid in notifier._pid_to_key and notifier._pid_to_key[pid] == key:
                            del notifier._pid_to_key[pid]
                        
                        cleaned_tasks.append(task)
                        memory_freed += self._estimate_task_memory_usage(task)
                
                # 清理待处理消息
                if conversation_id in notifier._pending_messages:
                    messages_to_remove = [
                        task["index"] for task in tasks_to_cleanup 
                        if task["type"] == "pending_message"
                    ]
                    # 按索引降序排列，避免删除时索引变化
                    messages_to_remove.sort(reverse=True)
                    
                    for index in messages_to_remove:
                        if index < len(notifier._pending_messages[conversation_id]):
                            removed_msg = notifier._pending_messages[conversation_id].pop(index)
                            memory_freed += self._estimate_message_memory_usage(removed_msg)
                            
                            # 找到对应的任务并添加到清理列表
                            for task in tasks_to_cleanup:
                                if (task["type"] == "pending_message" and 
                                    task["index"] == index):
                                    cleaned_tasks.append(task)
                                    break
                    
                    # 如果队列为空，删除整个条目
                    if not notifier._pending_messages[conversation_id]:
                        del notifier._pending_messages[conversation_id]
            
            # 统计清理结果
            completed_count = len([t for t in cleaned_tasks if t["status"] == "completed"])
            failed_count = len([t for t in cleaned_tasks if t["status"] == "failed"])
            
            # 构建输出消息
            output_lines = [
                "清理后台任务完成:",
                f"- 已清理 {completed_count} 个已完成任务",
                f"- 已清理 {failed_count} 个失败任务",
                f"- 释放内存约 {self._format_memory_size(memory_freed)}",
                "",
                f"剩余活跃任务: {self._count_active_tasks(notifier, conversation_id)} 个正在运行"
            ]
            
            # 构建结果内容
            result_content = {
                "action": "cleanup",
                "cleaned_count": len(cleaned_tasks),
                "cleaned_tasks": cleaned_tasks,
                "completed_count": completed_count,
                "failed_count": failed_count,
                "memory_freed_bytes": memory_freed,
                "remaining_active": self._count_active_tasks(notifier, conversation_id)
            }
            
            return ToolResult(
                success=True,
                message="\n".join(output_lines),
                content=result_content
            )
            
        except Exception as e:
            logger.error(f"Cleanup action failed: {str(e)}")
            return ToolResult(
                success=False,
                message=f"清理后台任务失败: {str(e)}",
                content={"action": "cleanup", "error": str(e), "cleaned_count": 0}
            )
    
    def _handle_kill_action(self, conversation_id: str) -> ToolResult:
        """处理终止任务的操作"""
        try:
            # 验证参数
            if not self.tool.task_id and not self.tool.pid and not self.tool.pids and not self.tool.process_uniq_id:
                return ToolResult(
                    success=False,
                    message="kill 操作必须提供 task_id、pid、pids 或 process_uniq_id 参数",
                    content={
                        "action": "kill",
                        "target_pids": [],
                        "verified_pids": [],
                        "kill_results": [],
                        "success_count": 0,
                        "failed_count": 0,
                        "force_mode": self.tool.force,
                        "kill_children": self.tool.kill_children,
                        "error": "missing_required_params"
                    }
                )
            
            # 收集要终止的进程ID
            target_pids = []
            
            if self.tool.pids:
                # 批量操作模式
                target_pids = list(self.tool.pids)
            elif self.tool.pid:
                # 单个PID模式
                target_pids = [self.tool.pid]
            elif self.tool.task_id:
                # 通过task_id查找PID
                found_pids = self._find_pids_by_task_id(conversation_id, self.tool.task_id)
                if not found_pids:
                    return ToolResult(
                        success=False,
                        message=f"未找到 task_id={self.tool.task_id} 对应的进程",
                        content={
                            "action": "kill",
                            "target_pids": [],
                            "verified_pids": [],
                            "kill_results": [],
                            "success_count": 0,
                            "failed_count": 0,
                            "force_mode": self.tool.force,
                            "kill_children": self.tool.kill_children,
                            "error": "task_not_found"
                        }
                    )
                target_pids = found_pids
            elif self.tool.process_uniq_id:
                # 通过 process_uniq_id 查找 PID
                found_pids = self._find_pids_by_process_uniq_id(conversation_id, self.tool.process_uniq_id)
                if not found_pids:
                    return ToolResult(
                        success=False,
                        message=f"未找到 process_uniq_id={self.tool.process_uniq_id} 对应的进程",
                        content={
                            "action": "kill",
                            "target_pids": [],
                            "verified_pids": [],
                            "kill_results": [],
                            "success_count": 0,
                            "failed_count": 0,
                            "force_mode": self.tool.force,
                            "kill_children": self.tool.kill_children,
                            "error": "process_not_found"
                        }
                    )
                target_pids = found_pids
            
            # 验证进程是否属于当前会话
            verified_pids = []
            for pid in target_pids:
                if self._verify_process_ownership(conversation_id, pid):
                    verified_pids.append(pid)
                else:
                    logger.warning(f"PID {pid} 不属于当前会话 {conversation_id}，跳过")
            
            if not verified_pids:
                return ToolResult(
                    success=False,
                    message="没有找到属于当前会话的有效进程",
                    content={
                        "action": "kill",
                        "target_pids": target_pids,
                        "verified_pids": [],
                        "kill_results": [],
                        "success_count": 0,
                        "failed_count": 0,
                        "force_mode": self.tool.force,
                        "kill_children": self.tool.kill_children,
                        "error": "no_valid_processes"
                    }
                )
            
            # 执行终止操作
            kill_results = []
            success_count = 0
            failed_count = 0
            
            for pid in verified_pids:
                result = self._kill_process(pid, self.tool.force, self.tool.kill_children)
                kill_results.append(result)
                
                if result["success"]:
                    success_count += 1
                else:
                    failed_count += 1
            
            # 构建输出消息
            output_lines = ["终止后台任务:"]
            
            for result in kill_results:
                status_icon = "✅" if result["success"] else "❌"
                task_info = f"任务 {result.get('task_id', 'N/A')} (PID: {result['pid']})"
                
                if result["success"]:
                    output_lines.append(f"{status_icon} {task_info} 已成功终止")
                else:
                    output_lines.append(f"{status_icon} {task_info} 终止失败: {result['error']}")
            
            output_lines.append("")
            output_lines.append(f"总计: {success_count} 个任务成功终止, {failed_count} 个任务失败")
            
            # 构建结果内容
            result_content = {
                "action": "kill",
                "target_pids": target_pids,
                "verified_pids": verified_pids,
                "kill_results": kill_results,
                "success_count": success_count,
                "failed_count": failed_count,
                "force_mode": self.tool.force,
                "kill_children": self.tool.kill_children
            }
            
            overall_success = success_count > 0
            
            return ToolResult(
                success=overall_success,
                message="\n".join(output_lines),
                content=result_content
            )
            
        except Exception as e:
            logger.error(f"Kill action failed: {str(e)}")
            return ToolResult(
                success=False,
                message=f"终止后台任务失败: {str(e)}"
            )
    
    # 以下是辅助方法，从原来的各个解析器中整合而来
    
    def _format_duration(self, seconds: float) -> str:
        """格式化持续时间为人类可读格式"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def _find_tasks_by_task_id(self, notifier, conversation_id: str, task_id: str) -> List[Dict[str, Any]]:
        """通过 task_id 查找任务"""
        tasks = []
        
        with notifier._lock:
            registrations = dict(notifier._registrations)
            pending_messages = dict(notifier._pending_messages)
        
        # 在注册的任务中查找
        for key, reg in registrations.items():
            if reg.conversation_id == conversation_id and reg.task_id == task_id:
                pid, start_time = key
                tasks.append({
                    "task_id": reg.task_id,
                    "pid": pid,
                    "tool_name": reg.tool_name,
                    "command": reg.command,
                    "cwd": reg.cwd,
                    "agent_name": reg.agent_name,
                    "task": reg.task,
                    "start_time": reg.start_time
                })
        
        # 在待处理消息中查找
        if conversation_id in pending_messages:
            for msg in pending_messages[conversation_id]:
                if msg.task_id == task_id:
                    tasks.append({
                        "task_id": msg.task_id,
                        "pid": msg.pid,
                        "tool_name": msg.tool_name,
                        "command": msg.command,
                        "cwd": msg.cwd,
                        "agent_name": msg.agent_name,
                        "task": msg.task,
                        "start_time": msg.completed_at - (msg.duration_sec or 0),
                        "completed": True
                    })
        
        return tasks
    
    def _find_tasks_by_process_uniq_id(self, notifier, conversation_id: str, process_uniq_id: str) -> List[Dict[str, Any]]:
        """通过 process_uniq_id 查找任务"""
        tasks = []
        bg_processes = get_background_processes()
        if not bg_processes:
            bg_processes = {}
        
        # 在后台进程中查找匹配的 process_uniq_id
        for pid, process_info in bg_processes.items():
            if process_info.get("process_uniq_id") == process_uniq_id:
                # 找到匹配的进程，现在查找对应的任务信息
                with notifier._lock:
                    registrations = dict(notifier._registrations)
                    pending_messages = dict(notifier._pending_messages)
                
                # 在注册的任务中查找
                for key, reg in registrations.items():
                    reg_pid, start_time = key
                    if reg.conversation_id == conversation_id and reg_pid == pid:
                        tasks.append({
                            "task_id": reg.task_id,
                            "pid": reg_pid,
                            "process_uniq_id": process_uniq_id,
                            "tool_name": reg.tool_name,
                            "command": reg.command,
                            "cwd": reg.cwd,
                            "agent_name": reg.agent_name,
                            "task": reg.task,
                            "start_time": reg.start_time
                        })
                
                # 在待处理消息中查找
                if conversation_id in pending_messages:
                    for msg in pending_messages[conversation_id]:
                        if msg.pid == pid:
                            tasks.append({
                                "task_id": msg.task_id,
                                "pid": msg.pid,
                                "process_uniq_id": process_uniq_id,
                                "tool_name": msg.tool_name,
                                "command": msg.command,
                                "cwd": msg.cwd,
                                "agent_name": msg.agent_name,
                                "task": msg.task,
                                "start_time": msg.completed_at - (msg.duration_sec or 0),
                                "completed": True
                            })
                
                # 如果没有找到注册任务，创建一个默认任务
                if not tasks:
                    tasks.append({
                        "task_id": f"bg_{pid}",  # 生成一个默认的 task_id
                        "pid": pid,
                        "process_uniq_id": process_uniq_id,
                        "tool_name": "background_command",
                        "command": process_info.get("command", "Unknown"),
                        "cwd": process_info.get("cwd"),
                        "agent_name": "system",
                        "task": process_info.get("command", "Unknown"),
                        "start_time": process_info.get("start_time")
                    })
                
                break
        
        return tasks
    
    def _find_pids_by_process_uniq_id(self, conversation_id: str, process_uniq_id: str) -> List[int]:
        """通过 process_uniq_id 查找对应的 PID"""
        pids = []
        bg_processes = get_background_processes()
        if not bg_processes:
            return pids
        
        # 在后台进程中查找匹配的 process_uniq_id
        for pid, process_info in bg_processes.items():
            if process_info.get("process_uniq_id") == process_uniq_id:
                # 验证该进程属于当前会话
                if self._verify_process_ownership(conversation_id, pid):
                    pids.append(pid)
                break
        
        return pids
    
    def _find_tasks_by_pid(self, notifier, conversation_id: str, pid: int) -> List[Dict[str, Any]]:
        """通过 pid 查找任务"""
        tasks = []
        
        with notifier._lock:
            registrations = dict(notifier._registrations)
            pending_messages = dict(notifier._pending_messages)
        
        # 在注册的任务中查找
        for key, reg in registrations.items():
            reg_pid, start_time = key
            if reg.conversation_id == conversation_id and reg_pid == pid:
                tasks.append({
                    "task_id": reg.task_id,
                    "pid": reg_pid,
                    "tool_name": reg.tool_name,
                    "command": reg.command,
                    "cwd": reg.cwd,
                    "agent_name": reg.agent_name,
                    "task": reg.task,
                    "start_time": reg.start_time
                })
        
        # 在待处理消息中查找
        if conversation_id in pending_messages:
            for msg in pending_messages[conversation_id]:
                if msg.pid == pid:
                    tasks.append({
                        "task_id": msg.task_id,
                        "pid": msg.pid,
                        "tool_name": msg.tool_name,
                        "command": msg.command,
                        "cwd": msg.cwd,
                        "agent_name": msg.agent_name,
                        "task": msg.task,
                        "start_time": msg.completed_at - (msg.duration_sec or 0),
                        "completed": True
                    })
        
        # 如果在注册中没有找到，尝试从 bg_processes 中查找
        if not tasks:
            bg_processes = get_background_processes()
            if pid in bg_processes:
                process_info = bg_processes[pid]
                tasks.append({
                    "task_id": f"bg_{pid}",  # 生成一个默认的 task_id
                    "pid": pid,
                    "tool_name": "background_command",
                    "command": process_info.get("command", "Unknown"),
                    "cwd": process_info.get("cwd"),
                    "agent_name": "system",
                    "task": process_info.get("command", "Unknown"),
                    "start_time": process_info.get("start_time"),
                    "process_uniq_id": process_info.get("process_uniq_id")
                })
        
        return tasks
    
    def _get_process_output(self, process_info: Dict[str, Any], pid: int) -> Tuple[Optional[str], Optional[str]]:
        """从文件系统中获取进程的 stdout 和 stderr 输出，使用通知器的实现"""
        try:
            # 获取后台进程通知器实例
            notifier = get_background_process_notifier()
            
            # 使用通知器的方法来读取输出
            return notifier._read_process_output_tails(process_info)
                
        except Exception as e:
            logger.error(f"Error getting process output for PID {pid}: {str(e)}")
            return None, None
    
    def _format_output_lines(self, content: str, max_lines: int, output_type: str) -> List[str]:
        """格式化输出内容为指定行数"""
        if not content:
            return []
        
        lines = content.splitlines()
        
        # 取最后 max_lines 行
        if len(lines) > max_lines:
            lines = lines[-max_lines:]
            truncated = True
        else:
            truncated = False
        
        result = [f"=== {output_type} (最后 {len(lines)} 行) ==="]
        
        if truncated:
            result.append(f"... (已截断，仅显示最后 {max_lines} 行)")
        
        result.extend(lines)
        
        return result
    
    def _should_cleanup_task(self, registration, process_info: Optional[Dict], current_time: float) -> bool:
        """判断注册任务是否应该被清理"""
        # 状态过滤
        if self.tool.status_filter:
            # 对于已报告的任务，假设它们已完成
            if self.tool.status_filter not in ["completed"]:
                return False
        
        # 时间过滤
        if self.tool.older_than_minutes:
            task_age_minutes = (current_time - registration.start_time) / 60
            if task_age_minutes < self.tool.older_than_minutes:
                return False
        
        return True
    
    def _should_cleanup_message(self, message, current_time: float) -> bool:
        """判断待处理消息是否应该被清理"""
        # 状态过滤
        if self.tool.status_filter:
            if message.status != self.tool.status_filter:
                return False
        
        # 时间过滤
        if self.tool.older_than_minutes:
            message_age_minutes = (current_time - message.completed_at) / 60
            if message_age_minutes < self.tool.older_than_minutes:
                return False
        
        return True
    
    def _count_active_tasks(self, notifier, conversation_id: str) -> int:
        """统计当前活跃的任务数量"""
        count = 0
        with notifier._lock:
            for reg in notifier._registrations.values():
                if reg.conversation_id == conversation_id:
                    count += 1
        return count
    
    def _estimate_task_memory_usage(self, task: Dict[str, Any]) -> int:
        """估算任务占用的内存大小（字节）"""
        # 简单估算：基于任务信息的字符串长度
        base_size = 1024  # 基础对象开销
        
        # 字符串字段的估算
        string_fields = ["task_id", "tool_name", "status"]
        for field in string_fields:
            if field in task and task[field]:
                base_size += len(str(task[field])) * 2  # Unicode 字符
        
        return base_size
    
    def _estimate_message_memory_usage(self, message) -> int:
        """估算消息对象占用的内存大小（字节）"""
        base_size = 2048  # 基础对象开销
        
        # 估算字符串字段
        string_fields = ["task_id", "tool_name", "command", "cwd", "agent_name", "task", "output_tail", "error_tail"]
        for field in string_fields:
            value = getattr(message, field, None)
            if value:
                base_size += len(str(value)) * 2
        
        return base_size
    
    def _format_memory_size(self, bytes_size: int) -> str:
        """格式化内存大小为人类可读格式"""
        if bytes_size < 1024:
            return f"{bytes_size}B"
        elif bytes_size < 1024 * 1024:
            return f"{bytes_size / 1024:.1f}KB"
        else:
            return f"{bytes_size / (1024 * 1024):.1f}MB"
    
    def _find_pids_by_task_id(self, conversation_id: str, task_id: str) -> List[int]:
        """通过 task_id 查找对应的 PID"""
        pids = []
        notifier = get_background_process_notifier()
        
        with notifier._lock:
            registrations = dict(notifier._registrations)
            pending_messages = dict(notifier._pending_messages)
        
        # 在注册的任务中查找
        for key, reg in registrations.items():
            if reg.conversation_id == conversation_id and reg.task_id == task_id:
                pid, start_time = key
                pids.append(pid)
        
        # 在待处理消息中查找（已完成的任务）
        if conversation_id in pending_messages:
            for msg in pending_messages[conversation_id]:
                if msg.task_id == task_id:
                    pids.append(msg.pid)
        
        return pids
    
    def _verify_process_ownership(self, conversation_id: str, pid: int) -> bool:
        """验证进程是否属于当前会话"""
        notifier = get_background_process_notifier()
        
        with notifier._lock:
            registrations = dict(notifier._registrations)
            pending_messages = dict(notifier._pending_messages)
        
        # 检查注册的任务
        for key, reg in registrations.items():
            reg_pid, start_time = key
            if reg.conversation_id == conversation_id and reg_pid == pid:
                return True
        
        # 检查待处理消息
        if conversation_id in pending_messages:
            for msg in pending_messages[conversation_id]:
                if msg.pid == pid:
                    return True
        
        return False
    
    def _kill_process(self, pid: int, force: bool, kill_children: bool) -> Dict[str, Any]:
        """终止指定的进程"""
        result = {
            "pid": pid,
            "success": False,
            "error": None,
            "task_id": None,
            "children_killed": []
        }
        
        try:
            # 获取任务信息
            task_id = self._get_task_id_by_pid(pid)
            result["task_id"] = task_id
            
            # 检查进程是否存在
            if not psutil.pid_exists(pid):
                result["error"] = "进程不存在"
                return result
            
            try:
                process = psutil.Process(pid)
            except psutil.NoSuchProcess:
                result["error"] = "进程不存在"
                return result
            
            # 获取子进程（如果需要）
            children = []
            if kill_children:
                try:
                    children = process.children(recursive=True)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 选择终止信号
            if force:
                sig = signal.SIGKILL  # 强制终止
            else:
                sig = signal.SIGTERM  # 优雅终止
            
            # 终止子进程
            children_killed = []
            for child in children:
                try:
                    child.send_signal(sig)
                    children_killed.append(child.pid)
                    logger.info(f"Sent signal {sig} to child process {child.pid}")
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    logger.warning(f"Failed to kill child process {child.pid}: {str(e)}")
            
            result["children_killed"] = children_killed
            
            # 终止主进程
            try:
                process.send_signal(sig)
                logger.info(f"Sent signal {sig} to process {pid}")
                
                # 等待进程终止（最多等待5秒）
                if not force:
                    try:
                        process.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        # 如果优雅终止超时，使用强制终止
                        logger.warning(f"Process {pid} did not terminate gracefully, forcing kill")
                        process.send_signal(signal.SIGKILL)
                        process.wait(timeout=2)
                
                result["success"] = True
                
            except psutil.NoSuchProcess:
                # 进程已经不存在，认为成功
                result["success"] = True
            except psutil.AccessDenied:
                result["error"] = "权限不足，无法终止进程"
            except Exception as e:
                result["error"] = f"终止进程时发生错误: {str(e)}"
            
        except Exception as e:
            result["error"] = f"处理进程时发生错误: {str(e)}"
            logger.error(f"Error killing process {pid}: {str(e)}")
        
        return result
    
    def _get_task_id_by_pid(self, pid: int) -> Optional[str]:
        """通过 PID 获取 task_id"""
        notifier = get_background_process_notifier()
        
        with notifier._lock:
            registrations = dict(notifier._registrations)
            pending_messages = dict(notifier._pending_messages)
        
        # 在注册的任务中查找
        for key, reg in registrations.items():
            reg_pid, start_time = key
            if reg_pid == pid:
                return reg.task_id
        
        # 在待处理消息中查找
        for conv_messages in pending_messages.values():
            for msg in conv_messages:
                if msg.pid == pid:
                    return msg.task_id
        
        return None

    def _classify_tool_name(self, tool_name: Optional[str]) -> str:
        """将不同风格的工具名称归一化为类别: 'command' 或 'subagent'

        兼容的名称示例:
        - 命令类: 'ExecuteCommandTool'
        - 子代理类:'RunNamedSubagentsTool'
        """
        if not tool_name:
            return 'command'
        name = str(tool_name).strip().lower()
        # 子代理优先匹配，避免 "subagent" 与 "command" 同时出现时误判
        if 'subagent' in name or name in {'run_named_subagents', 'runnamedsubagentstool'}:
            return 'subagent'
        if (
            name in {'execute_command', 'background_command', 'command'}
            or 'executecommand' in name
            or ('command' in name and 'subagent' not in name)
        ):
            return 'command'
        # 未知的名称默认按命令类处理
        return 'command'




