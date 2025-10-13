"""测试三级命令补全功能"""
from importlib import util
from pathlib import Path

from prompt_toolkit.document import Document

from autocoder.plugins import Plugin, PluginManager

# 动态加载 completer 模块
_COMPLETER_SPEC = util.spec_from_file_location(
    "terminal_ui_completer_for_test",
    Path(__file__).resolve().parents[1]
    / "autocoder"
    / "terminal"
    / "ui"
    / "completer.py",
)
_COMPLETER_MODULE = util.module_from_spec(_COMPLETER_SPEC)
assert _COMPLETER_SPEC and _COMPLETER_SPEC.loader
_COMPLETER_SPEC.loader.exec_module(_COMPLETER_MODULE)  # type: ignore[union-attr]
EnhancedCompleter = _COMPLETER_MODULE.EnhancedCompleter


class _DummyGitPlugin(Plugin):
    """测试用Git插件：模拟git命令的多级补全结构"""

    name = "dummy_git"
    description = "Test git plugin with multi-level completions"
    version = "0.0.1"

    def get_completions(self):
        return {
            "/git": ["/status", "/commit", "/github", "/gitlab", "/platform"],
            "/git /github": ["/setup", "/list", "/modify", "/delete", "/test"],
            "/git /gitlab": ["/setup", "/list", "/modify", "/delete", "/test"],
            "/git /platform": ["/switch", "/list"],
            "/git /platform /switch": ["github", "gitlab"],
        }


def test_git_second_level_completion():
    """测试二级命令补全：/git 后应显示子命令"""
    manager = PluginManager()
    assert manager.load_plugin(_DummyGitPlugin)

    completer = EnhancedCompleter(base_completer=None, plugin_manager=manager)
    document = Document("/git ", len("/git "))

    results = list(completer.get_completions(document, None))
    completion_texts = {completion.text for completion in results}

    # 应该包含所有二级子命令
    assert "/status" in completion_texts
    assert "/commit" in completion_texts
    assert "/github" in completion_texts
    assert "/gitlab" in completion_texts
    assert "/platform" in completion_texts


def test_git_github_third_level_completion():
    """测试三级命令补全：/git /github 后应显示其子命令"""
    manager = PluginManager()
    assert manager.load_plugin(_DummyGitPlugin)

    completer = EnhancedCompleter(base_completer=None, plugin_manager=manager)
    document = Document("/git /github ", len("/git /github "))

    results = list(completer.get_completions(document, None))
    completion_texts = {completion.text for completion in results}

    # 应该包含 /git /github 的子命令
    assert "/setup" in completion_texts
    assert "/list" in completion_texts
    assert "/modify" in completion_texts
    assert "/delete" in completion_texts
    assert "/test" in completion_texts

    # 不应该包含 /git 的子命令
    assert "/status" not in completion_texts
    assert "/commit" not in completion_texts


def test_git_gitlab_third_level_completion():
    """测试三级命令补全：/git /gitlab 后应显示其子命令"""
    manager = PluginManager()
    assert manager.load_plugin(_DummyGitPlugin)

    completer = EnhancedCompleter(base_completer=None, plugin_manager=manager)
    document = Document("/git /gitlab ", len("/git /gitlab "))

    results = list(completer.get_completions(document, None))
    completion_texts = {completion.text for completion in results}

    # 应该包含 /git /gitlab 的子命令
    assert "/setup" in completion_texts
    assert "/list" in completion_texts
    assert "/modify" in completion_texts
    assert "/delete" in completion_texts
    assert "/test" in completion_texts


def test_git_platform_third_level_completion():
    """测试三级命令补全：/git /platform 后应显示其子命令"""
    manager = PluginManager()
    assert manager.load_plugin(_DummyGitPlugin)

    completer = EnhancedCompleter(base_completer=None, plugin_manager=manager)
    document = Document("/git /platform ", len("/git /platform "))

    results = list(completer.get_completions(document, None))
    completion_texts = {completion.text for completion in results}

    # 应该包含 /git /platform 的子命令
    assert "/switch" in completion_texts
    assert "/list" in completion_texts

    # 不应该包含 /git 的其他子命令
    assert "/status" not in completion_texts
    assert "/github" not in completion_texts


def test_git_platform_switch_fourth_level_completion():
    """测试四级命令补全：/git /platform /switch 后应显示平台选项"""
    manager = PluginManager()
    assert manager.load_plugin(_DummyGitPlugin)

    completer = EnhancedCompleter(base_completer=None, plugin_manager=manager)
    document = Document("/git /platform /switch ", len("/git /platform /switch "))

    results = list(completer.get_completions(document, None))
    completion_texts = {completion.text for completion in results}

    # 应该包含平台选项
    assert "github" in completion_texts
    assert "gitlab" in completion_texts


def test_partial_third_level_completion():
    """测试部分输入的三级命令补全：/git /github /set 应该补全为 /setup"""
    manager = PluginManager()
    assert manager.load_plugin(_DummyGitPlugin)

    completer = EnhancedCompleter(base_completer=None, plugin_manager=manager)
    document = Document("/git /github /set", len("/git /github /set"))

    results = list(completer.get_completions(document, None))
    completion_texts = {completion.text for completion in results}

    # 应该只包含匹配的子命令的剩余部分
    assert "up" in completion_texts  # /setup 的剩余部分


def test_longest_match_priority():
    """测试最长匹配优先：确保 /git /github 的补全优先于 /git 的补全"""
    manager = PluginManager()
    assert manager.load_plugin(_DummyGitPlugin)

    completer = EnhancedCompleter(base_completer=None, plugin_manager=manager)

    # 测试 /git /github （应该匹配三级）
    document = Document("/git /github ", len("/git /github "))
    results = list(completer.get_completions(document, None))
    completion_texts = {completion.text for completion in results}

    # 应该是 /git /github 的补全，而不是 /git 的补全
    assert "/setup" in completion_texts
    assert "/status" not in completion_texts

    # 测试 /git （应该匹配二级）
    document2 = Document("/git ", len("/git "))
    results2 = list(completer.get_completions(document2, None))
    completion_texts2 = {completion.text for completion in results2}

    # 应该是 /git 的补全
    assert "/status" in completion_texts2
    assert "/github" in completion_texts2


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
