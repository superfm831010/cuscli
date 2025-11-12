from typing import List, Dict, Any, Union, Optional
import json
import re
import copy
import byzerllm
from autocoder.common.printer import Printer
from autocoder.common.tokens import count_string_tokens
from loguru import logger
from autocoder.common import AutoCoderArgs
from autocoder.common.autocoderargs_parser import AutoCoderArgsParser
from autocoder.common.save_formatted_log import save_formatted_log
from autocoder.common.wrap_llm_hint.utils import merge_with_last_user_message
from autocoder.common.conversations.get_conversation_manager import get_conversation_manager
from .tool_content_detector import ToolContentDetector
from .conversation_message_ids_api import get_conversation_message_ids_api
from .conversation_message_ids_pruner import ConversationMessageIdsPruner


class AgenticConversationPruner:
    """
    Specialized conversation pruner for agentic conversations that cleans up tool outputs.

    This pruner specifically targets tool result messages (role='user', content contains '<tool_result>')
    and replaces their content with a placeholder message to reduce token usage while maintaining
    conversation flow.
    """

    def __init__(self, args: AutoCoderArgs, llm: Union[byzerllm.ByzerLLM, byzerllm.SimpleByzerLLM, None], conversation_id: Optional[str] = None):
        if conversation_id is None:
            raise ValueError("conversation_id is required in AgenticConversationPruner")
            
        self.args = args
        self.llm = llm
        self.conversation_id = conversation_id
        self.printer = Printer()
        self.replacement_message = "This message has been cleared. If you still want to get this information, you can call the tool again to retrieve it."

        # Initialize AutoCoderArgs parser for flexible parameter parsing
        self.args_parser = AutoCoderArgsParser()

        # Initialize tool content detector
        self.tool_content_detector = ToolContentDetector(
            replacement_message="Content cleared to save tokens"
        )

        # Initialize message IDs-based pruning components
        self.message_ids_api = get_conversation_message_ids_api()
        self.message_ids_pruner = ConversationMessageIdsPruner()

        # Track pruning statistics
        self.pruning_stats = {
            "range_pruning_applied": False,
            "range_pruning_success": False,
            "original_length": 0,
            "after_range_pruning": 0,
            "after_tool_cleanup": 0,
            "total_compression_ratio": 1.0
        }

    def _get_current_conversation_id(self) -> str:
        """
        Get the current conversation ID from the constructor parameter.

        Returns:
            Current conversation ID (guaranteed to be not None)
        """
        return self.conversation_id

    def _get_parsed_safe_zone_tokens(self) -> int:
        """
        解析 conversation_prune_safe_zone_tokens 参数，支持多种格式

        Returns:
            解析后的 token 数量
        """
        # 添加调试信息
        raw_value = self.args.conversation_prune_safe_zone_tokens
        code_model = self.args.code_model or self.args.model
                        
        result = self.args_parser.parse_conversation_prune_safe_zone_tokens(
            raw_value,
            code_model
        )
                        
        # 防护逻辑：如果结果为 0，使用默认值
        if result == 0:
            default_value = 50 * 1024
            print(f"[WARNING] conversation_prune_safe_zone_tokens 为 0，使用默认值: {default_value}")
            return default_value
        
        return result

    def prune_conversations(self, conversations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prune conversations by applying range-based pruning first, then cleaning up tool outputs and tool call content.

        Args:
            conversations: Original conversation list            

        Returns:
            Pruned conversation list
        """
        safe_zone_tokens = self._get_parsed_safe_zone_tokens()
        # print(f"safe_zone_tokens: {safe_zone_tokens}")

        # 保存原始conversations的深拷贝，用于最终对比分析
        # original_conversations = copy.deepcopy(conversations)
        original_length = len(conversations)

        # Initialize pruning statistics
        self.pruning_stats["original_length"] = original_length

        current_tokens = count_string_tokens(
            json.dumps(conversations, ensure_ascii=False))

        if current_tokens <= safe_zone_tokens:
            # Update stats for no pruning needed
            self.pruning_stats.update({
                "after_range_pruning": original_length,
                "after_tool_cleanup": original_length,
                "total_compression_ratio": 1.0
            })
            return conversations

        # Step 1: Apply message ids pruning if conversation_id is provided
        processed_conversations = self._apply_message_ids_pruning(
            conversations)
        logger.info(
            f"After Message IDs pruning: {len(conversations)} -> {len(processed_conversations)} messages")

        # Check if we're within safe zone after range pruning
        current_tokens = count_string_tokens(json.dumps(
            processed_conversations, ensure_ascii=False))

        # Step 2: Apply tool cleanup if still needed
        if current_tokens > safe_zone_tokens:
            config = {"safe_zone_tokens": safe_zone_tokens}
            processed_conversations = self._unified_tool_cleanup_prune(
                processed_conversations, config)

        # Update final statistics
        final_length = len(processed_conversations)
        self.pruning_stats["after_tool_cleanup"] = final_length
        self.pruning_stats["total_compression_ratio"] = final_length / \
            original_length if original_length > 0 else 1.0

        # Log overall pruning results
        logger.info(f"Complete pruning: {original_length} -> {final_length} messages "
                    f"(total compression: {self.pruning_stats['total_compression_ratio']:.2%})")

        # if the processed_conversations is still too long, we should add a user message to ask the LLM to clean up the conversation
        final_tokens = count_string_tokens(json.dumps(
            processed_conversations, ensure_ascii=False))
        if final_tokens > safe_zone_tokens:
            cleanup_message = "The conversation is still too long, please use conversation_message_ids_write tool to save the message ids to be deleted."

            # Use standardized hint merging from wrap_llm_hint module
            processed_conversations = merge_with_last_user_message(
                processed_conversations, cleanup_message)
        # 执行裁剪前后对比分析并记录到日志
        # self._compare_and_log_conversations(original_conversations, processed_conversations)

        save_formatted_log(self.args.source_dir, json.dumps(processed_conversations, ensure_ascii=False),
                           "agentic_pruned_conversation", conversation_id=self._get_current_conversation_id())

        return processed_conversations

    def _apply_message_ids_pruning(self, conversations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply message IDs-based pruning if conversation_id is provided and message IDs configuration exists.

        Args:
            conversations: Original conversation list

        Returns:
            Conversations after message IDs pruning (or original if no message IDs config)
        """
        # Check if we have conversation_id and message IDs configuration
        conversation_id = self._get_current_conversation_id()
        if not conversation_id:
            logger.debug(
                "No conversation_id provided, skipping message IDs pruning")
            self.pruning_stats["after_range_pruning"] = len(conversations)
            return conversations

        # Get message IDs configuration for this conversation
        conversation_message_ids = self.message_ids_api.get_conversation_message_ids(
            conversation_id)
        if not conversation_message_ids:
            logger.debug(
                f"No message IDs configuration found for conversation {conversation_id}, skipping message IDs pruning")
            self.pruning_stats["after_range_pruning"] = len(conversations)
            return conversations

        # Apply message IDs pruning
        logger.info(
            f"Applying message IDs pruning for conversation {conversation_id}")
        self.pruning_stats["range_pruning_applied"] = True

        try:
            pruning_result = self.message_ids_pruner.prune_conversations(
                conversations, conversation_message_ids)
            logger.info(f"Message IDs: {pruning_result}")

            if pruning_result.success:
                self.pruning_stats["range_pruning_success"] = True
                self.pruning_stats["after_range_pruning"] = pruning_result.pruned_length

                # Log message IDs pruning results
                logger.info(f"Message IDs pruning completed: {pruning_result.original_length} -> {pruning_result.pruned_length} messages "
                            f"(message IDs compression: {pruning_result.compression_ratio:.2%})")

                # Log warnings if any
                if pruning_result.warnings:
                    for warning in pruning_result.warnings:
                        logger.warning(f"Message IDs pruning: {warning}")

                return pruning_result.pruned_conversations
            else:
                # Message IDs pruning failed, log error and continue with original conversations
                logger.error(
                    f"Message IDs pruning failed: {pruning_result.error_message}")
                self.pruning_stats["after_range_pruning"] = len(conversations)
                return conversations

        except Exception as e:
            logger.error(
                f"Message IDs pruning failed with exception: {str(e)}")
            self.pruning_stats["after_range_pruning"] = len(conversations)
            return conversations

    def _unified_tool_cleanup_prune(self, conversations: List[Dict[str, Any]],
                                    config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Clean up both tool output results and tool call content in a unified process.

        This method:
        1. Identifies both tool result messages (role='user' with '<tool_result' in content)
           and assistant messages containing tool calls with large content
        2. Processes all cleanable messages in order, prioritizing tool results first
        3. Stops when token count is within safe zone OR when less than 6 unpruned messages remain
        """
        safe_zone_tokens = config.get("safe_zone_tokens", 80 * 1024)
        # 使用深拷贝避免修改原始数据
        processed_conversations = copy.deepcopy(conversations)

        # 预先计算初始 token 数量，避免在循环中引用未定义的变量
        current_tokens = count_string_tokens(json.dumps(
            processed_conversations, ensure_ascii=False))

        # Find all cleanable message indices with their types
        cleanable_messages = []

        # Find both tool result messages and tool call messages in one loop
        for i, conv in enumerate(processed_conversations):
            content = conv.get("content", "")
            role = conv.get("role")

            if isinstance(content, str):
                # Check for tool result messages (user role)
                if (role == "user" and self._is_tool_result_message(content)):
                    cleanable_messages.append(
                        {"index": i, "type": "tool_result"})
                # Check for assistant messages with tool calls
                elif (role == "assistant" and self.tool_content_detector.is_tool_call_content(content)):
                    cleanable_messages.append(
                        {"index": i, "type": "tool_call"})

        # Sort by index to process in order, but prioritize tool_result messages
        cleanable_messages.sort(key=lambda x: (
            x["index"], x["type"] != "tool_result"))

        logger.info(f"Found {len([m for m in cleanable_messages if m['type'] == 'tool_result'])} tool result messages "
                    f"and {len([m for m in cleanable_messages if m['type'] == 'tool_call'])} tool call messages to potentially clean")

        # Track cleaned messages
        cleaned_count = 0

        # Clean messages one by one
        for i, message_info in enumerate(cleanable_messages):
            # 更新当前 token 数量
            current_tokens = count_string_tokens(json.dumps(
                processed_conversations, ensure_ascii=False))

            # 检查停止条件
            # 1. Token数已经在安全区域内
            if current_tokens <= safe_zone_tokens:
                logger.info(
                    f"Token count ({current_tokens}) is within safe zone ({safe_zone_tokens}), stopping cleanup")
                break

            # 2. 剩余未裁剪的对话少于6段
            remaining_unpruned = len(
                cleanable_messages) - (i + 1)  # i+1 因为i是从0开始的索引
            if remaining_unpruned < 6:
                logger.info(
                    f"Less than 6 unpruned messages remaining ({remaining_unpruned}), stopping cleanup")
                break

            msg_index = message_info["index"]
            msg_type = message_info["type"]
            original_content = processed_conversations[msg_index]["content"]

            if msg_type == "tool_result":
                # Handle tool result cleanup
                tool_name = self._extract_tool_name(original_content)
                replacement_content = self._generate_replacement_message(
                    tool_name)
                processed_conversations[msg_index]["content"] = replacement_content
                cleaned_count += 1

                logger.info(f"Cleaned tool result at index {msg_index} (tool: {tool_name}), "
                            f"reduced from {len(original_content)} to {len(replacement_content)} characters")

            elif msg_type == "tool_call":
                # Handle tool call content cleanup
                tool_info = self.tool_content_detector.detect_tool_call(
                    original_content)

                if tool_info:
                    new_content, replaced = self.tool_content_detector.replace_tool_content(
                        original_content, max_content_length=500
                    )

                    if replaced:
                        processed_conversations[msg_index]["content"] = new_content
                        cleaned_count += 1
                        logger.info(f"Cleaned tool call content at index {msg_index} (tool: {tool_info['tool_name']}), "
                                    f"reduced from {len(original_content)} to {len(new_content)} characters")

        final_tokens = count_string_tokens(json.dumps(
            processed_conversations, ensure_ascii=False))
        initial_tokens = count_string_tokens(
            json.dumps(conversations, ensure_ascii=False))
        logger.info(
            f"Unified tool cleanup completed. Cleaned {cleaned_count} messages. Token count: {initial_tokens} -> {final_tokens}")

        return processed_conversations

    def _is_tool_result_message(self, content: str) -> bool:
        """
        Check if a message content contains tool result XML.

        Args:
            content: Message content to check

        Returns:
            True if content contains tool result format
        """
        if content is None:
            return False
        return "<tool_result" in content and "tool_name=" in content

    def _extract_tool_name(self, content: str) -> str:
        """
        Extract tool name from tool result XML content.

        Args:
            content: Tool result XML content

        Returns:
            Tool name or 'unknown' if not found
        """
        # Pattern to match: <tool_result tool_name='...' or <tool_result tool_name="..."
        pattern = r"<tool_result[^>]*tool_name=['\"]([^'\"]*)['\"]"
        match = re.search(pattern, content)

        if match:
            return match.group(1)
        return "unknown"

    def _generate_replacement_message(self, tool_name: str) -> str:
        """
        Generate a replacement message for a cleaned tool result.

        Args:
            tool_name: Name of the tool that was called

        Returns:
            Replacement message string
        """
        if tool_name and tool_name != "unknown":
            return (f"<tool_result tool_name='{tool_name}' success='true'>"
                    f"<message>Content cleared to save tokens</message>"
                    f"<content>{self.replacement_message}</content>"
                    f"</tool_result>")
        else:
            return f"<tool_result success='true'><message>[Content cleared to save tokens, you can call the tool again to get the tool result.]</message><content>{self.replacement_message}</content></tool_result>"

    def get_cleanup_statistics(self, original_conversations: List[Dict[str, Any]],
                               pruned_conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about the cleanup process.

        Args:
            original_conversations: Original conversation list
            pruned_conversations: Pruned conversation list

        Returns:
            Dictionary with cleanup statistics
        """
        original_tokens = count_string_tokens(
            json.dumps(original_conversations, ensure_ascii=False))
        pruned_tokens = count_string_tokens(
            json.dumps(pruned_conversations, ensure_ascii=False))

        # Count cleaned tool results
        tool_results_cleaned = 0
        tool_calls_cleaned = 0

        for orig, pruned in zip(original_conversations, pruned_conversations):
            if orig.get("content") != pruned.get("content"):
                # Check if it's a tool result message (user role)
                if (orig.get("role") == "user" and
                        self._is_tool_result_message(orig.get("content", ""))):
                    tool_results_cleaned += 1

                # Check if it's a tool call message (assistant role)
                elif (orig.get("role") == "assistant" and
                      self.tool_content_detector.is_tool_call_content(orig.get("content", ""))):
                    tool_calls_cleaned += 1

        return {
            "original_tokens": original_tokens,
            "pruned_tokens": pruned_tokens,
            "tokens_saved": original_tokens - pruned_tokens,
            "compression_ratio": pruned_tokens / original_tokens if original_tokens > 0 else 1.0,
            "tool_results_cleaned": tool_results_cleaned,
            "tool_calls_cleaned": tool_calls_cleaned,
            "total_messages": len(original_conversations)
        }

    def get_pruning_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive pruning statistics including both range and tool cleanup.

        Returns:
            Dictionary with complete pruning statistics
        """
        return {
            "range_pruning": {
                "applied": self.pruning_stats["range_pruning_applied"],
                "success": self.pruning_stats["range_pruning_success"],
                "conversation_id": self._get_current_conversation_id()
            },
            "message_counts": {
                "original": self.pruning_stats["original_length"],
                "after_range_pruning": self.pruning_stats["after_range_pruning"],
                "after_tool_cleanup": self.pruning_stats["after_tool_cleanup"]
            },
            "compression": {
                "range_pruning_ratio": (
                    self.pruning_stats["after_range_pruning"] /
                    self.pruning_stats["original_length"]
                    if self.pruning_stats["original_length"] > 0 else 1.0
                ),
                "tool_cleanup_ratio": (
                    self.pruning_stats["after_tool_cleanup"] /
                    self.pruning_stats["after_range_pruning"]
                    if self.pruning_stats["after_range_pruning"] > 0 else 1.0
                ),
                "total_compression_ratio": self.pruning_stats["total_compression_ratio"]
            },
            "messages_removed": {
                "by_range_pruning": (
                    self.pruning_stats["original_length"] -
                    self.pruning_stats["after_range_pruning"]
                ),
                "by_tool_cleanup": (
                    self.pruning_stats["after_range_pruning"] -
                    self.pruning_stats["after_tool_cleanup"]
                ),
                "total_removed": (
                    self.pruning_stats["original_length"] -
                    self.pruning_stats["after_tool_cleanup"]
                )
            }
        }

    def _compare_and_log_conversations(self, original_conversations: List[Dict[str, Any]],
                                       pruned_conversations: List[Dict[str, Any]]) -> None:
        """
        独立的方法：对比裁剪前后的conversations，生成详细的对比报告并记录到日志中。

        Args:
            original_conversations: 裁剪前的对话列表
            pruned_conversations: 裁剪后的对话列表
        """
        try:
            # 生成对比分析报告
            comparison_report = self._generate_comparison_report(
                original_conversations, pruned_conversations)

            # 记录详细的对比日志
            logger.info("=== 对话裁剪前后对比分析 ===")
            logger.info(
                f"原始对话数量: {comparison_report['message_counts']['original']}")
            logger.info(
                f"裁剪后对话数量: {comparison_report['message_counts']['final']}")
            logger.info(
                f"删除的对话数量: {comparison_report['message_counts']['removed']}")
            logger.info(
                f"消息压缩比: {comparison_report['compression']['message_compression_ratio']:.2%}")
            logger.info(
                f"Token压缩比: {comparison_report['compression']['token_compression_ratio']:.2%}")
            logger.info(f"Token节省数量: {comparison_report['tokens']['saved']:,}")

            if comparison_report['changes']['tool_results_modified'] > 0:
                logger.info(
                    f"工具结果消息清理数量: {comparison_report['changes']['tool_results_modified']}")

            if comparison_report['changes']['tool_calls_modified'] > 0:
                logger.info(
                    f"工具调用内容清理数量: {comparison_report['changes']['tool_calls_modified']}")

            if comparison_report['changes']['messages_removed_by_ids'] > 0:
                logger.info(
                    f"基于消息ID删除的消息数量: {comparison_report['changes']['messages_removed_by_ids']}")

            # 保存详细的对比报告到文件日志
            save_formatted_log(
                self.args.source_dir,
                json.dumps(comparison_report, ensure_ascii=False, indent=2),
                "conversation_comparison_report",
                conversation_id=self._get_current_conversation_id()
            )

        except Exception as e:
            logger.error(f"生成对话对比报告时出错: {str(e)}")
            logger.exception(e)

    def _generate_comparison_report(self, original_conversations: List[Dict[str, Any]],
                                    pruned_conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成详细的对比分析报告。

        Args:
            original_conversations: 裁剪前的对话列表
            pruned_conversations: 裁剪后的对话列表

        Returns:
            包含详细对比信息的字典
        """
        # 基础统计信息
        original_count = len(original_conversations)
        pruned_count = len(pruned_conversations)
        removed_count = original_count - pruned_count

        # Token统计
        original_tokens = count_string_tokens(
            json.dumps(original_conversations, ensure_ascii=False))
        pruned_tokens = count_string_tokens(
            json.dumps(pruned_conversations, ensure_ascii=False))
        tokens_saved = original_tokens - pruned_tokens

        # 分析变化详情
        changes_analysis = self._analyze_conversation_changes(
            original_conversations, pruned_conversations)

        # 分析消息类型分布
        original_distribution = self._analyze_message_distribution(
            original_conversations)
        pruned_distribution = self._analyze_message_distribution(
            pruned_conversations)

        # 生成完整的对比报告
        report = {
            "timestamp": str(__import__("datetime").datetime.now()),
            "conversation_id": self._get_current_conversation_id(),
            "pruning_strategy": {
                "range_pruning_applied": self.pruning_stats["range_pruning_applied"],
                "tool_cleanup_applied": True,
                "safe_zone_tokens": self._get_parsed_safe_zone_tokens()
            },
            "message_counts": {
                "original": original_count,
                "final": pruned_count,
                "removed": removed_count,
                "after_range_pruning": self.pruning_stats.get("after_range_pruning", original_count)
            },
            "tokens": {
                "original": original_tokens,
                "final": pruned_tokens,
                "saved": tokens_saved,
                "safe_zone_limit": self._get_parsed_safe_zone_tokens()
            },
            "compression": {
                "message_compression_ratio": pruned_count / original_count if original_count > 0 else 1.0,
                "token_compression_ratio": pruned_tokens / original_tokens if original_tokens > 0 else 1.0,
                "range_pruning_compression": (
                    self.pruning_stats.get(
                        "after_range_pruning", original_count) / original_count
                    if original_count > 0 else 1.0
                ),
                "tool_cleanup_compression": (
                    pruned_count /
                    self.pruning_stats.get(
                        "after_range_pruning", original_count)
                    if self.pruning_stats.get("after_range_pruning", original_count) > 0 else 1.0
                )
            },
            "changes": {
                "messages_removed_by_ids": (
                    original_count -
                    self.pruning_stats.get(
                        "after_range_pruning", original_count)
                ),
                "tool_results_modified": changes_analysis["tool_results_modified"],
                "tool_calls_modified": changes_analysis["tool_calls_modified"],
                "content_modifications": changes_analysis["content_modifications"],
                "unchanged_messages": changes_analysis["unchanged_messages"]
            },
            "message_distribution": {
                "original": original_distribution,
                "pruned": pruned_distribution
            },
            "detailed_changes": changes_analysis["detailed_changes"],
            "pruning_effectiveness": {
                "tokens_per_message_before": original_tokens / original_count if original_count > 0 else 0,
                "tokens_per_message_after": pruned_tokens / pruned_count if pruned_count > 0 else 0,
                "average_token_reduction_per_message": tokens_saved / original_count if original_count > 0 else 0,
                "within_safe_zone": pruned_tokens <= self._get_parsed_safe_zone_tokens()
            }
        }

        return report

    def _analyze_conversation_changes(self, original_conversations: List[Dict[str, Any]],
                                      pruned_conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析对话变化的详细信息。

        Args:
            original_conversations: 原始对话列表
            pruned_conversations: 裁剪后对话列表

        Returns:
            包含变化分析的字典
        """
        tool_results_modified = 0
        tool_calls_modified = 0
        content_modifications = 0
        unchanged_messages = 0
        detailed_changes = []

        # 创建一个映射来匹配原始和裁剪后的消息
        min_length = min(len(original_conversations),
                         len(pruned_conversations))

        for i in range(min_length):
            original_msg = original_conversations[i]
            pruned_msg = pruned_conversations[i]

            original_content = original_msg.get("content", "")
            pruned_content = pruned_msg.get("content", "")

            if original_content != pruned_content:
                content_modifications += 1

                # 分析修改类型
                change_type = "content_modified"
                tool_name = None

                if (original_msg.get("role") == "user" and
                        self._is_tool_result_message(original_content)):
                    tool_results_modified += 1
                    change_type = "tool_result_cleaned"
                    tool_name = self._extract_tool_name(original_content)

                elif (original_msg.get("role") == "assistant" and
                      self.tool_content_detector.is_tool_call_content(original_content)):
                    tool_calls_modified += 1
                    change_type = "tool_call_cleaned"
                    tool_info = self.tool_content_detector.detect_tool_call(
                        original_content)
                    tool_name = tool_info.get(
                        "tool_name") if tool_info else "unknown"

                detailed_changes.append({
                    "message_index": i,
                    "role": original_msg.get("role"),
                    "change_type": change_type,
                    "tool_name": tool_name,
                    "original_length": len(original_content),
                    "pruned_length": len(pruned_content),
                    "size_reduction": len(original_content) - len(pruned_content)
                })
            else:
                unchanged_messages += 1

        return {
            "tool_results_modified": tool_results_modified,
            "tool_calls_modified": tool_calls_modified,
            "content_modifications": content_modifications,
            "unchanged_messages": unchanged_messages,
            "detailed_changes": detailed_changes
        }

    def _analyze_message_distribution(self, conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析消息的角色分布和类型分布。

        Args:
            conversations: 对话列表

        Returns:
            包含分布信息的字典
        """
        role_counts = {"user": 0, "assistant": 0, "system": 0, "other": 0}
        message_types = {
            "tool_result": 0,
            "tool_call": 0,
            "regular_user": 0,
            "regular_assistant": 0,
            "system": 0
        }

        for msg in conversations:
            role = msg.get("role", "other")
            content = msg.get("content", "")

            # 统计角色分布
            if role in role_counts:
                role_counts[role] += 1
            else:
                role_counts["other"] += 1

            # 统计消息类型分布
            if role == "system":
                message_types["system"] += 1
            elif role == "user":
                if self._is_tool_result_message(content):
                    message_types["tool_result"] += 1
                else:
                    message_types["regular_user"] += 1
            elif role == "assistant":
                if self.tool_content_detector.is_tool_call_content(content):
                    message_types["tool_call"] += 1
                else:
                    message_types["regular_assistant"] += 1

        return {
            "total_messages": len(conversations),
            "role_distribution": role_counts,
            "message_type_distribution": message_types
        }
