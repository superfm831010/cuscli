# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **extracted wheel package** of `auto-coder` (version 1.0.39), an AI-powered coding assistant tool. The codebase is in Python and has been extracted from `auto_coder-1.0.39-py3-none-any.whl`.

**Important**: This is proprietary software with commercial use restrictions. See LICENSE for details.

## Entry Points

The package provides multiple command-line interfaces via [entry_points.txt](extracted/auto_coder-1.0.39.dist-info/entry_points.txt):

- `auto-coder` / `auto-coder.core`: Main CLI entry ([auto_coder.py](extracted/autocoder/auto_coder.py):main)
- `auto-coder.chat` / `chat-auto-coder`: Interactive chat interface ([chat_auto_coder.py](extracted/autocoder/chat_auto_coder.py):main)
- `auto-coder.run` / `auto-coder.cli`: SDK CLI interface ([sdk/cli.py](extracted/autocoder/sdk/cli.py):main)
- `auto-coder.rag`: RAG (Retrieval-Augmented Generation) mode ([auto_coder_rag.py](extracted/autocoder/auto_coder_rag.py):main)
- `auto-coder.chat.beta` / `auto-coder.chat.beta3`: Beta terminal versions

## Architecture

### Core Components

1. **Main Entry Point** ([auto_coder.py](extracted/autocoder/auto_coder.py))
   - Command-line argument parsing via [command_args.py](extracted/autocoder/command_args.py)
   - Supports two product modes: `lite` (SimpleByzerLLM, direct API calls) and `pro` (ByzerLLM with Ray cluster)
   - Model management with multiple specialized models (code_model, chat_model, vl_model, emb_model, etc.)
   - Configuration via YAML files with include/inheritance support
   - Action/command dispatcher via `Dispacher` class

2. **Chat Interface** ([chat_auto_coder.py](extracted/autocoder/chat_auto_coder.py))
   - Async-based REPL with prompt_toolkit
   - Plugin system via `PluginManager`
   - Multiple modes: normal, auto_detect, voice_input, shell
   - Background task monitoring and bottom toolbar with system status
   - Command completion and history

3. **Agent System** ([agent/](extracted/autocoder/agent/))
   - Base agent framework in [agent/base_agentic/](extracted/autocoder/agent/base_agentic/)
   - Tool-based architecture with resolvers in [agent/base_agentic/tools/](extracted/autocoder/agent/base_agentic/tools/)
   - Specialized agents: Planner, Designer, Coder, ProjectReader, ChatAgent, AutoTool
   - V2 agentic editing system in [common/v2/agent/](extracted/autocoder/common/v2/agent/)

4. **LLM Integration**
   - Model configuration via [common/llms.py](extracted/autocoder/common/llms.py) and `LLMManager`
   - Powered by `byzerllm` library (both ByzerLLM for Ray clusters and SimpleByzerLLM for direct API)
   - Token counting and request interception
   - Support for multiple model providers (OpenAI, Anthropic, Google, Azure, etc.)

### Key Subsystems

- **RAG System** ([rag/](extracted/autocoder/rag/)): Document indexing, retrieval, and serving
- **Index System** ([index/](extracted/autocoder/index/)): Code indexing and querying
- **Command System** ([commands/](extracted/autocoder/commands/)): Auto-command and web tools
- **Common Utilities** ([common/](extracted/autocoder/common/)): File operations, git utils, code generation/merging, shell/Jupyter clients

## Development Commands

Since this is an extracted wheel package (not a development repository), typical development workflows don't apply. However:

### Running the Tools

```bash
# Activate environment
conda activate autocoder  # or your venv

# Run chat interface (most common)
python -m autocoder.chat_auto_coder

# Run core CLI
python -m autocoder.auto_coder --help

# Run SDK CLI
python -m autocoder.sdk.cli --help
```

### Testing

Tests are present in the codebase:
- Unit tests scattered throughout (e.g., `test_*.py` files)
- Integration tests in specific modules

No centralized test runner configuration is visible in this extracted package.

## Configuration

### Product Modes

- **lite mode**: Uses `SimpleByzerLLM` for direct API calls without Ray cluster
- **pro mode**: Uses `ByzerLLM` with Ray cluster support for distributed computing

### Model Configuration

Models are managed via `LLMManager` and configured through:
- YAML configuration files (with `include_file` support for composition)
- Environment variables (prefix with `ENV {{VARIABLE_NAME}}` in YAML)
- Command-line arguments

Example model types:
- `model`: Primary model for generation
- `code_model`: Specialized for code generation (can be comma-separated list)
- `chat_model`: For chat interactions
- `index_model`: For code indexing
- `emb_model`: For embeddings
- `vl_model`: Vision-language model
- `planner_model`, `designer_model`, `commit_model`: Specialized agents

### Configuration Files

- `.auto-coder/`: Local configuration and state directory
- `actions/`: YAML action files for batch operations
- `.autocoderignore`: Gitignore-style file exclusion

## Important Implementation Details

### Code Generation/Merging

Multiple strategies in [common/](extracted/autocoder/common/):
- `code_auto_generate.py`: Base code generation
- `code_auto_generate_editblock.py`: Edit block format
- `code_auto_generate_diff.py`: Diff format
- `code_auto_merge.py` and variants: Different merge strategies

### Agent Tool System

Tools are resolver-based:
1. Tool definitions with JSON schemas
2. Tool resolvers implement execution logic
3. Tool registry manages available tools
4. Agent hub coordinates multi-agent interactions

Example tool resolvers:
- `read_file_tool_resolver.py`
- `write_to_file_tool_resolver.py`
- `execute_command_tool_resolver.py`
- `search_files_tool_resolver.py`

### Event System

- Event-driven architecture with `EventManager`
- Event files generated per request for cancellation support
- Global cancel mechanism via `global_cancel` singleton

## Dependencies

Key dependencies (from METADATA):
- `byzerllm[saas] >=0.1.196`: Core LLM integration
- `openai >=1.14.3`, `anthropic`, `google-generativeai`: Model providers
- `prompt-toolkit`: Terminal UI
- `fastapi`, `uvicorn`: Web serving
- `GitPython`: Git operations
- `tiktoken`, `tokenizers`: Token counting
- `rich`, `tabulate`: Output formatting

See [METADATA](extracted/auto_coder-1.0.39.dist-info/METADATA) for complete list.

## Special Notes

1. **This is not a source repository**: This is an extracted wheel package, so there's no `.git/`, `setup.py`, or typical development files.

2. **Logging**: Early logger configuration in [__init__.py](extracted/autocoder/__init__.py) suppresses console output and redirects to `.auto-coder/logs/auto-coder.log`

3. **Internationalization**: Language support via [lang.py](extracted/autocoder/lang.py) and [chat_auto_coder_lang.py](extracted/autocoder/chat_auto_coder_lang.py)

4. **Plugin System**: Extensible via plugin manager, plugins in [plugins/](extracted/autocoder/plugins/)

5. **MCP Support**: Model Context Protocol integration via `mcp` library

6. **Async Architecture**: Heavy use of asyncio, especially in chat interface and event handling

## 其他要求
- 用中文答复