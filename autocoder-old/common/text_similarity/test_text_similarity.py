

"""
Text Similarity Module Tests

测试文本相似度计算模块的各项功能。
"""

import pytest
import sys
import os

from autocoder.common.text_similarity.text_similarity import TextSimilarity
from autocoder.common.text_similarity.utils import compare_texts_simple, find_best_matches, analyze_text_similarity


class TestTextSimilarity:
    """测试 TextSimilarity 类的功能"""
    
    def setup_method(self):
        """设置测试数据"""
        # 测试目标：验证基本的文本相似度计算功能
        self.text_a = """def hello_world():
    print("Hello, World!")
    return True"""
        
        self.text_b = """import os
import sys

def hello_world():
    print("Hello, World!")
    return True

def goodbye_world():
    print("Goodbye, World!")
    return False

if __name__ == "__main__":
    hello_world()
    goodbye_world()"""
    
    def test_initialization(self):
        """测试目标：验证 TextSimilarity 类的正确初始化"""
        similarity = TextSimilarity(self.text_a, self.text_b)
        
        assert similarity.text_a == self.text_a
        assert similarity.text_b == self.text_b
        assert similarity.m == 3  # text_a 有 3 行
        assert similarity.n == 14  # text_b 有 14 行（包括空行）
        assert len(similarity.lines_a) == 3
        assert len(similarity.lines_b) == 14
    
    def test_split_into_lines(self):
        """测试目标：验证文本正确分割为行"""
        similarity = TextSimilarity(self.text_a, self.text_b)
        
        lines_a = similarity._split_into_lines(self.text_a)
        expected_lines_a = [
            'def hello_world():',
            '    print("Hello, World!")',
            '    return True'
        ]
        
        assert lines_a == expected_lines_a
    
    def test_levenshtein_ratio(self):
        """测试目标：验证莱文斯坦相似度计算的正确性"""
        similarity = TextSimilarity(self.text_a, self.text_b)
        
        # 完全相同的字符串
        ratio1 = similarity._levenshtein_ratio("hello", "hello")
        assert ratio1 == 1.0
        
        # 完全不同的字符串
        ratio2 = similarity._levenshtein_ratio("hello", "world")
        assert 0.0 <= ratio2 <= 1.0
        
        # 部分相似的字符串
        ratio3 = similarity._levenshtein_ratio("hello", "hallo")
        assert 0.0 < ratio3 < 1.0
    
    def test_get_best_matching_window(self):
        """测试目标：验证基本滑动窗口匹配功能的正确性"""
        similarity = TextSimilarity(self.text_a, self.text_b)
        
        score, window = similarity.get_best_matching_window()
        
        # 验证返回值类型
        assert isinstance(score, float)
        assert isinstance(window, str)
        
        # 验证相似度在合理范围内
        assert 0.0 <= score <= 1.0
        
        # 验证窗口长度（应该包含3行，因为text_a有3行）
        window_lines = window.split('\n')
        assert len(window_lines) == 3
        
        # 验证找到的是最相似的部分（应该包含hello_world函数）
        assert "hello_world" in window.lower()
    
    def test_get_best_matching_window_all_sizes(self):
        """测试目标：验证全窗口大小遍历匹配功能的正确性"""
        similarity = TextSimilarity(self.text_a, self.text_b)
        
        score, window, info = similarity.get_best_matching_window_all_sizes()
        
        # 验证返回值类型
        assert isinstance(score, float)
        assert isinstance(window, str)
        assert isinstance(info, dict)
        
        # 验证相似度在合理范围内
        assert 0.0 <= score <= 1.0
        
        # 验证详细信息包含必要字段
        required_keys = ["window_size", "start_position", "end_position", "total_windows_checked"]
        for key in required_keys:
            assert key in info
        
        # 验证检查的窗口数量是合理的
        assert info["total_windows_checked"] > 0
        
        # 验证位置信息的合理性
        assert 0 <= info["start_position"] < info["end_position"] <= similarity.n
    
    def test_get_similarity_matrix(self):
        """测试目标：验证相似度矩阵计算的正确性"""
        similarity = TextSimilarity(self.text_a, self.text_b)
        
        matrix = similarity.get_similarity_matrix()
        
        # 验证矩阵维度
        assert len(matrix) == similarity.m  # 行数等于text_a的行数
        for row in matrix:
            assert len(row) == similarity.n  # 列数等于text_b的行数
        
        # 验证矩阵中的值都在[0,1]范围内
        for i in range(len(matrix)):
            for j in range(len(matrix[i])):
                assert 0.0 <= matrix[i][j] <= 1.0
    
    def test_get_window_similarities(self):
        """测试目标：验证窗口相似度列表功能的正确性"""
        similarity = TextSimilarity(self.text_a, self.text_b)
        
        similarities = similarity.get_window_similarities()
        
        # 验证返回的是列表
        assert isinstance(similarities, list)
        
        # 验证每个元素的结构
        for item in similarities:
            assert isinstance(item, tuple)
            assert len(item) == 3
            start_pos, score, window_text = item
            
            assert isinstance(start_pos, int)
            assert isinstance(score, float)
            assert isinstance(window_text, str)
            
            assert 0.0 <= score <= 1.0
            assert start_pos >= 0
        
        # 验证结果按相似度降序排列
        scores = [item[1] for item in similarities]
        assert scores == sorted(scores, reverse=True)
    
    def test_get_statistics(self):
        """测试目标：验证统计信息功能的正确性"""
        similarity = TextSimilarity(self.text_a, self.text_b)
        
        stats = similarity.get_statistics()
        
        # 验证统计信息包含所有必要字段
        required_keys = [
            "text_a_lines", "text_b_lines", "text_a_chars", "text_b_chars",
            "possible_windows", "full_text_similarity"
        ]
        for key in required_keys:
            assert key in stats
        
        # 验证统计信息的正确性
        assert stats["text_a_lines"] == 3
        assert stats["text_b_lines"] == 14
        assert stats["text_a_chars"] == len(self.text_a)
        assert stats["text_b_chars"] == len(self.text_b)
        assert stats["possible_windows"] == 12  # 14 - 3 + 1
        assert 0.0 <= stats["full_text_similarity"] <= 1.0
    
    def test_edge_cases(self):
        """测试目标：验证边界情况的处理"""
        # 空文本测试
        empty_similarity = TextSimilarity("", "some text")
        score, window = empty_similarity.get_best_matching_window()
        assert isinstance(score, float)
        
        # 源文本比目标文本长的情况
        long_short_similarity = TextSimilarity("very long text here", "short")
        score, window = long_short_similarity.get_best_matching_window()
        assert window == "short"
        
        # 相同文本测试
        same_similarity = TextSimilarity("same text", "same text")
        score, window = same_similarity.get_best_matching_window()
        assert score == 1.0
        assert window == "same text"


