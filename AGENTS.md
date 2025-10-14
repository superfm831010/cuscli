# Repository Guidelines

## Project Structure & Module Organization
Primary code lives in `autocoder/`, with entry points such as `chat_auto_coder.py`, the CLI in `auto_coder.py`, and feature modules (`agent/`, `checker/`, `rag/`, `sdk/`, `plugins/`). The `tests/` tree mirrors checker functionality (`tests/checker/`), while `rules/` stores customizable lint rule definitions and configuration. Reference docs, integration notes, and checker guides sit in `docs/`, and build artefacts land in `build/` and `dist/`. Utility scripts, including the test runner, are under `scripts/`. Keep translations and licensing files untouched inside `dist-info/` and `cuscli.egg-info/`.

## Build, Test, and Development Commands
- `python -m venv venv && source venv/bin/activate` – create an isolated environment before installing dependencies.  
- `pip install -r requirements.txt` – install runtime plus developer tooling (`pytest`, `pylint`, etc.).  
- `python -m autocoder.chat_auto_coder` – launch the interactive chat interface for manual smoke checks.  
- `python -m autocoder.auto_coder --help` – verify CLI wiring and available subcommands.  
- `./scripts/run_tests.sh -a` – run checker unit and integration suites; add `-c` or `--html` for coverage reports.

## Coding Style & Naming Conventions
All Python code uses 4-space indentation, lowercase-snake-case module and file names, and PascalCase classes. Match existing docstring tone (concise summaries, Chinese comments where already present) and keep public functions type-hinted. Run `pylint` against touched modules (`pylint autocoder/checker/...`) before posting a PR, ensuring no new disables are added to `.pylintrc` equivalents. Prefer pathlib for filesystem work, guard side effects with `if __name__ == "__main__":`, and place configuration constants in `autocoder/common` rather than scattering literals.

## Testing Guidelines
Write or update tests in `tests/checker/`, following the `test_<feature>.py` pattern defined in `pytest.ini`. Use markers `@pytest.mark.unit` or `@pytest.mark.integration` to help `run_tests.sh` filter suites. New features should cover happy paths plus failure modes that raise the project’s domain-specific exceptions. Aim for >=90% coverage on checker components when enabling `--cov`, and document any intentional gaps in the PR description.

## Commit & Pull Request Guidelines
Follow the Conventional Commit style seen in history (`fix(scope): …`, `docs: …`). Group related changes per commit; avoid mixing refactors with behavioural fixes. PRs should include: objective summary, testing evidence (`./scripts/run_tests.sh …` output), linked tracker issue (if any), and screenshots or CLI transcripts for user-facing changes. Request review from a maintainer familiar with the touched module (`checker`, `agent`, etc.) and confirm localisation files remain unmodified unless explicitly required.

## Security & Configuration Tips
Do not hardcode API keys; rely on the environment variables described in `README.md` (`OPENAI_API_KEY`, `AUTOCODER_MODEL`, etc.). When adding new integrations, surface defaults in `autocoder/common/config.py` and document override instructions in `docs/`. Screening logs or samples must redact customer data before committing.

## 其他要求
- 用中文答复
- 所有修改需同时兼容windows和linux下运行
- 把修改过程记录到/docs/二次开发记录.md文件
- 修复完提交git
