#!/usr/bin/env python3
"""
测试 Git Commit 补全功能
"""

import sys
import os

# 添加项目路径到 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from autocoder.checker.git_helper import GitFileHelper

def test_git_completion():
    """测试 Git 补全功能"""
    print("=" * 60)
    print("测试 Git Commit 补全功能")
    print("=" * 60)
    print()

    try:
        # 初始化 GitFileHelper
        git_helper = GitFileHelper()
        repo = git_helper.repo

        # 1. 测试获取本地未推送的 commits
        print("1. 检测本地未推送的 commits")
        print("-" * 60)

        local_commits = []
        if repo.heads:
            current_branch = repo.active_branch
            print(f"   当前分支: {current_branch.name}")

            if current_branch.tracking_branch():
                remote_branch = current_branch.tracking_branch()
                print(f"   远程跟踪分支: {remote_branch.name}")

                # 获取本地领先远程的 commits
                local_only = list(repo.iter_commits(f'{remote_branch.name}..{current_branch.name}'))

                print(f"   本地未推送的 commits: {len(local_only)} 个")
                print()

                for i, commit in enumerate(local_only[:10], 1):
                    short_hash = commit.hexsha[:7]
                    message = commit.message.strip().split('\n')[0]
                    if len(message) > 50:
                        message = message[:47] + "..."

                    print(f"   {i}. {short_hash} - [本地] {message}")
                    local_commits.append(short_hash)
            else:
                print("   ⚠️ 当前分支没有远程跟踪分支")
        else:
            print("   ⚠️ 没有找到分支")

        print()

        # 2. 测试获取最近的 commits
        print("2. 获取最近 20 个 commits")
        print("-" * 60)

        commits = list(repo.iter_commits('HEAD', max_count=20))
        print(f"   找到 {len(commits)} 个 commits")
        print()

        # 显示前10个（排除本地未推送的）
        count = 0
        for commit in commits:
            short_hash = commit.hexsha[:7]

            # 跳过已经作为本地 commit 显示的
            if short_hash in local_commits:
                continue

            message = commit.message.strip().split('\n')[0]
            if len(message) > 50:
                message = message[:47] + "..."

            count += 1
            if count <= 10:
                print(f"   {count}. {short_hash} - {message}")

        print()

        # 3. 显示补全列表预览
        print("3. 补全列表预览（前15项）")
        print("-" * 60)

        completions = []

        # 本地 commits
        local_hashes = set()
        if repo.heads:
            current_branch = repo.active_branch
            if current_branch.tracking_branch():
                remote_branch = current_branch.tracking_branch()
                local_only = list(repo.iter_commits(f'{remote_branch.name}..{current_branch.name}'))

                for commit in local_only:
                    short_hash = commit.hexsha[:7]
                    message = commit.message.strip().split('\n')[0]
                    if len(message) > 45:
                        message = message[:42] + "..."

                    display = f"{short_hash} - [本地] {message}"
                    completions.append((short_hash, display))
                    local_hashes.add(short_hash)

        # 最近的 commits
        commits = list(repo.iter_commits('HEAD', max_count=20))
        for commit in commits:
            short_hash = commit.hexsha[:7]
            if short_hash in local_hashes:
                continue

            message = commit.message.strip().split('\n')[0]
            if len(message) > 50:
                message = message[:47] + "..."

            display = f"{short_hash} - {message}"
            completions.append((short_hash, display))

        # 相对引用
        relative_refs = [
            ("HEAD", "HEAD (最新 commit)"),
            ("HEAD~1", "HEAD~1 (前1个 commit)"),
            ("HEAD~2", "HEAD~2 (前2个 commit)"),
            ("HEAD~3", "HEAD~3 (前3个 commit)"),
            ("HEAD~5", "HEAD~5 (前5个 commit)"),
            ("HEAD~10", "HEAD~10 (前10个 commit)"),
        ]
        completions.extend(relative_refs)

        # 分支名
        branches = [b.name for b in repo.branches]
        for branch in branches[:5]:
            completions.append((branch, f"{branch} (分支)"))

        # 显示前15项
        for i, (ref, display) in enumerate(completions[:15], 1):
            print(f"   {i}. {display}")

        print()
        print(f"   ... 总共 {len(completions)} 项补全选项")
        print()

        print("=" * 60)
        print("✅ 测试完成")
        print("=" * 60)

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(test_git_completion())
