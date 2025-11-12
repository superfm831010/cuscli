"""
流式 JSON 格式化器

实时输出每个处理步骤的 JSON 事件，适合前端集成和实时进度显示。
"""

import json
from datetime import datetime
from .base import detect_stage_from_reasoning


class StreamJSONFormatter:
    """流式JSON格式化器：实时输出每个事件为一行JSON"""

    def format(self, result_generator, contexts):
        """
        格式化为流式JSON输出

        每个事件输出一行JSON，格式：
        {"event_type": "...", "data": {...}, "timestamp": "..."}

        Args:
            result_generator: 生成器，产生 (chunk, meta) 元组
            contexts: 上下文文档列表
        """
        current_stage_type = None
        final_metadata = {}

        # 1. 发送开始事件
        self._emit_event("start", {"status": "started"})

        try:
            # 2. 处理每个chunk和meta
            for chunk, meta in result_generator:
                # 处理元数据中的中间步骤信息
                if meta:
                    # 更新最终元数据
                    final_metadata = {
                        "input_tokens": meta.input_tokens_count,
                        "generated_tokens": meta.generated_tokens_count,
                        "finish_reason": meta.finish_reason,
                    }

                    # 处理 reasoning_content（各个处理阶段）
                    if meta.reasoning_content:
                        stage_type = detect_stage_from_reasoning(meta.reasoning_content)

                        # 避免重复发送相同阶段（但message不同时也要发送）
                        if (
                            stage_type != current_stage_type
                            or meta.reasoning_content.strip()
                        ):
                            self._emit_event(
                                "stage",
                                {
                                    "type": stage_type,
                                    "message": meta.reasoning_content,
                                    "tokens": {
                                        "input": meta.input_tokens_count,
                                        "generated": meta.generated_tokens_count,
                                    },
                                },
                            )
                            current_stage_type = stage_type

                # 处理实际的答案内容
                if chunk:
                    self._emit_event("content", {"content": chunk})

            # 3. 发送上下文信息
            if contexts:
                self._emit_event("contexts", {"contexts": contexts})

            # 4. 发送结束事件（包含最终元数据）
            self._emit_event("end", {"status": "completed", "metadata": final_metadata})

        except Exception as e:
            # 发送错误事件
            self._emit_event("error", {"error": str(e)})
            raise

    def _emit_event(self, event_type: str, data: dict):
        """
        输出单个事件（一行JSON）

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        event = {
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(event, ensure_ascii=False), flush=True)
