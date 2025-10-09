
"""
Text Similarity Utilities

提供文本相似度计算的辅助工具函数。
"""

from typing import List, Tuple, Dict, Any
from .text_similarity import TextSimilarity


def compare_texts_simple(text_a: str, text_b: str) -> Dict[str, Any]:
    """
    简单的文本比较函数
    
    Args:
        text_a: 第一个文本
        text_b: 第二个文本
        
    Returns:
        包含比较结果的字典
    """
    similarity = TextSimilarity(text_a, text_b)
    
    # 获取基本匹配结果
    basic_score, basic_window = similarity.get_best_matching_window()
    
    # 获取全面匹配结果
    full_score, full_window, full_info = similarity.get_best_matching_window_all_sizes()
    
    # 获取统计信息
    stats = similarity.get_statistics()
    
    return {
        "basic_matching": {
            "score": basic_score,
            "window": basic_window
        },
        "comprehensive_matching": {
            "score": full_score,
            "window": full_window,
            "details": full_info
        },
        "statistics": stats
    }


def find_best_matches(text_a: str, text_b: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    查找最佳匹配的前K个结果
    
    Args:
        text_a: 源文本
        text_b: 目标文本
        top_k: 返回前K个最佳匹配
        
    Returns:
        匹配结果列表，按相似度降序排列
    """
    similarity = TextSimilarity(text_a, text_b)
    window_similarities = similarity.get_window_similarities()
    
    results = []
    for i, (start_pos, score, window_text) in enumerate(window_similarities[:top_k]):
        results.append({
            "rank": i + 1,
            "start_position": start_pos,
            "end_position": start_pos + similarity.m,
            "similarity_score": score,
            "window_text": window_text
        })
    
    return results


def analyze_text_similarity(text_a: str, text_b: str) -> Dict[str, Any]:
    """
    全面分析两个文本的相似度
    
    Args:
        text_a: 第一个文本
        text_b: 第二个文本
        
    Returns:
        详细的相似度分析结果
    """
    similarity = TextSimilarity(text_a, text_b)
    
    # 基本信息
    stats = similarity.get_statistics()
    
    # 基本窗口匹配
    basic_score, basic_window = similarity.get_best_matching_window()
    
    # 全面窗口匹配
    full_score, full_window, full_info = similarity.get_best_matching_window_all_sizes()
    
    # 相似度矩阵
    matrix = similarity.get_similarity_matrix()
    
    # 前5个最佳匹配
    top_matches = find_best_matches(text_a, text_b, 5)
    
    return {
        "summary": {
            "basic_best_score": basic_score,
            "comprehensive_best_score": full_score,
            "improvement": full_score - basic_score,
            "total_windows_checked": full_info.get("total_windows_checked", 0)
        },
        "basic_matching": {
            "score": basic_score,
            "window": basic_window
        },
        "comprehensive_matching": {
            "score": full_score,
            "window": full_window,
            "details": full_info
        },
        "top_matches": top_matches,
        "statistics": stats,
        "similarity_matrix_shape": (len(matrix), len(matrix[0]) if matrix else 0)
    }