class TestUtils:
    """测试工具函数"""
    
    def setup_method(self):
        """设置测试数据"""
        self.text_a = "Hello World"
        self.text_b = "Hello Beautiful World\nGoodbye Cruel World\nHello Again"
    
    def test_compare_texts_simple(self):
        """测试目标：验证简单文本比较功能的完整性"""
        result = compare_texts_simple(self.text_a, self.text_b)
        
        # 验证返回结构
        assert "basic_matching" in result
        assert "comprehensive_matching" in result
        assert "statistics" in result
        
        # 验证基本匹配结果
        basic = result["basic_matching"]
        assert "score" in basic
        assert "window" in basic
        assert isinstance(basic["score"], float)
        assert isinstance(basic["window"], str)
        
        # 验证全面匹配结果
        comprehensive = result["comprehensive_matching"]
        assert "score" in comprehensive
        assert "window" in comprehensive
        assert "details" in comprehensive
    
    def test_find_best_matches(self):
        """测试目标：验证最佳匹配查找功能的准确性"""
        matches = find_best_matches(self.text_a, self.text_b, top_k=2)
        
        # 验证返回的匹配数量
        assert len(matches) <= 2
        
        # 验证每个匹配的结构
        for match in matches:
            required_keys = ["rank", "start_position", "end_position", "similarity_score", "window_text"]
            for key in required_keys:
                assert key in match
            
            assert isinstance(match["similarity_score"], float)
            assert 0.0 <= match["similarity_score"] <= 1.0
    
    def test_analyze_text_similarity(self):
        """测试目标：验证全面文本相似度分析功能的完整性"""
        analysis = analyze_text_similarity(self.text_a, self.text_b)
        
        # 验证分析结果包含所有必要部分
        required_sections = [
            "summary", "basic_matching", "comprehensive_matching", 
            "top_matches", "statistics", "similarity_matrix_shape"
        ]
        for section in required_sections:
            assert section in analysis
        
        # 验证摘要信息
        summary = analysis["summary"]
        assert "basic_best_score" in summary
        assert "comprehensive_best_score" in summary
        assert "improvement" in summary
        assert "total_windows_checked" in summary
        
        # 验证改进值的合理性（全面搜索应该不差于基本搜索）
        assert summary["improvement"] >= 0


if __name__ == "__main__":
    # 运行简单的功能验证测试
    print("运行文本相似度模块测试...")
    
    # 基本功能测试
    text_a = "def test():\n    return True"
    text_b = "import sys\n\ndef test():\n    return True\n\ndef main():\n    test()"
    
    similarity = TextSimilarity(text_a, text_b)
    
    print("=== 基本匹配测试 ===")
    score1, window1 = similarity.get_best_matching_window()
    print(f"基本匹配得分: {score1:.4f}")
    print(f"匹配窗口:\n{window1}")
    
    print("\n=== 全面匹配测试 ===")
    score2, window2, info2 = similarity.get_best_matching_window_all_sizes()
    print(f"全面匹配得分: {score2:.4f}")
    print(f"检查窗口数: {info2['total_windows_checked']}")
    print(f"最佳窗口大小: {info2['window_size']}")
    print(f"匹配窗口:\n{window2}")
    
    print(f"\n=== 性能对比 ===")
    print(f"得分提升: {score2 - score1:.4f}")
    
    print("\n测试完成！")


