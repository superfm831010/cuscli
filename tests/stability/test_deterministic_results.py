"""
稳定性测试：确保 CodeChecker 的 LLM 调用配置具有确定性。
"""

from unittest.mock import Mock, patch

import pytest

from autocoder.checker.core import CodeChecker
from autocoder.checker.types import Rule, Severity
from autocoder.common import AutoCoderArgs


@pytest.fixture
def llm_stub():
    """提供一个简单的 LLM mock"""
    llm = Mock()
    mock_response = Mock()
    mock_response.output = "```json\n[]\n```"
    llm.chat_oai.return_value = [mock_response]
    return llm


def test_llm_config_defaults_are_deterministic(llm_stub):
    """默认配置应启用确定性参数"""
    checker = CodeChecker(llm_stub, AutoCoderArgs())
    assert checker.llm_config["temperature"] == 0.0
    assert checker.llm_config["top_p"] == 1.0
    assert checker.llm_config["seed"] == 42
    assert checker.file_processor.chunk_size == 20000


def test_llm_config_overrides_from_args(llm_stub):
    """Args 中的配置应该覆盖默认值"""
    args = AutoCoderArgs(
        checker_llm_temperature=0.2,
        checker_llm_top_p=0.9,
        checker_llm_seed=128,
        checker_llm_config={"presence_penalty": 0.1},
        checker_chunk_token_limit=8000,
    )
    checker = CodeChecker(llm_stub, args)

    assert checker.llm_config["temperature"] == 0.2
    assert checker.llm_config["top_p"] == 0.9
    assert checker.llm_config["seed"] == 128
    assert checker.llm_config["presence_penalty"] == 0.1
    assert checker.file_processor.chunk_size == 8000


def test_llm_config_env_override(monkeypatch, llm_stub):
    """环境变量可以覆盖默认值"""
    monkeypatch.setenv("CODECHECKER_LLM_TEMPERATURE", "0.15")
    monkeypatch.setenv("CODECHECKER_LLM_TOP_P", "0.8")
    monkeypatch.setenv("CODECHECKER_LLM_SEED", "99")
    monkeypatch.setenv("CODECHECKER_CHUNK_TOKEN_LIMIT", "12000")

    checker = CodeChecker(llm_stub, AutoCoderArgs())

    assert checker.llm_config["temperature"] == 0.15
    assert checker.llm_config["top_p"] == 0.8
    assert checker.llm_config["seed"] == 99
    assert checker.file_processor.chunk_size == 12000

    # 清理环境变量，避免影响其它测试
    monkeypatch.delenv("CODECHECKER_LLM_TEMPERATURE", raising=False)
    monkeypatch.delenv("CODECHECKER_LLM_TOP_P", raising=False)
    monkeypatch.delenv("CODECHECKER_LLM_SEED", raising=False)
    monkeypatch.delenv("CODECHECKER_CHUNK_TOKEN_LIMIT", raising=False)


def test_check_code_chunk_uses_llm_config(llm_stub):
    """check_code_chunk 应该传递统一的 LLM 配置"""
    checker = CodeChecker(llm_stub, AutoCoderArgs())

    rule = Rule(
        id="demo",
        category="测试",
        title="测试规则",
        description="描述",
        severity=Severity.ERROR,
    )

    response_stub = Mock()
    response_stub.output = "```json\n[]\n```"

    with patch.object(checker, "_call_llm", return_value=[response_stub]) as mock_call:
        checker.check_code_chunk("1 demo()", [rule])

        # mock_call.call_args[0] -> (conversations, llm_config)
        assert mock_call.call_count == 1
        _, llm_config = mock_call.call_args[0]
        assert llm_config == checker.llm_config
