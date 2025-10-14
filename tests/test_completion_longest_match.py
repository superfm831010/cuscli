from importlib import util
from pathlib import Path

from prompt_toolkit.document import Document

from autocoder.plugins import Plugin, PluginManager

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


class _DummyLongestMatchPlugin(Plugin):
    """测试用插件：用于验证动态补全的最长匹配逻辑。"""

    name = "dummy_longest_match"
    description = "Ensure longest dynamic command wins"
    version = "0.0.1"
    dynamic_cmds = ["/foo /bar", "/foo /bar /baz"]

    def get_dynamic_completions(self, command: str, current_input: str):
        if command == "/foo /bar":
            return [("wrong", "wrong")]
        if command == "/foo /bar /baz":
            return [("alpha", "alpha")]
        return []


def test_enhanced_completer_prefers_longest_dynamic_command():
    manager = PluginManager()
    assert manager.load_plugin(_DummyLongestMatchPlugin)

    completer = EnhancedCompleter(base_completer=None, plugin_manager=manager)
    document = Document("/foo /bar /baz ", len("/foo /bar /baz "))

    results = list(completer.get_completions(document, None))
    completion_texts = {completion.text for completion in results}

    assert "alpha" in completion_texts
    assert "wrong" not in completion_texts
