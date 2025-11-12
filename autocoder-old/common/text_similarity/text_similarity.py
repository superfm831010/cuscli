
"""
Text Similarity Calculation Module

提供文本相似度计算功能，包括滑动窗口匹配和全窗口遍历匹配两种实现方式。
"""

from difflib import SequenceMatcher
from typing import Tuple, List, Dict, Any


class TextSimilarity:
    """
    文本相似度计算类
    
    用于计算两个文本之间的相似度，支持基于行的比较和滑动窗口匹配。
    """
    
    def __init__(self, text_a: str, text_b: str):
        """
        初始化文本相似度计算器
        
        Args:
            text_a: 源文本（较短的文本，用作匹配模板）
            text_b: 目标文本（较长的文本，在其中寻找匹配窗口）
        """
        self.text_a = text_a
        self.text_b = text_b
        self.lines_a = self._split_into_lines(text_a)
        self.lines_b = self._split_into_lines(text_b)
        self.m = len(self.lines_a)  # 源文本行数
        self.n = len(self.lines_b)  # 目标文本行数

    def _split_into_lines(self, text: str) -> List[str]:
        """
        将文本分割为行
        
        Args:
            text: 输入文本
            
        Returns:
            文本行列表
        """
        return text.splitlines()

    def _levenshtein_ratio(self, s1: str, s2: str) -> float:
        """
        计算两个字符串的莱文斯坦相似度比率
        
        Args:
            s1: 第一个字符串
            s2: 第二个字符串
            
        Returns:
            相似度比率 (0.0 - 1.0)
        """
        return SequenceMatcher(None, s1, s2).ratio()

    def get_best_matching_window(self) -> Tuple[float, str]:
        """
        获取最佳匹配窗口（原始实现）
        
        使用滑动窗口在目标文本中寻找与源文本最相似的片段。
        窗口大小固定为源文本的行数。
        
        Returns:
            Tuple[float, str]: (最佳相似度, 最佳匹配窗口的文本内容)
        """
        if self.m > self.n:
            # 如果源文本比目标文本长，返回整个目标文本
            similarity = self._levenshtein_ratio(self.text_a, self.text_b)
            return similarity, self.text_b
        
        best_similarity = 0
        best_window = []

        # 滑动窗口遍历
        for i in range(self.n - self.m + 1):
            window_b = self.lines_b[i:i + self.m]
            similarity = self._levenshtein_ratio("\n".join(self.lines_a), "\n".join(window_b))
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_window = window_b

        return best_similarity, "\n".join(best_window)

    def get_best_matching_window_all_sizes(self) -> Tuple[float, str, Dict[str, Any]]:
        """
        获取最佳匹配窗口（遍历所有窗口大小）
        
        遍历所有可能的窗口大小，找到得分最高的匹配窗口。
        这种方法更全面，但计算复杂度更高。
        
        Returns:
            Tuple[float, str, Dict[str, Any]]: (最佳相似度, 最佳匹配窗口的文本内容, 详细信息)
        """
        best_similarity = 0
        best_window = ""
        best_info = {
            "window_size": 0,
            "start_position": 0,
            "end_position": 0,
            "total_windows_checked": 0
        }
        
        total_windows = 0
        
        # 遍历所有可能的窗口大小
        for window_size in range(1, self.n + 1):
            # 对于每个窗口大小，遍历所有可能的起始位置
            for start_pos in range(self.n - window_size + 1):
                end_pos = start_pos + window_size
                window_b = self.lines_b[start_pos:end_pos]
                window_text = "\n".join(window_b)
                
                # 计算相似度
                similarity = self._levenshtein_ratio(self.text_a, window_text)
                total_windows += 1
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_window = window_text
                    best_info.update({
                        "window_size": window_size,
                        "start_position": start_pos,
                        "end_position": end_pos,
                        "total_windows_checked": total_windows
                    })
        
        best_info["total_windows_checked"] = total_windows
        return best_similarity, best_window, best_info

    def get_similarity_matrix(self) -> List[List[float]]:
        """
        获取行级别的相似度矩阵
        
        计算源文本的每一行与目标文本的每一行之间的相似度。
        
        Returns:
            相似度矩阵，其中 matrix[i][j] 表示源文本第i行与目标文本第j行的相似度
        """
        matrix = []
        for i, line_a in enumerate(self.lines_a):
            row = []
            for j, line_b in enumerate(self.lines_b):
                similarity = self._levenshtein_ratio(line_a, line_b)
                row.append(similarity)
            matrix.append(row)
        return matrix

    def get_window_similarities(self, window_size: int = None) -> List[Tuple[int, float, str]]:
        """
        获取所有窗口的相似度信息
        
        Args:
            window_size: 窗口大小，如果为None则使用源文本行数
            
        Returns:
            List[Tuple[int, float, str]]: (起始位置, 相似度, 窗口文本) 的列表
        """
        if window_size is None:
            window_size = self.m
            
        if window_size > self.n:
            window_size = self.n
            
        similarities = []
        for i in range(self.n - window_size + 1):
            window_b = self.lines_b[i:i + window_size]
            window_text = "\n".join(window_b)
            similarity = self._levenshtein_ratio(self.text_a, window_text)
            similarities.append((i, similarity, window_text))
            
        # 按相似度降序排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取文本统计信息
        
        Returns:
            包含各种统计信息的字典
        """
        return {
            "text_a_lines": self.m,
            "text_b_lines": self.n,
            "text_a_chars": len(self.text_a),
            "text_b_chars": len(self.text_b),
            "possible_windows": max(0, self.n - self.m + 1) if self.m <= self.n else 0,
            "full_text_similarity": self._levenshtein_ratio(self.text_a, self.text_b)
        }

