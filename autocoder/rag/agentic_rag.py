import json
import os
import time
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

import pathspec
from byzerllm import ByzerLLM
import byzerllm
from loguru import logger
import traceback

from autocoder.common import AutoCoderArgs, SourceCode
from importlib.metadata import version
from pydantic import BaseModel
from autocoder.common import openai_content as OpenAIContentProcessor
from autocoder.rag.long_context_rag import LongContextRAG
import json
import os
from autocoder.agent.base_agentic.base_agent import BaseAgent
from autocoder.agent.base_agentic.types import AgentRequest, AgenticEditConversationConfig
from autocoder.common import SourceCodeList
from autocoder.rag.tools import register_search_tool, register_recall_tool, register_todo_read_tool, register_todo_write_tool, register_web_search_tool, register_web_crawl_tool
from byzerllm.utils.types import SingleOutputMeta
import uuid

class RAGAgent(BaseAgent):
    def __init__(self, name: str,
                 llm: Union[byzerllm.ByzerLLM, byzerllm.SimpleByzerLLM],
                 files: SourceCodeList,
                 args: AutoCoderArgs,
                 rag: LongContextRAG,
                 conversation_history: Optional[List[Dict[str, Any]]] = None,
                 custom_system_prompt: Optional[str] = None,
                 conversation_config: Optional[Any] = None,
                 cancel_token: Optional[str] = None):

        if conversation_config is None:
            conversation_config = AgenticEditConversationConfig(
                conversation_name=f"rag_session_{uuid.uuid4().hex[:8]}",
                conversation_id=str(uuid.uuid4())
            )

        self.llm = llm
        self.default_llm = self.llm
        self.context_prune_llm = self.default_llm
        if self.default_llm.get_sub_client("context_prune_model"):
            self.context_prune_llm = self.default_llm.get_sub_client(
                "context_prune_model")

        self.llm = self.default_llm
        if self.default_llm.get_sub_client("agentic_model"):
            self.llm = self.default_llm.get_sub_client("agentic_model")

        self.rag = rag
        super().__init__(
            name=name,
            llm=self.llm,
            files=files,
            args=args,
            conversation_history=conversation_history,
            default_tools_list=["read_file"],
            custom_system_prompt=custom_system_prompt,
            conversation_config=conversation_config,
            cancel_token=cancel_token
        )
        # 注册RAG工具
        # register_search_tool()
        register_recall_tool()
        register_todo_read_tool()
        register_todo_write_tool()

        # 如果配置了firecrawl_api_key，则注册web_search_tool和web_crawl_tool
        if self.args.firecrawl_api_key or self.args.metaso_api_key or self.args.bochaai_api_key:            
            logger.info(f"firecrawl_api_key or metaso_api_key or bochaai_api_key is configured, register web_search_tool and web_crawl_tool")
            register_web_search_tool()
            register_web_crawl_tool()


