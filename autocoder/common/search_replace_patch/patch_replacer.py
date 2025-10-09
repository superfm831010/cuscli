"""
Patch-based text replacer implementation
"""

import tempfile
import os
from typing import List, Tuple, Optional
from loguru import logger

from .base import BaseReplacer, ReplaceResult, ReplaceStrategy


class PatchReplacer(BaseReplacer):
    """基于补丁库的文本替换器"""
    
    def __init__(self, use_patch_ng: bool = True):
        """
        初始化补丁替换器
        
        Args:
            use_patch_ng: 是否使用 patch-ng 库（True）还是 unidiff 库（False）
        """
        super().__init__(ReplaceStrategy.PATCH)
        self.use_patch_ng = use_patch_ng
        self._patch_module = None
        self._load_patch_module()
    
    def _load_patch_module(self):
        """加载补丁模块"""
        try:
            if self.use_patch_ng:
                try:
                    import patch_ng
                    self._patch_module = patch_ng
                    logger.info("Loaded patch-ng module")
                except ImportError:
                    logger.warning("patch-ng not available, falling back to unidiff")
                    self.use_patch_ng = False
            
            if not self.use_patch_ng:
                try:
                    import unidiff
                    self._patch_module = unidiff
                    logger.info("Loaded unidiff module")
                except ImportError:
                    logger.error("Neither patch-ng nor unidiff is available")
                    self._patch_module = None
                    
        except Exception as e:
            logger.error(f"Failed to load patch module: {e}")
            self._patch_module = None
    
    def _search_blocks_to_unified_diff(self, search_blocks: List[Tuple[str, str]], 
                                       filename: str = "file.txt") -> str:
        """
        将搜索替换块转换为统一差异格式
        
        Args:
            search_blocks: 搜索替换块列表
            filename: 文件名（用于生成diff头）
            
        Returns:
            统一差异格式的字符串
        """
        # 为了简化，我们假设每个搜索块都是完整的替换
        # 实际应用中可能需要更复杂的逻辑来生成正确的unified diff
        
        diff_lines = []
        diff_lines.append(f"--- a/{filename}")
        diff_lines.append(f"+++ b/{filename}")
        
        for i, (search_text, replace_text) in enumerate(search_blocks):
            search_lines = search_text.splitlines()
            replace_lines = replace_text.splitlines()
            
            # 生成hunk头
            diff_lines.append(f"@@ -{i+1},{len(search_lines)} +{i+1},{len(replace_lines)} @@")
            
            # 添加删除行
            for line in search_lines:
                diff_lines.append(f"-{line}")
            
            # 添加添加行
            for line in replace_lines:
                diff_lines.append(f"+{line}")
        
        return "\n".join(diff_lines) + "\n"
    
    def _apply_patch_ng(self, content: str, diff_content: str, filename: str) -> Optional[str]:
        """
        使用 patch-ng 应用补丁
        
        Args:
            content: 原始内容
            diff_content: 差异内容
            filename: 文件名
            
        Returns:
            应用补丁后的内容，失败时返回 None
        """
        try:
            patchset = self._patch_module.PatchSet.from_string(diff_content)
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(content)
                temp_file = f.name
            
            try:
                # 应用补丁
                if patchset.apply(root=os.path.dirname(temp_file)):
                    with open(temp_file, 'r', encoding='utf-8') as f:
                        return f.read()
                else:
                    logger.error("Failed to apply patch using patch-ng")
                    return None
            finally:
                # 清理临时文件
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    
        except Exception as e:
            logger.error(f"Error applying patch with patch-ng: {e}")
            return None
    
    def _apply_unidiff(self, content: str, diff_content: str, filename: str) -> Optional[str]:
        """
        使用 unidiff 应用补丁
        
        Args:
            content: 原始内容
            diff_content: 差异内容
            filename: 文件名
            
        Returns:
            应用补丁后的内容，失败时返回 None
        """
        try:
            patchset = self._patch_module.PatchSet(diff_content)
            
            if not patchset:
                logger.error("No patches found in diff content")
                return None
            
            # 取第一个补丁文件
            patch_file = patchset[0]
            
            # 将内容分割为行
            lines = content.splitlines(keepends=True)
            
            # 应用补丁
            try:
                new_lines = self._apply_patch_to_lines(lines, patch_file)
                return ''.join(new_lines)
            except Exception as e:
                logger.error(f"Error applying patch to lines: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error applying patch with unidiff: {e}")
            return None
    
    def _apply_patch_to_lines(self, lines: List[str], patch_file) -> List[str]:
        """
        将补丁应用到行列表
        
        Args:
            lines: 原始行列表
            patch_file: 补丁文件对象
            
        Returns:
            应用补丁后的行列表
        """
        new_lines = lines.copy()
        
        # 按照行号倒序处理hunks，避免行号偏移问题
        for hunk in reversed(patch_file):
            target_line = hunk.target_start - 1  # 转换为0索引
            
            # 删除旧行
            lines_to_remove = [line for line in hunk if line.is_removed]
            for _ in lines_to_remove:
                if target_line < len(new_lines):
                    new_lines.pop(target_line)
            
            # 添加新行
            lines_to_add = [line.value for line in hunk if line.is_added]
            for i, line_value in enumerate(lines_to_add):
                new_lines.insert(target_line + i, line_value)
        
        return new_lines
    
    def replace(self, content: str, search_blocks: List[Tuple[str, str]]) -> ReplaceResult:
        """
        执行基于补丁的替换
        
        Args:
            content: 原始文件内容
            search_blocks: 搜索替换块列表
            
        Returns:
            ReplaceResult: 替换结果
        """
        if not self._patch_module:
            return ReplaceResult(
                success=False,
                message="No patch module available. Please install patch-ng or unidiff",
                total_count=len(search_blocks)
            )
        
        if not self.validate_search_blocks(search_blocks):
            return ReplaceResult(
                success=False,
                message="Invalid search blocks provided",
                total_count=len(search_blocks)
            )
        
        try:
            # 检查是否有插入操作
            insert_blocks = [(i, replace_text) for i, (search_text, replace_text) in enumerate(search_blocks) if search_text == ""]
            regular_blocks = [(search_text, replace_text) for search_text, replace_text in search_blocks if search_text != ""]
            
            current_content = content
            applied_count = 0
            
            # 先处理插入操作
            for i, insert_text in insert_blocks:
                # 插入到文件开头
                if not insert_text.endswith(("\n", "\r\n")):
                    insert_text += "\n"
                
                current_content = insert_text + current_content
                applied_count += 1
                logger.info(f"Patch replacer inserted block {i+1}/{len(search_blocks)} at file head")
            
            # 如果没有常规替换块，直接返回插入结果
            if not regular_blocks:
                return ReplaceResult(
                    success=True,
                    message=f"Successfully inserted {applied_count} blocks at file head",
                    new_content=current_content,
                    applied_count=applied_count,
                    total_count=len(search_blocks),
                    metadata={
                        'strategy': self.get_strategy_name(),
                        'patch_module': 'patch-ng' if self.use_patch_ng else 'unidiff'
                    }
                )
            
            # 处理常规替换块
            # 将搜索替换块转换为统一差异格式
            diff_content = self._search_blocks_to_unified_diff(regular_blocks)
            logger.debug(f"Generated diff content:\n{diff_content}")
            
            # 应用补丁
            if self.use_patch_ng:
                new_content = self._apply_patch_ng(current_content, diff_content, "file.txt")
            else:
                new_content = self._apply_unidiff(current_content, diff_content, "file.txt")
            
            if new_content is not None:
                return ReplaceResult(
                    success=True,
                    message=f"Successfully applied patch with {len(regular_blocks)} blocks and {len(insert_blocks)} inserts",
                    new_content=new_content,
                    applied_count=applied_count + len(regular_blocks),
                    total_count=len(search_blocks),
                    metadata={
                        'strategy': self.get_strategy_name(),
                        'patch_module': 'patch-ng' if self.use_patch_ng else 'unidiff'
                    }
                )
            else:
                return ReplaceResult(
                    success=applied_count > 0,
                    message=f"Failed to apply patch for regular blocks, but {applied_count} inserts succeeded",
                    new_content=current_content if applied_count > 0 else None,
                    applied_count=applied_count,
                    total_count=len(search_blocks),
                    errors=["Patch application failed for regular blocks"]
                )
                
        except Exception as e:
            logger.error(f"Error in patch replacement: {e}")
            return ReplaceResult(
                success=False,
                message=f"Error in patch replacement: {str(e)}",
                total_count=len(search_blocks),
                errors=[str(e)]
            )
    
    def can_handle(self, content: str, search_blocks: List[Tuple[str, str]]) -> bool:
        """
        检查是否能处理给定的内容和搜索块
        
        Args:
            content: 原始文件内容
            search_blocks: 搜索替换块列表
            
        Returns:
            bool: 是否能处理
        """
        return (self._patch_module is not None and 
                self.validate_search_blocks(search_blocks)) 