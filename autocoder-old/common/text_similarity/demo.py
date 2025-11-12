

#!/usr/bin/env python3
"""
Text Similarity Module Demo

演示两个版本的 get_best_matching_window 函数的差异和用法。
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.insert(0, project_root)

try:
    from .text_similarity import TextSimilarity
except ImportError:
    from text_similarity import TextSimilarity


def demo_two_versions():
    """演示两个版本的get_best_matching_window函数"""
    print("=" * 60)
    print("Text Similarity Module - 两个版本函数演示")
    print("=" * 60)
    
    # 测试案例1：展示两个版本的基本差异
    print("\n【测试案例1】基本功能对比")
    print("-" * 40)
    
    source_text = """def hello():
    print("Hello")
    return True"""
    
    target_text = """import os
import sys

def hello():
    print("Hello")
    return True

def goodbye():
    print("Goodbye")
    return False

def main():
    hello()
    goodbye()

if __name__ == "__main__":
    main()"""
    
    similarity = TextSimilarity(source_text, target_text)
    
    # 版本1：原始实现（固定窗口大小）
    print("版本1 - get_best_matching_window()（原始实现）:")
    score1, window1 = similarity.get_best_matching_window()
    print(f"  得分: {score1:.4f}")
    print(f"  窗口大小: {len(window1.splitlines())} 行（固定为源文本行数）")
    print(f"  匹配内容:\n{window1}")
    
    # 版本2：遍历所有窗口大小
    print("\n版本2 - get_best_matching_window_all_sizes()（遍历所有窗口）:")
    score2, window2, info2 = similarity.get_best_matching_window_all_sizes()
    print(f"  得分: {score2:.4f}")
    print(f"  最佳窗口大小: {info2['window_size']} 行")
    print(f"  窗口位置: {info2['start_position']}-{info2['end_position']}")
    print(f"  检查的窗口总数: {info2['total_windows_checked']}")
    print(f"  匹配内容:\n{window2}")
    
    print(f"\n性能对比:")
    print(f"  得分提升: {score2 - score1:.4f}")
    print(f"  效率差异: 版本2检查了 {info2['total_windows_checked']} 个窗口，版本1只检查了 {similarity.n - similarity.m + 1} 个")
    
    # 测试案例2：展示版本2能找到更好匹配的情况
    print("\n\n【测试案例2】版本2优势展示")
    print("-" * 40)
    
    query = "error handling"
    
    code_base = """import logging
logger = logging.getLogger(__name__)

def process_data(data):
    try:
        result = complex_operation(data)
        return result
    except ValueError as e:
        logger.error(f"Data processing error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

def error_handling():
    print("This function handles errors")

def main():
    try:
        process_data(None)
    except Exception:
        print("Error handled in main")"""
    
    similarity2 = TextSimilarity(query, code_base)
    
    print(f"查询: '{query}'")
    
    # 版本1结果
    score1, window1 = similarity2.get_best_matching_window()
    print(f"\n版本1结果:")
    print(f"  得分: {score1:.4f}")
    print(f"  匹配内容: {repr(window1)}")
    
    # 版本2结果
    score2, window2, info2 = similarity2.get_best_matching_window_all_sizes()
    print(f"\n版本2结果:")
    print(f"  得分: {score2:.4f}")
    print(f"  最佳窗口大小: {info2['window_size']} 行")
    print(f"  匹配内容: {repr(window2)}")
    
    if score2 > score1:
        print(f"\n✓ 版本2找到了更好的匹配！得分提升: {score2 - score1:.4f}")
    elif score2 == score1:
        print(f"\n= 两个版本找到了相同质量的匹配")
    else:
        print(f"\n? 意外情况：版本1得分更高")


def demo_practical_usage():
    """演示实际使用场景"""
    print("\n\n【实际使用场景演示】")
    print("-" * 40)
    
    # 代码片段搜索场景
    function_signature = "def calculate(a, b):"
    
    codebase = """class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def calculate(a, b):
        return a * b
    
    def subtract(self, a, b):
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result
    
    def calculate_advanced(self, operation, a, b):
        if operation == "power":
            return a ** b
        elif operation == "divide":
            return a / b if b != 0 else None
        return None"""
    
    print(f"搜索函数签名: '{function_signature}'")
    
    similarity = TextSimilarity(function_signature, codebase)
    
    # 获取所有窗口的相似度排序
    all_matches = similarity.get_window_similarities()
    
    print(f"\n找到 {len(all_matches)} 个可能的匹配:")
    for i, (start_pos, score, window_text) in enumerate(all_matches[:3]):
        print(f"  {i+1}. 得分: {score:.4f} | 位置: {start_pos} | 内容: {repr(window_text[:30])}...")
    
    # 比较两个版本
    score1, window1 = similarity.get_best_matching_window()
    score2, window2, info2 = similarity.get_best_matching_window_all_sizes()
    
    print(f"\n版本对比:")
    print(f"  版本1 (固定窗口): {score1:.4f}")
    print(f"  版本2 (全搜索): {score2:.4f}")
    print(f"  版本2检查了 {info2['total_windows_checked']} 个窗口")


def demo_statistics():
    """演示统计功能"""
    print("\n\n【统计信息演示】")
    print("-" * 40)
    
    text_a = "Hello World\nPython Programming"
    text_b = "Welcome to Python\nHello World\nProgramming Tutorial\nGoodbye World"
    
    similarity = TextSimilarity(text_a, text_b)
    stats = similarity.get_statistics()
    
    print("文本统计信息:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 相似度矩阵
    matrix = similarity.get_similarity_matrix()
    print(f"\n相似度矩阵 ({len(matrix)}x{len(matrix[0])}):")
    for i, row in enumerate(matrix):
        formatted_row = [f"{val:.2f}" for val in row]
        print(f"  行{i+1}: {formatted_row}")


if __name__ == "__main__":
    demo_two_versions()
    demo_practical_usage()
    demo_statistics()
    
    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


