

"""
Text Similarity Module Usage Examples

展示文本相似度模块的各种使用方式和应用场景。
"""

import sys
import os


from autocoder.common.text_similarity.text_similarity import TextSimilarity
from autocoder.common.text_similarity.utils import compare_texts_simple, find_best_matches, analyze_text_similarity



def basic_usage_example():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    # 示例代码片段
    code_snippet = """def calculate_sum(a, b):
    result = a + b
    return result"""
    
    full_code = """import math

def calculate_sum(a, b):
    result = a + b
    return result

def calculate_product(a, b):
    result = a * b
    return result

def main():
    print(calculate_sum(1, 2))
    print(calculate_product(3, 4))

if __name__ == "__main__":
    main()"""
    
    # 创建相似度计算器
    similarity = TextSimilarity(code_snippet, full_code)
    
    # 基本匹配
    score, window = similarity.get_best_matching_window()
    print(f"基本匹配得分: {score:.4f}")
    print(f"匹配到的代码片段:\n{window}")
    
    # 全面匹配
    full_score, full_window, info = similarity.get_best_matching_window_all_sizes()
    print(f"\n全面匹配得分: {full_score:.4f}")
    print(f"最佳窗口大小: {info['window_size']} 行")
    print(f"匹配位置: {info['start_position']}-{info['end_position']}")
    print(f"匹配到的代码片段:\n{full_window}")
    
    print(f"\n得分提升: {full_score - score:.4f}")


def documentation_matching_example():
    """文档匹配示例"""
    print("\n=== 文档匹配示例 ===")
    
    query_text = """如何使用Python处理文件？
需要打开文件、读取内容、处理数据。"""
    
    documentation = """Python文件操作指南

1. 文件打开
使用open()函数打开文件：
file = open('filename.txt', 'r')

2. 读取文件内容
可以使用read()、readline()或readlines()方法

3. 如何使用Python处理文件？
需要打开文件、读取内容、处理数据。
这是Python中常见的文件操作流程。

4. 文件写入
使用write()方法写入内容

5. 关闭文件
记得使用close()方法关闭文件"""
    
    # 使用工具函数进行分析
    result = analyze_text_similarity(query_text, documentation)
    
    print(f"最佳匹配得分: {result['comprehensive_matching']['score']:.4f}")
    print(f"检查了 {result['summary']['total_windows_checked']} 个窗口")
    print(f"匹配的文档片段:\n{result['comprehensive_matching']['window']}")


def code_similarity_comparison():
    """代码相似度比较示例"""
    print("\n=== 代码相似度比较示例 ===")
    
    original_function = """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)"""
    
    code_file = """import sys

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def prime_check(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

def main():
    print(fibonacci(10))
    print(factorial(5))"""
    
    # 查找最佳匹配
    matches = find_best_matches(original_function, code_file, top_k=3)
    
    print("前3个最佳匹配:")
    for match in matches:
        print(f"\n排名 {match['rank']}: 得分 {match['similarity_score']:.4f}")
        print(f"位置: {match['start_position']}-{match['end_position']}")
        print(f"匹配代码:\n{match['window_text']}")


def performance_comparison_example():
    """性能对比示例"""
    print("\n=== 性能对比示例 ===")
    
    import time
    
    # 创建较大的测试文本
    small_text = "def test():\n    return True"
    large_text = "\n".join([f"def function_{i}():\n    return {i}" for i in range(50)])
    
    similarity = TextSimilarity(small_text, large_text)
    
    # 测试基本匹配性能
    start_time = time.time()
    basic_score, basic_window = similarity.get_best_matching_window()
    basic_time = time.time() - start_time
    
    # 测试全面匹配性能
    start_time = time.time()
    full_score, full_window, info = similarity.get_best_matching_window_all_sizes()
    full_time = time.time() - start_time
    
    print(f"基本匹配:")
    print(f"  得分: {basic_score:.4f}")
    print(f"  时间: {basic_time:.4f} 秒")
    
    print(f"\n全面匹配:")
    print(f"  得分: {full_score:.4f}")
    print(f"  时间: {full_time:.4f} 秒")
    print(f"  检查窗口数: {info['total_windows_checked']}")
    
    print(f"\n性能对比:")
    print(f"  得分提升: {full_score - basic_score:.4f}")
    print(f"  时间比率: {full_time/basic_time:.2f}x")


def text_analysis_example():
    """文本分析示例"""
    print("\n=== 文本分析示例 ===")
    
    poem_verse = """春眠不觉晓
处处闻啼鸟"""
    
    full_poem = """春晓

春眠不觉晓
处处闻啼鸟
夜来风雨声
花落知多少

这是孟浩然的著名诗作
描写了春天清晨的美好景象"""
    
    # 获取详细统计信息
    similarity = TextSimilarity(poem_verse, full_poem)
    stats = similarity.get_statistics()
    
    print("文本统计信息:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 获取相似度矩阵
    matrix = similarity.get_similarity_matrix()
    print(f"\n相似度矩阵 ({len(matrix)}x{len(matrix[0])}):")
    for i, row in enumerate(matrix):
        print(f"  第{i+1}行: {[f'{val:.2f}' for val in row]}")


def integration_example():
    """集成应用示例"""
    print("\n=== 集成应用示例 ===")
    
    # 模拟代码搜索场景
    search_query = "处理用户输入验证"
    
    code_database = [
        ("user_validation.py", """def validate_user_input(data):
    if not data:
        return False
    # 处理用户输入验证
    return True"""),
        
        ("data_processing.py", """def process_data(input_data):
    cleaned = clean_data(input_data)
    return cleaned"""),
        
        ("auth_system.py", """def authenticate_user(username, password):
    # 用户身份验证
    if validate_credentials(username, password):
        return create_session(username)
    return None

def validate_credentials(username, password):
    # 处理用户输入验证
    return check_database(username, password)""")
    ]
    
    print(f"搜索查询: '{search_query}'")
    print("\n搜索结果:")
    
    results = []
    for filename, code in code_database:
        similarity = TextSimilarity(search_query, code)
        score, window = similarity.get_best_matching_window()
        results.append((filename, score, window))
    
    # 按相似度排序
    results.sort(key=lambda x: x[1], reverse=True)
    
    for i, (filename, score, window) in enumerate(results, 1):
        print(f"\n{i}. {filename} (相似度: {score:.4f})")
        print(f"   匹配片段: {window[:50]}...")


if __name__ == "__main__":
    """运行所有示例"""
    print("文本相似度模块使用示例\n")
    
    basic_usage_example()
    documentation_matching_example()
    code_similarity_comparison()
    performance_comparison_example()
    text_analysis_example()
    integration_example()
    
    print("\n=== 示例运行完成 ===")


