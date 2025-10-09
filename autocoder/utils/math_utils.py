"""
简单的数学工具函数模块

提供基础的数学计算功能，包括：
- 计算两个数字的和
- 计算数字的平方
- 判断是否为偶数
- 计算阶乘
"""

from typing import Union


def add_numbers(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """
    计算两个数字的和
    
    Args:
        a: 第一个数字
        b: 第二个数字
        
    Returns:
        两个数字的和
        
    Examples:
        >>> add_numbers(2, 3)
        5
        >>> add_numbers(2.5, 3.7)
        6.2
    """
    return a + b


def square(x: Union[int, float]) -> Union[int, float]:
    """
    计算数字的平方
    
    Args:
        x: 要计算平方的数字
        
    Returns:
        x 的平方值
        
    Examples:
        >>> square(4)
        16
        >>> square(2.5)
        6.25
    """
    return x * x


def is_even(n: int) -> bool:
    """
    判断一个整数是否为偶数
    
    Args:
        n: 要判断的整数
        
    Returns:
        如果是偶数返回 True，否则返回 False
        
    Examples:
        >>> is_even(4)
        True
        >>> is_even(5)
        False
    """
    return n % 2 == 0


def factorial(n: int) -> int:
    """
    计算正整数的阶乘
    
    Args:
        n: 要计算阶乘的正整数
        
    Returns:
        n 的阶乘值
        
    Raises:
        ValueError: 当 n 为负数时抛出异常
        
    Examples:
        >>> factorial(5)
        120
        >>> factorial(0)
        1
    """
    if n < 0:
        raise ValueError("阶乘只能计算非负整数")
    
    if n == 0 or n == 1:
        return 1
    
    result = 1
    for i in range(2, n + 1):
        result *= i
    
    return result
