import pytest
import os
import shutil
import tempfile
from loguru import logger
from pathlib import Path
import time
import json
from typing import Dict, Any, List, Optional

# 导入被测模块
from autocoder.rag.token_limiter import TokenLimiter
from autocoder.common import AutoCoderArgs, SourceCode
from autocoder.rag.long_context_rag import RAGStat, RecallStat, ChunkStat, AnswerStat
from byzerllm.utils.types import SingleOutputMeta

# 1. 初始化FileMonitor（必须最先进行）
@pytest.fixture(scope="function")
def setup_file_monitor(temp_test_dir):
    """初始化FileMonitor，必须最先执行"""
    try:
        from autocoder.common.file_monitor.monitor import FileMonitor
        monitor = FileMonitor(temp_test_dir)
        monitor.reset_instance()
        if not monitor.is_running():
            monitor.start()
            logger.info(f"文件监控已启动: {temp_test_dir}")
        else:
            logger.info(f"文件监控已在运行中: {monitor.root_dir}")
    except Exception as e:
        logger.error(f"初始化文件监控出错: {e}")
    
    # 2. 加载规则文件
    try:
        from autocoder.common.rulefiles import get_rules, reset_rules_manager
        reset_rules_manager()
        rules = get_rules(temp_test_dir)
        logger.info(f"已加载规则: {len(rules)} 条")
    except Exception as e:
        logger.error(f"加载规则出错: {e}")
    
    return temp_test_dir

# Pytest Fixture: 临时测试目录
@pytest.fixture(scope="function")
def temp_test_dir():
    """提供一个临时的、测试后自动清理的目录"""
    temp_dir = tempfile.mkdtemp()
    logger.info(f"创建测试临时目录: {temp_dir}")
    yield temp_dir
    logger.info(f"清理测试临时目录: {temp_dir}")
    shutil.rmtree(temp_dir)