class AgenticRAG:
    def __init__(
        self,
        llm: ByzerLLM,
        args: AutoCoderArgs,
        path: str,
        tokenizer_path: Optional[str] = None,
    ) -> None:
        self.llm = llm
        self.args = args
        self.path = path
        self.tokenizer_path = tokenizer_path
        self.rag = LongContextRAG(
            llm=self.llm, args=self.args, path=self.path, tokenizer_path=self.tokenizer_path)

    def build(self):
        pass

    def search(self, query: str) -> List[SourceCode]:
        return []

    def stream_chat_oai(
        self,
        conversations,
        model: Optional[str] = None,
        role_mapping=None,
        llm_config: Dict[str, Any] = {},
        extra_request_params: Dict[str, Any] = {}
    ):
        try:
            return self._stream_chat_oai(
                conversations,
                model=model,
                role_mapping=role_mapping,
                llm_config=llm_config,
                extra_request_params=extra_request_params
            )
        except Exception as e:
            logger.error(f"Error in stream_chat_oai: {str(e)}")
            traceback.print_exc()
            return ["出现错误，请稍后再试。"], []

    @byzerllm.prompt()
    def conversation_to_query(self, messages: List[Dict[str, Any]]):
        '''        
        【历史对话】按时间顺序排列，从旧到新：
        {% for message in messages %}
        <message>
        {% if message.role == "user" %}【用户】{% else %}【助手】{% endif %}    
        <content>
        {{ message.content }}
        </content>
        </message>
        {% endfor %}

        【当前问题】用户的最新需求如下:
        <current_query>
        {{ query }}
        </current_query>            
        '''
        temp_messages = messages[0:-1]
        message = messages[-1]

        return {
            "messages": temp_messages,
            "query": message["content"]
        }

    @byzerllm.prompt()
    def system_prompt(self):
        '''
        You are an intelligent assistant based on a knowledge base. My core capability is to answer user questions through Retrieval-Augmented Generation (RAG) technology.

        Your workflow is as follows:
        1. When users ask questions, you first understand the core intent and key information needs of the question
        2. For complex questions, you MUST use TODO tools to manage the analysis and retrieval process
        3. You analyze the question from multiple angles, determine the best retrieval strategy and keywords, then use the recall tool to get the most relevant detailed content
        4. If the obtained information is sufficient to answer the user's question, you will generate an answer directly
        5. If the obtained information is insufficient, you will continue using the recall tool until you have obtained enough information

        ## IMPORTANT: All Complex Questions MUST Use TODO Files

        For ANY complex question that requires multiple steps, comparisons, or process tracing, you MUST use TODO tools to manage the work:

        ### Example 1: Comparison Questions
        User question: "What are the differences between the implementation methods of the user authentication module and the permission management module in the system?"

        **MANDATORY Processing with TODO:**

        1. **First create TODO list**:
        ```
        <todo_write>
        <action>create</action>
        <content>
        <task>Retrieve and analyze user authentication module implementation details</task>
        <task>Retrieve and analyze permission management module implementation details</task>
        <task>Compare architecture design between the two modules</task>
        <task>Compare technology selection and patterns used</task>
        <task>Synthesize findings into comprehensive comparison</task>
        </content>
        <priority>high</priority>
        </todo_write>
        ```

        2. **Execute with TODO tracking**:
        - Check todo_read before starting
        - Mark first todo as in_progress
        - Use recall("user authentication login token") for authentication info
        - Mark first todo as completed with notes
        - Mark second todo as in_progress
        - Use recall("permission management authorization role RBAC") for permission info
        - Mark second todo as completed
        - Continue through all todos systematically

        3. **Complete analysis**: After all todos are marked completed, provide comprehensive comparison

        ### Example 2: Process Tracing Questions
        User question: "What is the entire process from user login to order completion? Which modules and interfaces are involved?"

        **MANDATORY Processing with TODO:**

        1. **First create TODO list**:
        ```
        <todo_write>
        <action>create</action>
        <content>
        <task>Trace and document user login process and entry points</task>
        <task>Analyze session management and token verification flow</task>
        <task>Map order creation process and required data</task>
        <task>Track order processing workflow and state transitions</task>
        <task>Identify payment integration and completion mechanisms</task>
        <task>Document all involved modules and interfaces</task>
        <task>Create end-to-end process summary</task>
        </content>
        <priority>high</priority>
        </todo_write>
        ```

        2. **Execute with TODO tracking**:
        - Use todo_read to check current status
        - For each todo: mark as in_progress → execute recalls → mark as completed
        - Use recall for each process step (login, session, order, payment)
        - Add new todos if additional steps are discovered
        - Document findings in todo notes

        3. **Synthesize results**: Once all todos completed, organize the complete business flow

        ### When TODO Files are MANDATORY:

        **You MUST use TODO files for:**
        - Any question requiring comparison between multiple items
        - Process tracing or workflow analysis questions
        - Questions with "step by step", "entire process", or "all involved" keywords
        - Multi-part questions that need systematic investigation
        - Questions about relationships between different components
        - Any analysis requiring more than 3 recall operations

        ### TODO Tool Usage Rules:

        1. **Always start complex questions with todo_write**: Create a comprehensive plan BEFORE any recall
        2. **Use todo_read before each major step**: Maintain awareness of progress
        3. **Mark todos systematically**: in_progress → completed with notes
        4. **Add discovered todos**: Use action="add_task" when finding new aspects to investigate
        5. **Document in notes**: Record key findings, blockers, or important information

        ### Tool Usage Principles:
        - **todo_write/todo_read**: MANDATORY for all complex questions - use FIRST before any recalls
        - **recall tool**: Primary tool for information retrieval after TODO planning
        - **read_file tool**: Only when specific file details are needed beyond recall results
        - **Iterative approach**: Adjust keywords and add todos based on findings

        ### Remember:
        This is a RAG system focused on information retrieval and synthesis. We do not modify code or files, we only retrieve and analyze information to answer questions. TODO tools help organize complex retrieval tasks systematically.

        8. When you encounter images, please infer the relevance of the image to the question based on the surrounding text content. If relevant, output the Markdown image path using ![]() format in your answer; otherwise, do not output it.
        {% if local_image_host %}
        9. Image path processing
        - Image addresses need to return absolute paths
        - For Windows-style paths, convert to Linux-style, for example: ![image](C:\\Users\\user\\Desktop\\image.png) converts to ![image](C:/Users/user/Desktop/image.png)
        - To request image resources, add http://{{ local_image_host }}/static/ as a prefix
        For example: ![image](/path/to/images/image.png), return ![image](http://{{ local_image_host }}/static/path/to/images/image.png)
        {% endif %} 
        '''
        return {
            "local_image_host": self.args.local_image_host
        }

    def _stream_chat_oai(
        self,
        conversations,
        model: Optional[str] = None,
        role_mapping=None,
        llm_config: Dict[str, Any] = {},
        extra_request_params: Dict[str, Any] = {}
    ):
        if not llm_config:
            llm_config = {}

        if extra_request_params:
            llm_config.update(extra_request_params)

        conversations = OpenAIContentProcessor.process_conversations(
            conversations)

        context = []

        def _generate_sream():
            # 提取最后一个 user 消息和对话历史
            last_user_message = None
            conversation_history = []

            # 从后往前查找最后一个 role="user" 的消息
            for i in range(len(conversations) - 1, -1, -1):
                if conversations[i].get("role") == "user":
                    last_user_message = conversations[i]["content"]
                    # 将之前的所有消息作为历史记录（不包括最后一个user消息）
                    conversation_history = conversations[:i]
                    break

            # 如果没有找到 user 消息，使用默认处理
            if last_user_message is None:
                last_user_message = self.conversation_to_query.prompt(
                    conversations)
                conversation_history = []

            recall_request = AgentRequest(user_input=last_user_message)

            # 为每个RAGAgent实例创建新的conversation_config
            conversation_config = AgenticEditConversationConfig(
                conversation_name=f"rag_session_{uuid.uuid4().hex[:8]}",
                conversation_id=str(uuid.uuid4())
            )

            rag_agent = RAGAgent(
                name="RAGAgent",
                llm=self.llm,
                files=SourceCodeList(sources=[]),
                args=self.args,
                rag=self.rag,
                conversation_history=conversation_history,
                custom_system_prompt=None,
                conversation_config=conversation_config,
                cancel_token=None
            )

            rag_agent.who_am_i(self.system_prompt.prompt())

            events = rag_agent.run_with_generator(recall_request)
            for (t, content) in events:
                if t == "thinking":
                    yield ("", SingleOutputMeta(
                        generated_tokens_count=0,
                        input_tokens_count=0,
                        reasoning_content=content,
                    ))
                else:
                    yield (content, SingleOutputMeta(
                        generated_tokens_count=0,
                        input_tokens_count=0,
                        reasoning_content="",
                    ))

        return _generate_sream(), context
    
    def close(self):
        self.rag.close()
