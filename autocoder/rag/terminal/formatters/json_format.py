"""
JSON 格式化器

一次性输出完整的 JSON 结果，包含答案、上下文、处理阶段和元数据。
"""

import json
from .base import detect_stage_from_reasoning


class JSONFormatter:
    """JSON格式化器：收集所有内容后一次性输出完整的JSON"""

    def format(self, result_generator, contexts):
        """
        格式化为JSON输出

        Args:
            result_generator: 生成器，产生 (chunk, meta) 元组
            contexts: 上下文文档列表
        """
        answer = ""
        stages = []
        final_metadata = {}
        current_stage_type = None

        for chunk, meta in result_generator:
            # 收集答案内容
            answer += chunk

            # 收集元数据
            if meta:
                final_metadata = {
                    "input_tokens": meta.input_tokens_count,
                    "generated_tokens": meta.generated_tokens_count,
                    "finish_reason": meta.finish_reason,
                }

                # 收集中间处理步骤（从 reasoning_content）
                if meta.reasoning_content:
                    stage_type = detect_stage_from_reasoning(meta.reasoning_content)

                    # 避免重复记录相同阶段
                    if stage_type != current_stage_type:
                        stages.append(
                            {
                                "type": stage_type,
                                "message": meta.reasoning_content,
                                "tokens": {
                                    "input": meta.input_tokens_count,
                                    "generated": meta.generated_tokens_count,
                                },
                            }
                        )
                        current_stage_type = stage_type

        # 构建完整的结果
        result = {
            "answer": answer,
            "contexts": contexts,
            "stages": stages,
            "metadata": final_metadata,
        }

        # 一次性输出JSON
        print(json.dumps(result, ensure_ascii=False, indent=2))
