"""
Git Helper Plugin for Chat Auto Coder.
Provides convenient Git commands and information display.
"""

import os
import subprocess
from typing import Any, Callable, Dict, List, Optional, Tuple

from autocoder.plugins import Plugin, PluginManager
from autocoder.common.international import register_messages, get_message, get_message_with_format


class GitHelperPlugin(Plugin):
    """Git helper plugin for the Chat Auto Coder."""

    name = "git_helper"
    description = "Git helper plugin providing Git commands and status"
    version = "0.1.0"

    def __init__(self, manager: PluginManager, config: Optional[Dict[str, Any]] = None, config_path: Optional[str] = None):
        """Initialize the Git helper plugin."""
        super().__init__(manager, config, config_path)        
        
        self.git_available = self._check_git_available()
        self.default_branch = self.config.get("default_branch", "main")

    def _check_git_available(self) -> bool:
        """Check if Git is available."""
        try:
            subprocess.run(
                ["git", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            return True
        except Exception:
            return False

    def initialize(self) -> bool:
        """Initialize the plugin.

        Returns:
            True if initialization was successful
        """
        if not self.git_available:
            print(f"[{self.name}] {get_message('git_not_available_warning')}")
            return True

        print(f"[{self.name}] {get_message('git_helper_initialized')}")
        return True

    def get_commands(self) -> Dict[str, Tuple[Callable, str]]:
        """Get commands provided by this plugin.

        Returns:
            A dictionary of command name to handler and description
        """
        return {
            "git/status": (self.git_status, get_message("cmd_git_status_desc")),
            "git/commit": (self.git_commit, get_message("cmd_git_commit_desc")),
            "git/branch": (self.git_branch, get_message("cmd_git_branch_desc")),
            "git/checkout": (self.git_checkout, get_message("cmd_git_checkout_desc")),
            "git/diff": (self.git_diff, get_message("cmd_git_diff_desc")),
            "git/log": (self.git_log, get_message("cmd_git_log_desc")),
            "git/pull": (self.git_pull, get_message("cmd_git_pull_desc")),
            "git/push": (self.git_push, get_message("cmd_git_push_desc")),
            "git/reset": (self.handle_reset, get_message("cmd_git_reset_desc")),
        }

    def get_completions(self) -> Dict[str, List[str]]:
        """Get completions provided by this plugin.

        Returns:
            A dictionary mapping command prefixes to completion options
        """
        completions = {
            "/git/status": [],
            "/git/commit": [],
            "/git/branch": [],
            "/git/checkout": [],
            "/git/diff": [],
            "/git/log": [],
            "/git/pull": [],
            "/git/push": [],
            "/git/reset": ["hard", "soft", "mixed"],
        }

        # 添加分支补全
        if self.git_available:
            try:
                branches = self._get_git_branches()
                completions["/git/checkout"] = branches
                completions["/git/branch"] = branches + [
                    "--delete",
                    "--all",
                    "--remote",
                    "new",
                ]
            except Exception:
                pass

        return completions

    def _run_git_command(self, args: List[str]) -> Tuple[int, str, str]:
        """Run a Git command.

        Args:
            args: The command arguments

        Returns:
            A tuple of (return_code, stdout, stderr)
        """
        if not self.git_available:
            return 1, "", get_message("git_not_available")

        try:
            process = subprocess.run(
                ["git"] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return process.returncode, process.stdout, process.stderr
        except Exception as e:
            return 1, "", str(e)

    def _get_git_branches(self) -> List[str]:
        """Get Git branches.

        Returns:
            A list of branch names
        """
        code, stdout, _ = self._run_git_command(
            ["branch", "--list", "--format=%(refname:short)"]
        )
        if code == 0:
            return [b.strip() for b in stdout.splitlines() if b.strip()]
        return []

    def git_status(self, args: str) -> None:
        """Handle the git/status command."""
        code, stdout, stderr = self._run_git_command(["status"])
        if code == 0:
            print(f"\n{stdout}")
        else:
            print(f"{get_message('error_prefix')} {stderr}")

    def git_commit(self, args: str) -> None:
        """Handle the git/commit command."""
        if not args:
            print(get_message("commit_message_required"))
            return

        # 首先执行添加所有更改 (git add .)
        self._run_git_command(["add", "."])

        # 执行提交
        code, stdout, stderr = self._run_git_command(["commit", "-m", args])
        if code == 0:
            print(f"\n{stdout}")
        else:
            print(f"{get_message('error_prefix')} {stderr}")

    def git_branch(self, args: str) -> None:
        """Handle the git/branch command."""
        args_list = args.split() if args else []
        code, stdout, stderr = self._run_git_command(["branch"] + args_list)
        if code == 0:
            print(f"\n{stdout}")
        else:
            print(f"{get_message('error_prefix')} {stderr}")

    def git_checkout(self, args: str) -> None:
        """Handle the git/checkout command."""
        if not args:
            print(get_message("checkout_branch_required"))
            return

        args_list = args.split()
        code, stdout, stderr = self._run_git_command(["checkout"] + args_list)
        if code == 0:
            print(f"\n{stdout}")
        else:
            print(f"{get_message('error_prefix')} {stderr}")

    def git_diff(self, args: str) -> None:
        """Handle the git/diff command."""
        args_list = args.split() if args else []
        code, stdout, stderr = self._run_git_command(["diff"] + args_list)
        if code == 0:
            if stdout:
                print(f"\n{stdout}")
            else:
                print(get_message("no_differences"))
        else:
            print(f"{get_message('error_prefix')} {stderr}")

    def git_log(self, args: str) -> None:
        """Handle the git/log command."""
        args_list = args.split() if args else ["--oneline", "-n", "10"]
        code, stdout, stderr = self._run_git_command(["log"] + args_list)
        if code == 0:
            print(f"\n{stdout}")
        else:
            print(f"{get_message('error_prefix')} {stderr}")

    def git_pull(self, args: str) -> None:
        """Handle the git/pull command."""
        args_list = args.split() if args else []
        code, stdout, stderr = self._run_git_command(["pull"] + args_list)
        if code == 0:
            print(f"\n{stdout}")
        else:
            print(f"{get_message('error_prefix')} {stderr}")

    def git_push(self, args: str) -> None:
        """Handle the git/push command."""
        args_list = args.split() if args else []
        code, stdout, stderr = self._run_git_command(["push"] + args_list)
        if code == 0:
            print(f"\n{stdout}")
        else:
            print(f"{get_message('error_prefix')} {stderr}")

    def handle_reset(self, args: str) -> None:
        """Handle the git/reset command.
        
        Args:
            args: The reset mode (hard/soft/mixed) and optional commit hash
        """
        if not args:
            print(get_message("reset_mode_required"))
            return
            
        args_list = args.split()
        mode = args_list[0]
        commit = args_list[1] if len(args_list) > 1 else "HEAD"
        
        if mode not in ["hard", "soft", "mixed"]:
            print(get_message_with_format("invalid_reset_mode", mode=mode))
            return
            
        code, stdout, stderr = self._run_git_command(["reset", f"--{mode}", commit])
        if code == 0:
            print(f"\n{stdout}")
            print(get_message_with_format("reset_success", mode=mode, commit=commit))
        else:
            print(f"{get_message('error_prefix')} {stderr}")

    def shutdown(self) -> None:
        """Shutdown the plugin."""
        print(f"[{self.name}] {get_message('git_helper_shutdown')}")
