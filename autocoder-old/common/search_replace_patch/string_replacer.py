"""
String-based text replacer implementation (formerly regex-based)
"""

from typing import List, Tuple
from loguru import logger

from .base import BaseReplacer, ReplaceResult, ReplaceStrategy


class StringReplacer(BaseReplacer):
    """基于字符串匹配的文本替换器（严格匹配模式）"""
    
    def __init__(self, lenient_mode: bool = False):
        """
        初始化字符串替换器
        
        Args:
            lenient_mode: 保留此参数以兼容现有代码，但在严格模式下不生效
        """
        super().__init__(ReplaceStrategy.STRING)
        self.lenient_mode = lenient_mode  # 保留但不使用
    
    def _find_line_boundaries(self, content: str, search_text: str) -> List[Tuple[int, int]]:
        """
        查找所有匹配的位置，确保是行级匹配
        
        Args:
            content: 文件内容
            search_text: 搜索文本
            
        Returns:
            匹配位置列表 [(start_pos, end_pos), ...]
        """
        matches = []
        lines = content.splitlines(keepends=True)
        search_lines = search_text.splitlines()
        
        if not search_lines:
            return matches
        
        # 对于单行搜索
        if len(search_lines) == 1:
            search_line = search_lines[0]
            current_pos = 0
            
            for i, line in enumerate(lines):
                line_content = line.rstrip('\r\n')
                if line_content == search_line:
                    # 找到匹配的完整行
                    line_start = current_pos
                    line_end = current_pos + len(line)
                    matches.append((line_start, line_end))
                current_pos += len(line)
        
        # 对于多行搜索
        else:
            for i in range(len(lines) - len(search_lines) + 1):
                match_found = True
                for j, search_line in enumerate(search_lines):
                    if i + j >= len(lines):
                        match_found = False
                        break
                    line_content = lines[i + j].rstrip('\r\n')
                    if line_content != search_line:
                        match_found = False
                        break
                
                if match_found:
                    # 计算多行匹配的起始和结束位置
                    start_pos = sum(len(lines[k]) for k in range(i))
                    end_pos = sum(len(lines[k]) for k in range(i + len(search_lines)))
                    matches.append((start_pos, end_pos))
        
        return matches
    
    def replace(self, content: str, search_blocks: List[Tuple[str, str]]) -> ReplaceResult:
        """
        执行字符串替换（行级替换）
        
        Args:
            content: 原始文件内容
            search_blocks: 搜索替换块列表
            
        Returns:
            ReplaceResult: 替换结果
        """
        if not self.validate_search_blocks(search_blocks):
            return ReplaceResult(
                success=False,
                message="Invalid search blocks provided",
                total_count=len(search_blocks)
            )
        
        current_content = content
        applied_count = 0
        errors = []
        
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
                    logger.info(f"String replacer inserted block {i+1}/{len(search_blocks)} at file head")
                    continue
                
                # ----- 正常替换操作 -----
                # 查找匹配位置（确保行级匹配）
                matches = self._find_line_boundaries(current_content, search_text)
                
                if matches:
                    # 只替换第一个匹配项，从后往前替换避免位置偏移
                    start_pos, end_pos = matches[0]
                    
                    # 构建替换后的内容
                    before = current_content[:start_pos]
                    after = current_content[end_pos:]
                    
                    # 处理替换文本的换行符
                    replacement = replace_text
                    if '\n' not in search_text and current_content[end_pos-1:end_pos] == '\n':
                        # 如果原文本是单行且以换行符结尾，替换文本也应该以换行符结尾
                        if not replacement.endswith(('\n', '\r\n')):
                            replacement += '\n'
                    
                    current_content = before + replacement + after
                    applied_count += 1
                    logger.info(f"String replacer applied block {i+1}/{len(search_blocks)}")
                else:
                    error_msg = f"🔍 Block {i+1}: No exact line match found\n   📝 Search text: {repr(search_text[:60])}{'...' if len(search_text) > 60 else ''}\n   💡 只支持行级精确匹配，请确保搜索文本完全匹配目标行"
                    errors.append(error_msg)
                    logger.warning(f"Block {i+1}: No exact match found for search text")
                        
            except Exception as e:
                error_msg = f"Block {i+1}: Unexpected error - {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        success = applied_count > 0
        
        if success:
            if errors:
                message = f"Partial success: Applied {applied_count}/{len(search_blocks)} blocks with {len(errors)} errors"
            else:
                message = f"Success: Applied {applied_count}/{len(search_blocks)} blocks"
        else:
            message = f"Failed: No blocks were applied. {len(errors)} errors occurred"
        
        return ReplaceResult(
            success=success,
            message=message,
            new_content=current_content if success else None,
            applied_count=applied_count,
            total_count=len(search_blocks),
            errors=errors,
            metadata={
                'strategy': self.get_strategy_name(),
                'strict_mode': True,  # 现在总是严格模式
                'lenient_mode': False  # 保留兼容性
            }
        )
    
    def can_handle(self, content: str, search_blocks: List[Tuple[str, str]]) -> bool:
        """
        检查是否能处理给定的内容和搜索块
        
        Args:
            content: 原始文件内容
            search_blocks: 搜索替换块列表
            
        Returns:
            bool: 总是返回 True，因为字符串替换器可以处理所有文本
        """
        return self.validate_search_blocks(search_blocks) 