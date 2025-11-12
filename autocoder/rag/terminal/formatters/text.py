"""
文本格式化器

纯文本输出，只输出最终答案，适合人类阅读和管道传递。
"""


class TextFormatter:
    """文本格式化器：只输出答案内容，不包含中间步骤"""

    def format(self, result_generator, contexts):
        """
        格式化为纯文本输出

        Args:
            result_generator: 生成器，产生 (chunk, meta) 元组
            contexts: 上下文文档列表（在text格式中不输出）
        """
        for chunk, meta in result_generator:
            # 只输出实际的答案内容（chunk）
            # 忽略 meta.reasoning_content（中间处理步骤）
            if meta.reasoning_content:
                print(meta.reasoning_content, end="", flush=True)
            if chunk:
                print(chunk, end="", flush=True)

        # 输出完成后换行
        print()