# Pytest Fixture: 测试文件结构
@pytest.fixture(scope="function")
def test_files(temp_test_dir):
    """创建测试所需的文件/目录结构"""
    # 创建示例文件
    file_structure = {
        "docs/guide.md": "# TokenLimiter 使用指南\n使用TokenLimiter可以控制文档分块和令牌限制。",
        "docs/api.md": "# API说明\n## 初始化\n```python\nlimiter = TokenLimiter(count_tokens, full_text_limit, segment_limit, buff_limit, llm)\n```",
        "src/example.py": "def add(a, b):\n    return a + b\n\ndef subtract(a, b):\n    return a - b",
        "src/utils/helpers.py": "def format_text(text):\n    return text.strip()\n\ndef count_words(text):\n    return len(text.split())",
        ".gitignore": "*.log\n__pycache__/\n.cache/",
        ".autocoderignore": "*.log\n__pycache__/\n.cache/"
    }
    
    for file_path, content in file_structure.items():
        full_path = os.path.join(temp_test_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return temp_test_dir

# Pytest Fixture: 配置参数
@pytest.fixture
def test_args():
    """创建测试用配置参数"""
    return AutoCoderArgs(
        source_dir=".",
        context_prune=True,
        context_prune_strategy="extract",
        conversation_prune_safe_zone_tokens=400,
        context_prune_sliding_window_size=10,
        context_prune_sliding_window_overlap=2,
        rag_context_window_limit=8000,
        rag_doc_filter_relevance=3,
        full_text_ratio=0.7,
        segment_ratio=0.2,
        index_filter_workers=1,
        required_exts=".py,.md",
        monitor_mode=False,
        enable_hybrid_index=False,
        disable_segment_reorder=False
    )

# 3. 加载tokenizer (必须在FileMonitor和rules初始化之后)
@pytest.fixture
def load_tokenizer_fixture(setup_file_monitor):
    """加载tokenizer，必须在FileMonitor和rules初始化之后"""
    from autocoder.auto_coder_runner import load_tokenizer
    load_tokenizer()
    logger.info("Tokenizer加载完成")
    return True

# 4. 初始化LLM
@pytest.fixture
def real_llm(load_tokenizer_fixture):
    """创建真实的LLM对象，必须在tokenizer加载之后"""
    from autocoder.utils.llms import get_single_llm
    llm = get_single_llm("v3_chat", product_mode="lite")
    logger.info(f"LLM初始化完成: {llm.default_model_name}")
    return llm

# 5. TokenCounter实例
@pytest.fixture
def token_counter(load_tokenizer_fixture):
    """创建TokenCounter实例"""
    from autocoder.rag.token_counter import TokenCounter
    from autocoder.rag.variable_holder import VariableHolder
    
    tokenizer_path = None
    if hasattr(VariableHolder, "TOKENIZER_PATH") and VariableHolder.TOKENIZER_PATH:
        tokenizer_path = VariableHolder.TOKENIZER_PATH
        return TokenCounter(tokenizer_path)
    
    # 如果没有可用的tokenizer_path，使用RemoteTokenCounter
    from autocoder.rag.token_counter import RemoteTokenCounter
    from byzerllm import ByzerLLM
    
    tokenizer_llm = ByzerLLM()
    if tokenizer_llm.is_model_exist("deepseek_tokenizer"):
        tokenizer_llm.setup_default_model_name("deepseek_tokenizer")
        return RemoteTokenCounter(tokenizer_llm)
    
    pytest.skip("没有可用的tokenizer，跳过测试")

# 6. TokenLimiter实例
@pytest.fixture
def token_limiter(real_llm, token_counter, test_args):
    """创建TokenLimiter实例"""
    from autocoder.rag.token_limiter import TokenLimiter
    
    full_text_limit = int(test_args.rag_context_window_limit * test_args.full_text_ratio)
    segment_limit = int(test_args.rag_context_window_limit * test_args.segment_ratio)
    buff_limit = int(test_args.rag_context_window_limit * (1 - test_args.full_text_ratio - test_args.segment_ratio))
    
    limiter = TokenLimiter(
        count_tokens=token_counter.count_tokens,
        full_text_limit=full_text_limit,
        segment_limit=segment_limit,
        buff_limit=buff_limit,
        llm=real_llm,
        disable_segment_reorder=test_args.disable_segment_reorder
    )
    
    return limiter

# --- 测试用例 ---

def test_limit_tokens_basic(token_limiter, test_files):
    """测试TokenLimiter的基本功能"""
    # 创建测试文档
    relevant_docs = [
        SourceCode(
            module_name=os.path.join(test_files, "docs/guide.md"),
            source_code="# TokenLimiter 使用指南\n使用TokenLimiter可以控制文档分块和令牌限制。"
        ),
        SourceCode(
            module_name=os.path.join(test_files, "docs/api.md"),
            source_code="# API说明\n## 初始化\n```python\nlimiter = TokenLimiter(count_tokens, full_text_limit, segment_limit, buff_limit, llm)\n```"
        )
    ]
    
    # 创建对话
    conversations = [{"role": "user", "content": "如何使用TokenLimiter进行文档分块?"}]
    
    # 执行令牌限制
    result = token_limiter.limit_tokens(
        relevant_docs=relevant_docs,
        conversations=conversations,
        index_filter_workers=1
    )
    
    # 验证结果
    assert result is not None, "应该返回结果"
    assert hasattr(result, "docs"), "结果应该包含文档"
    assert len(result.docs) > 0, "应该至少返回一个文档"
    assert hasattr(result, "input_tokens_counts"), "结果应该包含输入token计数"
    assert hasattr(result, "generated_tokens_counts"), "结果应该包含生成token计数"
    
    # 检查是否有第一轮全文文档
    assert hasattr(token_limiter, "first_round_full_docs"), "应该有first_round_full_docs属性"
    
    # 检查是否有第二轮提取文档
    assert hasattr(token_limiter, "second_round_extracted_docs"), "应该有second_round_extracted_docs属性"
    
    # 打印测试结果详情
    logger.info("="*80)
    logger.info("TokenLimiter基本功能测试结果:")
    logger.info("-"*80)
    logger.info(f"输入文档数: {len(relevant_docs)}")
    logger.info(f"输出文档数: {len(result.docs)}")
    logger.info(f"第一轮全文文档数: {len(token_limiter.first_round_full_docs)}")
    logger.info(f"第二轮提取文档数: {len(token_limiter.second_round_extracted_docs)}")
    logger.info(f"输入token计数: {result.input_tokens_counts}")
    logger.info(f"生成token计数: {result.generated_tokens_counts}")
    logger.info("="*80)

def test_limit_tokens_with_large_docs(token_limiter, test_files):
    """测试TokenLimiter处理大文档的能力"""
    # 创建一个大的测试文档
    large_content = "# 大文档测试\n\n" + "这是一个很长的文档。" * 100
    
    relevant_docs = [
        SourceCode(
            module_name=os.path.join(test_files, "docs/large_doc.md"),
            source_code=large_content
        ),
        SourceCode(
            module_name=os.path.join(test_files, "docs/guide.md"),
            source_code="# TokenLimiter 使用指南\n使用TokenLimiter可以控制文档分块和令牌限制。"
        )
    ]
    
    # 创建对话
    conversations = [{"role": "user", "content": "如何处理大型文档?"}]
    
    # 执行令牌限制
    result = token_limiter.limit_tokens(
        relevant_docs=relevant_docs,
        conversations=conversations,
        index_filter_workers=1
    )
    
    # 验证结果
    assert result is not None, "应该返回结果"
    assert len(result.docs) > 0, "应该至少返回一个文档"
    
    # 检查所有文档的总令牌数是否低于限制
    total_tokens = sum([
        token_limiter.count_tokens(doc.source_code) for doc in result.docs
    ])
    total_limit = token_limiter.full_text_limit + token_limiter.segment_limit + token_limiter.buff_limit
    
    assert total_tokens <= total_limit, f"总令牌数({total_tokens})应该不超过限制({total_limit})"
    
    # 打印测试结果详情
    logger.info("="*80)
    logger.info("TokenLimiter处理大文档测试结果:")
    logger.info("-"*80)
    logger.info(f"输入文档数: {len(relevant_docs)}")
    logger.info(f"输出文档数: {len(result.docs)}")
    logger.info(f"总令牌数: {total_tokens}")
    logger.info(f"总限制: {total_limit}")
    logger.info(f"第一轮全文文档数: {len(token_limiter.first_round_full_docs)}")
    logger.info(f"第二轮提取文档数: {len(token_limiter.second_round_extracted_docs)}")
    logger.info("="*80)

def test_limit_tokens_integration(token_limiter, token_counter, real_llm, test_args, test_files):
    """集成测试：模拟LongContextRAG中的_process_document_chunking调用，构建触发第二轮处理的案例"""
    
    # 分析token限制配置
    # full_text_limit = 8000 * 0.7 = 5600
    # segment_limit = 8000 * 0.2 = 1600  
    # 第一轮总限制 = 5600 + 1600 = 7200 tokens
    # 我们需要创建总量超过7200 tokens的文档来触发第二轮处理
    
    # 创建大型测试文档 - 每个文档预计约2000-3000 tokens
    large_content_1 = """# TokenLimiter 详细使用指南

## 概述
TokenLimiter是一个强大的文档处理工具，专门用于控制和管理大规模文档的分块和令牌限制。它采用了先进的分级处理策略，能够有效地处理各种规模的文档集合。

## 核心功能

### 1. 文档分级处理
TokenLimiter采用两轮处理机制：
- 第一轮：全文装载阶段，将文档直接装载到指定的令牌限制内
- 第二轮：智能分块阶段，对剩余文档进行LLM驱动的相关内容提取

### 2. 令牌限制管理
系统支持多种令牌限制配置：
- full_text_limit: 全文区域的令牌限制
- segment_limit: 分段区域的令牌限制  
- buff_limit: 缓冲区域的令牌限制

### 3. 智能重排序
为了减少大模型幻觉，系统会对文档片段进行智能重排序：
- 识别来自同一文档的不同片段
- 根据原文顺序重新排列片段
- 确保文档的连贯性和逻辑性

## 使用示例

```python
# 初始化TokenLimiter
from autocoder.rag.token_limiter import TokenLimiter

limiter = TokenLimiter(
    count_tokens=token_counter,
    full_text_limit=5600,
    segment_limit=1600,
    buff_limit=800,
    llm=llm_instance,
    disable_segment_reorder=False
)

# 执行令牌限制处理
result = limiter.limit_tokens(
    relevant_docs=document_list,
    conversations=conversation_history,
    index_filter_workers=4
)
```

## 高级特性

### 并发处理
TokenLimiter支持多线程并发处理，显著提升处理效率：
- 可配置工作线程数量
- 智能任务分配和负载均衡
- 实时进度监控和状态报告

### 元数据管理  
系统会自动记录和管理各种元数据：
- 处理时间统计
- 令牌使用情况
- 文档处理状态
- 错误和异常信息

### 灵活配置
支持多种配置选项来适应不同的使用场景：
- 自定义令牌计数函数
- 可调节的处理策略
- 灵活的重排序控制
- 丰富的日志输出

这个工具特别适用于需要处理大量文档的RAG（检索增强生成）系统，能够有效地平衡处理效率和结果质量。
""" * 3  # 重复3次以确保足够大

    large_content_2 = """# API 详细说明文档

## TokenLimiter 类

### 构造函数
```python
def __init__(
    self,
    count_tokens: Callable[[str], int],
    full_text_limit: int,
    segment_limit: int, 
    buff_limit: int,
    llm: ByzerLLM,
    disable_segment_reorder: bool,
):
```

#### 参数说明
- `count_tokens`: 令牌计数函数，用于统计文档的令牌数量
- `full_text_limit`: 全文区域的最大令牌限制
- `segment_limit`: 分段区域的最大令牌限制
- `buff_limit`: 缓冲区域的最大令牌限制
- `llm`: ByzerLLM实例，用于执行智能分块提取
- `disable_segment_reorder`: 是否禁用段落重排序功能

### 核心方法

#### limit_tokens
```python
def limit_tokens(
    self,
    relevant_docs: List[SourceCode],
    conversations: List[Dict[str, str]],
    index_filter_workers: int,
) -> TokenLimiterResult:
```

这是TokenLimiter的核心方法，执行文档的令牌限制处理。

##### 处理流程
1. **文档重排序阶段**
   - 分析文档元数据
   - 识别同源文档片段
   - 按原文顺序重新排列

2. **第一轮处理阶段**
   - 按令牌限制装载文档
   - 优先处理高相关性文档
   - 记录装载统计信息

3. **第二轮处理阶段**（如需要）
   - 并发处理剩余文档
   - LLM驱动的相关内容提取
   - 智能分块和优化

##### 返回值
返回TokenLimiterResult对象，包含：
- `docs`: 最终处理后的文档列表
- `raw_docs`: 原始文档列表
- `input_tokens_counts`: 输入令牌计数列表
- `generated_tokens_counts`: 生成令牌计数列表
- `durations`: 处理时间列表
- `model_name`: 使用的模型名称

### 内部方法

#### extract_relevance_range_from_docs_with_conversation
使用LLM分析对话历史和文档内容，提取相关信息范围。

#### process_range_doc
处理单个文档的分块提取，支持重试机制和错误处理。

## 最佳实践

### 性能优化
- 合理设置工作线程数量
- 根据文档规模调整令牌限制
- 启用文档重排序以提高质量

### 错误处理
- 实现适当的重试机制
- 监控处理异常和错误
- 记录详细的日志信息

### 内存管理
- 及时释放不需要的文档对象
- 控制并发处理的内存使用
- 优化大文档的处理策略
""" * 2  # 重复2次

    large_content_3 = """# 实际应用案例和最佳实践

## 案例1：大规模代码库分析
在处理大型代码库时，TokenLimiter能够有效地管理代码文件的令牌使用：

```python
# 处理Python代码库
code_docs = load_python_files("./src")
result = limiter.limit_tokens(
    relevant_docs=code_docs,
    conversations=[{"role": "user", "content": "分析这个代码库的架构"}],
    index_filter_workers=8
)
```

## 案例2：文档问答系统  
在构建文档问答系统时，合理的令牌管理至关重要：

```python
# 处理技术文档
doc_collection = load_markdown_docs("./docs")
qa_result = limiter.limit_tokens(
    relevant_docs=doc_collection,
    conversations=conversation_history,
    index_filter_workers=4
)
```

## 性能基准测试
基于不同规模的文档集合进行的性能测试表明：
- 小型文档集（< 1000 tokens）：平均处理时间 < 100ms
- 中型文档集（1000-10000 tokens）：平均处理时间 < 500ms  
- 大型文档集（> 10000 tokens）：需要启用第二轮处理，时间依赖于LLM响应速度

## 故障排除指南

### 常见问题
1. 处理时间过长：检查LLM响应速度，调整并发参数
2. 内存使用过高：减少工作线程数，优化文档预处理
3. 结果质量不佳：启用文档重排序，调整令牌限制策略

### 调试技巧
- 启用详细日志输出
- 监控各阶段的处理时间
- 分析令牌使用统计
- 检查文档重排序效果
""" * 2  # 重复2次

    # 创建多个大文档来确保触发第二轮处理
    relevant_docs = [
        SourceCode(
            module_name=os.path.join(test_files, "docs/comprehensive_guide.md"),
            source_code=large_content_1
        ),
        SourceCode(
            module_name=os.path.join(test_files, "docs/api_reference.md"),
            source_code=large_content_2
        ),
        SourceCode(
            module_name=os.path.join(test_files, "docs/best_practices.md"),
            source_code=large_content_3
        ),
        SourceCode(
            module_name=os.path.join(test_files, "docs/tutorial.md"),
            source_code="# TokenLimiter 教程\n\n" + "这是一个详细的使用教程。" * 200
        ),
        SourceCode(
            module_name=os.path.join(test_files, "docs/examples.md"),
            source_code="# 代码示例\n\n" + "```python\n# 示例代码\nprint('Hello World')\n```\n\n" * 150
        )
    ]
    
    # 创建对话
    conversations = [{"role": "user", "content": "如何使用TokenLimiter?"}]
    
    # 准备RAG统计数据
    rag_stat = RAGStat(
        recall_stat=RecallStat(
            total_input_tokens=10,  # 假设已有一些token
            total_generated_tokens=5,
            model_name=real_llm.default_model_name,
        ),
        chunk_stat=ChunkStat(
            total_input_tokens=0,
            total_generated_tokens=0,
            model_name=real_llm.default_model_name,
        ),
        answer_stat=AnswerStat(
            total_input_tokens=0,
            total_generated_tokens=0,
            model_name=real_llm.default_model_name,
        ),
    )
    
    # 模拟_process_document_chunking的处理逻辑
    first_round_full_docs = []
    second_round_extracted_docs = []
    sencond_round_time = 0
    
    start_time = time.time()
    token_limiter_result = token_limiter.limit_tokens(
        relevant_docs=relevant_docs,
        conversations=conversations,
        index_filter_workers=test_args.index_filter_workers or 1,
    )
    sencond_round_time = time.time() - start_time
    
    # 更新统计信息
    rag_stat.chunk_stat.total_input_tokens += sum(token_limiter_result.input_tokens_counts)
    rag_stat.chunk_stat.total_generated_tokens += sum(token_limiter_result.generated_tokens_counts)
    rag_stat.chunk_stat.model_name = token_limiter_result.model_name
    
    final_relevant_docs = token_limiter_result.docs
    first_round_full_docs = token_limiter.first_round_full_docs
    second_round_extracted_docs = token_limiter.second_round_extracted_docs
    
    # 验证结果
    assert final_relevant_docs is not None, "应该返回处理后的文档"
    assert len(final_relevant_docs) > 0, "应该至少返回一个文档"
    
    # 计算总的token数量来验证是否超过了第一轮限制
    total_input_tokens = sum([token_limiter.count_tokens(doc.source_code) for doc in relevant_docs])
    first_round_limit = token_limiter.full_text_limit + token_limiter.segment_limit
    
    logger.info(f"总输入tokens: {total_input_tokens}, 第一轮限制: {first_round_limit}")
    
    # 由于我们构建了大量文档，应该触发第二轮处理
    has_second_round_processing = len(second_round_extracted_docs) > 0
    
    if total_input_tokens > first_round_limit:
        # 如果输入超过第一轮限制，应该触发第二轮处理
        assert has_second_round_processing, f"输入tokens({total_input_tokens}) > 第一轮限制({first_round_limit})，应该触发第二轮处理"
        assert rag_stat.chunk_stat.total_input_tokens > 0, "第二轮处理时输入token计数应该增加"
        logger.info("✅ 成功触发第二轮处理 - 有LLM调用和token统计")
    else:
        # 如果没有超过限制，记录但不强制要求第二轮处理
        logger.info(f"输入tokens({total_input_tokens}) <= 第一轮限制({first_round_limit})，可能不需要第二轮处理")
        if has_second_round_processing:
            logger.info("✅ 意外触发了第二轮处理")
            assert rag_stat.chunk_stat.total_input_tokens > 0, "第二轮处理时输入token计数应该增加"
        else:
            logger.info("没有触发第二轮处理 - 所有文档都能装入第一轮限制内")
    
    # 打印测试结果详情
    logger.info("="*80)
    logger.info("TokenLimiter集成测试结果:")
    logger.info("-"*80)
    logger.info(f"处理时间: {sencond_round_time:.4f}秒")
    logger.info(f"输入文档数: {len(relevant_docs)}")
    logger.info(f"输出文档数: {len(final_relevant_docs)}")
    logger.info(f"第一轮全文文档数: {len(first_round_full_docs)}")
    logger.info(f"第二轮提取文档数: {len(second_round_extracted_docs)}")
    logger.info(f"输入token总数: {rag_stat.chunk_stat.total_input_tokens}")
    logger.info(f"生成token总数: {rag_stat.chunk_stat.total_generated_tokens}")
    logger.info("="*80)

def test_limit_tokens_force_second_round(token_limiter, token_counter, real_llm, test_args, test_files):
    """专门测试触发第二轮处理的案例"""
    
    # 创建超大文档确保触发第二轮处理
    # 预计每个文档约5000-8000 tokens
    mega_content = """# 超大文档测试

## TokenLimiter 完整技术规范

TokenLimiter是一个企业级的文档处理和令牌管理系统，专门设计用于处理大规模文档集合和复杂的令牌限制场景。本系统采用了先进的分层处理架构，能够有效地管理从小型文档到大型文档库的各种处理需求。

### 核心架构设计

#### 1. 分层处理架构
系统采用了创新的两层处理架构：
- **第一层：直接装载层**：对于符合令牌限制的文档，系统会直接进行装载，无需额外的处理开销
- **第二层：智能提取层**：对于超出限制的文档，系统启动LLM驱动的智能内容提取机制

#### 2. 令牌管理策略
TokenLimiter实现了精细化的令牌管理策略：
- **全文区域（Full Text Area）**：优先装载完整文档的区域
- **分段区域（Segment Area）**：用于装载经过智能提取的文档片段
- **缓冲区域（Buffer Area）**：为系统操作预留的令牌空间

#### 3. 文档重排序算法
为了减少大语言模型的幻觉现象，系统实现了智能的文档重排序算法：
- 识别来自同一原始文档的多个片段
- 按照原始文档的逻辑顺序重新排列片段
- 确保文档的连贯性和上下文的完整性

### 技术实现细节

#### 并发处理机制
系统支持高度并发的文档处理：
- 使用ThreadPoolExecutor实现多线程并行处理
- 支持可配置的工作线程数量
- 实现了智能的任务调度和负载均衡

#### LLM集成
系统与ByzerLLM深度集成：
- 支持多种LLM后端
- 实现了智能的模型选择策略
- 提供了完整的错误处理和重试机制

#### 元数据管理
系统维护了丰富的元数据信息：
- 处理时间统计
- 令牌使用情况分析
- 文档处理状态跟踪
- 性能指标监控

### 性能优化策略

#### 1. 内存优化
- 采用流式处理减少内存占用
- 实现了智能的对象生命周期管理
- 支持大文档的分块处理

#### 2. 计算优化
- 缓存令牌计数结果
- 优化文档重排序算法
- 实现了增量处理机制

#### 3. 网络优化
- 支持批量LLM调用
- 实现了智能的请求合并
- 提供了网络错误的恢复机制

### 使用场景和最佳实践

#### 场景1：大型代码库分析
在处理包含数千个源代码文件的大型项目时：
```python
# 配置示例
limiter = TokenLimiter(
    count_tokens=tiktoken_counter,
    full_text_limit=10000,
    segment_limit=5000,
    buff_limit=2000,
    llm=code_analysis_llm,
    disable_segment_reorder=False
)

result = limiter.limit_tokens(
    relevant_docs=code_files,
    conversations=analysis_context,
    index_filter_workers=16
)
```

#### 场景2：技术文档问答系统
构建企业级技术文档问答系统：
```python
# 优化配置
limiter = TokenLimiter(
    count_tokens=precise_counter,
    full_text_limit=8000,
    segment_limit=4000,
    buff_limit=1000,
    llm=qa_specialized_llm,
    disable_segment_reorder=False
)
```

#### 场景3：多语言文档处理
处理包含多种编程语言和自然语言的混合文档：
```python
# 多语言配置
limiter = TokenLimiter(
    count_tokens=multilang_counter,
    full_text_limit=12000,
    segment_limit=6000,
    buff_limit=2000,
    llm=multilang_llm,
    disable_segment_reorder=True  # 某些情况下禁用重排序
)
```

### 高级功能特性

#### 1. 自适应令牌管理
系统能够根据文档类型和内容特征自动调整令牌分配策略

#### 2. 智能内容提取
基于对话上下文和文档内容，精确提取最相关的信息片段

#### 3. 质量评估机制
对提取结果进行质量评估，确保输出的可靠性

#### 4. 扩展性支持
支持插件机制，允许用户扩展和定制处理逻辑

### 监控和调试

#### 日志系统
系统提供了详细的日志输出：
- 处理阶段的详细信息
- 性能统计数据
- 错误和异常跟踪
- 调试信息输出

#### 性能监控
内置的性能监控功能：
- 实时处理进度
- 令牌使用统计
- 处理时间分析
- 资源使用情况

#### 故障诊断
完善的故障诊断机制：
- 自动错误检测
- 详细的错误报告
- 恢复建议
- 问题修复指南

### 未来发展规划

#### 短期目标
- 支持更多的LLM后端
- 优化处理性能
- 增强错误处理机制

#### 长期愿景
- 实现智能的自动调优
- 支持分布式处理
- 集成更多的AI能力

这个系统代表了文档处理和令牌管理领域的最新技术成果，为用户提供了强大而灵活的解决方案。
""" * 3  # 重复3次确保足够大

    # 创建6个超大文档
    relevant_docs = []
    for i in range(6):
        relevant_docs.append(
            SourceCode(
                module_name=os.path.join(test_files, f"docs/mega_doc_{i+1}.md"),
                source_code=f"# 超大文档 {i+1}\n\n{mega_content}"
            )
        )
    
    # 预先计算总token数
    total_input_tokens = sum([token_limiter.count_tokens(doc.source_code) for doc in relevant_docs])
    first_round_limit = token_limiter.full_text_limit + token_limiter.segment_limit
    
    logger.info(f"预计总输入tokens: {total_input_tokens}")
    logger.info(f"第一轮处理限制: {first_round_limit}")
    logger.info(f"是否会触发第二轮: {'是' if total_input_tokens > first_round_limit else '否'}")
        
    # 创建对话
    conversations = [{"role": "user", "content": "请详细分析TokenLimiter的核心功能和技术实现"}]
    
    # 准备RAG统计数据
    rag_stat = RAGStat(
        recall_stat=RecallStat(
            total_input_tokens=0,
            total_generated_tokens=0,
            model_name=real_llm.default_model_name,
        ),
        chunk_stat=ChunkStat(
            total_input_tokens=0,
            total_generated_tokens=0,
            model_name=real_llm.default_model_name,
        ),
        answer_stat=AnswerStat(
            total_input_tokens=0,
            total_generated_tokens=0,
            model_name=real_llm.default_model_name,
        ),
    )
    
    # 执行TokenLimiter处理
    start_time = time.time()
    token_limiter_result = token_limiter.limit_tokens(
        relevant_docs=relevant_docs,
        conversations=conversations,
        index_filter_workers=test_args.index_filter_workers or 2,
    )
    processing_time = time.time() - start_time
    
    # 更新统计信息
    rag_stat.chunk_stat.total_input_tokens += sum(token_limiter_result.input_tokens_counts)
    rag_stat.chunk_stat.total_generated_tokens += sum(token_limiter_result.generated_tokens_counts)
    
    # 获取处理结果
    final_docs = token_limiter_result.docs
    first_round_docs = token_limiter.first_round_full_docs  
    second_round_docs = token_limiter.second_round_extracted_docs
    
    # 强制验证第二轮处理被触发
    assert len(second_round_docs) > 0, f"期望触发第二轮处理，但second_round_docs为空。总tokens: {total_input_tokens}, 限制: {first_round_limit}"
    assert rag_stat.chunk_stat.total_input_tokens > 0, f"期望有LLM输入token统计，但为: {rag_stat.chunk_stat.total_input_tokens}"  
    assert rag_stat.chunk_stat.total_generated_tokens > 0, f"期望有LLM生成token统计，但为: {rag_stat.chunk_stat.total_generated_tokens}"
    
    # 验证处理结果的合理性
    assert len(final_docs) > 0, "最终应该返回处理后的文档"
    assert len(final_docs) == len(first_round_docs) + len(second_round_docs), "最终文档数应该等于两轮文档数之和"
    
    # 验证token使用情况
    final_tokens = sum([token_limiter.count_tokens(doc.source_code) for doc in final_docs])
    total_limit = token_limiter.full_text_limit + token_limiter.segment_limit + token_limiter.buff_limit
    assert final_tokens <= total_limit, f"最终文档tokens({final_tokens})应该不超过总限制({total_limit})"
    
    # 打印详细结果
    logger.info("="*80)
    logger.info("强制第二轮处理测试结果:")
    logger.info("-"*80)
    logger.info(f"✅ 成功触发第二轮处理!")
    logger.info(f"处理时间: {processing_time:.2f}秒")
    logger.info(f"输入文档数: {len(relevant_docs)}")
    logger.info(f"第一轮装载文档数: {len(first_round_docs)}")
    logger.info(f"第二轮提取文档数: {len(second_round_docs)}")
    logger.info(f"最终输出文档数: {len(final_docs)}")
    logger.info(f"LLM输入tokens: {rag_stat.chunk_stat.total_input_tokens}")
    logger.info(f"LLM生成tokens: {rag_stat.chunk_stat.total_generated_tokens}")
    logger.info(f"输入文档总tokens: {total_input_tokens}")
    logger.info(f"输出文档总tokens: {final_tokens}")
    logger.info(f"令牌压缩率: {((total_input_tokens - final_tokens) / total_input_tokens * 100):.1f}%")
    logger.info("="*80)

if __name__ == "__main__":
    pytest.main(["-xvs", "test_token_limiter.py"]) 