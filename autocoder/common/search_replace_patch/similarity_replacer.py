"""
Similarity-based text replacer implementation
"""

from typing import List, Tuple
from loguru import logger

from .base import BaseReplacer, ReplaceResult, ReplaceStrategy
from ..text_similarity import TextSimilarity


class SimilarityReplacer(BaseReplacer):
    """基于文本相似度的替换器"""
    
    def __init__(self, similarity_threshold: float = 0.9):
        """
        初始化相似度替换器
        
        Args:
            similarity_threshold: 相似度阈值，超过此值才进行替换
        """
        super().__init__(ReplaceStrategy.SIMILARITY)
        self.similarity_threshold = similarity_threshold
    
    def _find_line_numbers(self, content: str, text_block: str) -> Tuple[int, int]:
        """
        找到文本块在内容中的行号
        
        Args:
            content: 完整文件内容
            text_block: 要查找的文本块
            
        Returns:
            Tuple[int, int]: (起始行号, 结束行号)，1-based，如果未找到返回 (-1, -1)
        """
        lines = content.splitlines()
        block_lines = text_block.splitlines()
        
        # 找到文本块在内容中的位置
        block_start_idx = content.find(text_block)
        if block_start_idx == -1:
            return (-1, -1)
        
        # 计算到文本块开始位置的行数
        lines_before = content[:block_start_idx].count('\n')
        start_line = lines_before + 1
        
        # 计算文本块的行数
        lines_in_block = len(block_lines)
        end_line = start_line + lines_in_block - 1
        
        return (start_line, end_line)
    
    def _replace_by_line_numbers(self, content: str, start_line: int, end_line: int, 
                                 replace_text: str) -> str:
        """
        根据行号替换文本
        
        Args:
            content: 原始内容
            start_line: 起始行号（1-based）
            end_line: 结束行号（1-based）
            replace_text: 替换的文本
            
        Returns:
            替换后的内容
        """
        lines = content.splitlines(keepends=True)
        
        # 转换为0-based索引
        start_idx = start_line - 1
        end_idx = end_line - 1
        
        # 确保索引有效
        if start_idx < 0 or end_idx >= len(lines) or start_idx > end_idx:
            return content
        
        # 构建新内容
        new_lines = []
        new_lines.extend(lines[:start_idx])
        
        # 添加替换文本
        replace_lines = replace_text.splitlines(keepends=True)
        # 如果替换文本最后没有换行符，但原始文本有，则添加换行符
        if replace_lines and not replace_lines[-1].endswith('\n') and end_idx < len(lines) - 1:
            replace_lines[-1] += '\n'
        new_lines.extend(replace_lines)
        
        new_lines.extend(lines[end_idx + 1:])
        
        return ''.join(new_lines)
    
    def _build_similarity_error_message(self, block_index: int, search_text: str, similarity: float, 
                                       threshold: float, best_match: str, start_line: int, end_line: int) -> str:
        """
        构建针对大模型的详细相似度错误信息
        """
        message_parts = []
        
        message_parts.append(f"🔍 Block {block_index} Similarity Analysis:")
        message_parts.append(f"   📏 Found similarity: {similarity:.1%} (threshold: {threshold:.1%})")
        
        if similarity > 0.8:
            message_parts.append(f"   ✅ Very close match found at lines {start_line}-{end_line}")
            message_parts.append(f"   📝 Expected: {repr(search_text[:80])}{'...' if len(search_text) > 80 else ''}")
            message_parts.append(f"   📝 Actual:   {repr(best_match[:80])}{'...' if len(best_match) > 80 else ''}")
            message_parts.append("   💡 Use the exact content shown as 'Actual' in your SEARCH block")
        elif similarity > 0.6:
            message_parts.append(f"   ⚠️  Moderate similarity at lines {start_line}-{end_line}")
            message_parts.append(f"   📝 Your search: {repr(search_text[:60])}{'...' if len(search_text) > 60 else ''}")
            message_parts.append(f"   📝 Best match:  {repr(best_match[:60])}{'...' if len(best_match) > 60 else ''}")
            message_parts.append("   💡 Check for whitespace, line ending, or formatting differences")
        else:
            message_parts.append(f"   ❌ Low similarity - content may not exist as expected")
            message_parts.append(f"   📝 Searched for: {repr(search_text[:60])}{'...' if len(search_text) > 60 else ''}")
            message_parts.append("   💡 Verify the content exists or try a smaller, more unique search phrase")
        
        return "\n".join(message_parts)
    
    def replace(self, content: str, search_blocks: List[Tuple[str, str]]) -> ReplaceResult:
        """
        执行基于相似度的替换（行级替换）
        
        Args:
            content: 原始文件内容
            search_blocks: 搜索替换块列表
            
        Returns:
            ReplaceResult: 替换结果
        """
        if not self.validate_search_blocks(search_blocks):
            return ReplaceResult(
                success=False,
                message="Invalid search blocks provided. 只支持行级替换。",
                total_count=len(search_blocks)
            )
        
        current_content = content
        applied_count = 0
        errors = []
        similarity_info = []
        
        for i, (search_text, replace_text) in enumerate(search_blocks):
            try:
                # ----- 插入操作 -----
                if search_text == "":
                    # 插入到文件开头
                    insert_text = replace_text
                    # 如果插入文本不以换行符结尾，自动补一个，保持行级语义
                    if not insert_text.endswith(("\n", "\r\n")):
                        insert_text += "\n"
                    
                    current_content = insert_text + current_content
                    applied_count += 1
                    logger.info(f"Similarity replacer inserted block {i+1}/{len(search_blocks)} at file head")
                    continue
                
                # ----- 正常替换操作 -----
                # 硬约束：检查是否为行级替换
                if not self._is_line_level_search(search_text, content):
                    error_msg = f"🔍 Block {i+1}: 只支持行级替换\n   📝 Search text: {repr(search_text[:60])}{'...' if len(search_text) > 60 else ''}\n   💡 请确保搜索文本匹配完整行"
                    errors.append(error_msg)
                    continue
                
                # 使用TextSimilarity查找最佳匹配
                similarity_finder = TextSimilarity(search_text, current_content)
                similarity, best_window = similarity_finder.get_best_matching_window()
                
                logger.info(f"Block {i+1}: Found similarity {similarity:.3f} with threshold {self.similarity_threshold}")
                
                if similarity >= self.similarity_threshold:
                    # 找到行号
                    start_line, end_line = self._find_line_numbers(current_content, best_window)
                    
                    if start_line > 0 and end_line > 0:
                        # 执行替换
                        new_content = self._replace_by_line_numbers(
                            current_content, start_line, end_line, replace_text
                        )
                        
                        if new_content != current_content:
                            current_content = new_content
                            applied_count += 1
                            similarity_info.append({
                                'block_index': i + 1,
                                'similarity': similarity,
                                'start_line': start_line,
                                'end_line': end_line,
                                'matched_text': best_window[:100] + '...' if len(best_window) > 100 else best_window
                            })
                            logger.info(f"Applied block {i+1} at lines {start_line}-{end_line}")
                        else:
                            error_msg = f"Block {i+1}: Replacement did not change content"
                            errors.append(error_msg)
                            logger.warning(error_msg)
                    else:
                        error_msg = f"Block {i+1}: Could not determine line numbers for matched text"
                        errors.append(error_msg)
                        logger.warning(error_msg)
                else:
                    # 构建详细的错误信息给大模型
                    start_line, end_line = self._find_line_numbers(current_content, best_window)
                    error_msg = self._build_similarity_error_message(
                        i + 1, search_text, similarity, self.similarity_threshold, 
                        best_window, start_line, end_line
                    )
                    errors.append(error_msg)
                    logger.warning(f"Block {i+1}: Similarity {similarity:.3f} below threshold {self.similarity_threshold:.3f}")
                    
                    # 提供调试信息
                    similarity_info.append({
                        'block_index': i + 1,
                        'similarity': similarity,
                        'threshold': self.similarity_threshold,
                        'best_match': best_window[:100] + '...' if len(best_window) > 100 else best_window,
                        'location': f"lines {start_line}-{end_line}" if start_line > 0 else "unknown"
                    })
                    
            except Exception as e:
                error_msg = f"Block {i+1}: Error during similarity matching - {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        success = applied_count > 0
        
        if success:
            if errors:
                message = f"Partial success: Applied {applied_count}/{len(search_blocks)} blocks with {len(errors)} errors"
            else:
                message = f"Success: Applied {applied_count}/{len(search_blocks)} blocks using similarity matching"
        else:
            message = f"Failed: No blocks were applied using similarity matching. {len(errors)} errors occurred"
        
        return ReplaceResult(
            success=success,
            message=message,
            new_content=current_content if success else None,
            applied_count=applied_count,
            total_count=len(search_blocks),
            errors=errors,
            metadata={
                'strategy': self.get_strategy_name(),
                'similarity_threshold': self.similarity_threshold,
                'similarity_info': similarity_info
            }
        )
    
    def can_handle(self, content: str, search_blocks: List[Tuple[str, str]]) -> bool:
        """
        检查是否能处理给定的内容和搜索块
        
        Args:
            content: 原始文件内容
            search_blocks: 搜索替换块列表
            
        Returns:
            bool: 总是返回 True，因为相似度替换器可以处理所有文本
        """
        return self.validate_search_blocks(search_blocks)
    
    def set_similarity_threshold(self, threshold: float):
        """
        设置相似度阈值
        
        Args:
            threshold: 新的相似度阈值 (0.0 - 1.0)
        """
        if 0.0 <= threshold <= 1.0:
            self.similarity_threshold = threshold
            logger.info(f"Similarity threshold set to {threshold}")
        else:
            logger.warning(f"Invalid similarity threshold {threshold}, must be between 0.0 and 1.0")
    
    def _is_line_level_search(self, search_text: str, content: str) -> bool:
        """
        检查搜索文本是否为行级搜索
        
        Args:
            search_text: 搜索文本
            content: 文件内容
            
        Returns:
            bool: 是否为行级搜索
        """
        # 如果搜索文本包含换行符，认为是多行搜索，允许
        if '\n' in search_text:
            return True
        
        # 对于单行文本，使用TextSimilarity检查是否能找到完整行匹配
        try:
            similarity_finder = TextSimilarity(search_text, content)
            similarity, best_window = similarity_finder.get_best_matching_window()
            
            # 检查最佳匹配是否为完整行
            if similarity >= self.similarity_threshold:
                content_lines = content.splitlines()
                best_window_stripped = best_window.strip()
                
                # 检查最佳匹配是否等于某一完整行
                for line in content_lines:
                    if line.strip() == best_window_stripped:
                        return True
            
            return False
        except Exception:
            return False 