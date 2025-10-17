#!/usr/bin/env python3
"""测试 Git 仓库管理器修复后的功能"""

import os
from pathlib import Path
from autocoder.common.git_platform_config import GitPlatformManager
from autocoder.checker.git_repo_manager import GitRepoManager

def test_config_loading():
    """测试配置文件加载"""
    print("=== 测试配置文件加载 ===")

    # 检查正确的配置文件路径
    correct_config = Path.home() / ".auto-coder" / "plugins" / "autocoder.plugins.git_helper_plugin.GitHelperPlugin" / "config.json"
    print(f"检查配置文件路径: {correct_config}")
    print(f"配置文件存在: {correct_config.exists()}")

    # 测试 GitPlatformManager 加载
    if correct_config.exists():
        manager = GitPlatformManager(str(correct_config))

        # 列出所有配置
        for platform in ['gitlab', 'github']:
            configs = manager.list_configs(platform)
            print(f"\n{platform} 平台配置:")
            for config in configs:
                print(f"  - {config.name}: {config.base_url}")
                print(f"    Token: {'已配置' if config.token else '未配置'}")
                print(f"    激活状态: {'激活' if config.is_active else '未激活'}")

        # 获取当前激活的配置
        active_gitlab = manager.get_config('gitlab')
        active_github = manager.get_config('github')

        print(f"\n当前激活的 GitLab 配置: {active_gitlab.name if active_gitlab else '无'}")
        print(f"当前激活的 GitHub 配置: {active_github.name if active_github else '无'}")
    else:
        print("配置文件不存在，跳过详细测试")

    print()

def test_repo_manager():
    """测试 GitRepoManager"""
    print("=== 测试 GitRepoManager ===")

    # 创建 GitRepoManager 实例
    repo_manager = GitRepoManager()

    print(f"GitRepoManager 初始化成功")
    print(f"平台管理器已加载: {repo_manager.platform_manager is not None}")

    if repo_manager.platform_manager:
        # 测试 URL 匹配
        test_urls = [
            "http://10.56.215.182/zs/ecim/ecim-java.git",
            "https://github.com/example/repo.git",
            "git@gitlab.com:user/project.git"
        ]

        print("\n测试 URL 匹配:")
        for url in test_urls:
            config = repo_manager._match_git_config(url)
            if config:
                print(f"  {url}")
                print(f"    匹配到配置: {config.name} ({config.platform})")
                print(f"    Token 状态: {'已配置' if config.token else '未配置'}")
            else:
                print(f"  {url}")
                print(f"    未匹配到配置")

    print()

def test_error_messages():
    """测试错误提示信息"""
    print("=== 测试错误提示信息 ===")

    # 读取修复后的文件，检查错误提示是否正确
    git_repo_file = Path("/projects/cuscli/autocoder/checker/git_repo_manager.py")

    if git_repo_file.exists():
        content = git_repo_file.read_text()

        # 检查是否还存在错误的命令
        if "/git /config" in content:
            print("❌ 错误：文件中仍然包含 '/git /config' 命令")
        else:
            print("✅ 正确：文件中不再包含 '/git /config' 命令")

        # 检查是否包含正确的命令
        if "/git /gitlab /setup" in content and "/git /github /setup" in content:
            print("✅ 正确：文件包含正确的设置命令提示")
        else:
            print("⚠️  警告：文件可能缺少正确的设置命令提示")

    # 检查 code_checker_plugin.py
    plugin_file = Path("/projects/cuscli/autocoder/plugins/code_checker_plugin.py")

    if plugin_file.exists():
        content = plugin_file.read_text()

        # 检查是否还存在错误的配置路径
        if "git_helper_config.json" in content:
            print("❌ 错误：code_checker_plugin.py 仍然包含错误的配置路径")
        else:
            print("✅ 正确：code_checker_plugin.py 不再包含错误的配置路径")

        # 检查是否包含正确的配置路径
        if "autocoder.plugins.git_helper_plugin.GitHelperPlugin" in content:
            print("✅ 正确：code_checker_plugin.py 包含正确的配置路径")
        else:
            print("⚠️  警告：code_checker_plugin.py 可能缺少正确的配置路径")

    print()

if __name__ == "__main__":
    print("Git 仓库管理器修复测试\n")

    test_config_loading()
    test_repo_manager()
    test_error_messages()

    print("测试完成！")