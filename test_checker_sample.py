"""
测试文件：用于测试代码检查功能

这个文件故意包含一些不规范的代码，用于测试检查器的功能
"""

def function_with_too_many_params(a, b, c, d, e, f, g, h):
    """参数过多的函数"""
    pass


def deeply_nested_function():
    """嵌套过深的函数"""
    if True:
        if True:
            if True:
                if True:
                    print("Too deep!")


class ClassWithoutDocstring:
    def method1(self):
        pass


def function_with_print():
    """使用 print 调试的函数"""
    print("Debug message")
    return 42


# 全局变量（可能违反规范）
GLOBAL_VAR = "test"


def function_without_type_hints(x, y):
    """没有类型注解的函数"""
    return x + y


try:
    something()
except:  # 裸 except（不推荐）
    pass
