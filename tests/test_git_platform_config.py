"""测试 Git 平台配置管理模块"""
import os
import tempfile
from autocoder.common.git_platform_config import GitPlatformConfig, GitPlatformManager


def test_config_manager():
    """测试配置管理器基本功能"""

    # 使用临时文件
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        config_file = f.name

    try:
        # 1. 创建管理器
        manager = GitPlatformManager(config_file)

        # 2. 添加 GitHub 配置
        github_config = GitPlatformConfig(
            name="test-github",
            platform="github",
            base_url="https://api.github.com",
            token="test-token-123"
        )
        assert manager.add_config(github_config)

        # 3. 添加 GitLab 配置
        gitlab_config = GitPlatformConfig(
            name="test-gitlab",
            platform="gitlab",
            base_url="https://gitlab.com/api/v4",
            token="test-token-456"
        )
        assert manager.add_config(gitlab_config)

        # 4. 验证配置数量
        assert len(manager.list_configs("github")) == 1
        assert len(manager.list_configs("gitlab")) == 1

        # 5. 获取配置
        config = manager.get_config("github", "test-github")
        assert config is not None
        assert config.token == "test-token-123"

        # 6. 测试切换平台
        switched_config = manager.switch_platform("gitlab")
        assert switched_config is not None
        assert switched_config.name == "test-gitlab"

        # 7. 测试保存和加载
        manager.save_configs()

        new_manager = GitPlatformManager(config_file)
        assert len(new_manager.list_configs("github")) == 1
        assert len(new_manager.list_configs("gitlab")) == 1

        # 8. 验证 token 加密
        with open(config_file, 'r') as f:
            import json
            data = json.load(f)
            saved_token = data['platforms']['github']['test-github']['token']
            # 加密后的 token 不应该是明文
            assert saved_token != "test-token-123"

        # 9. 测试更新配置
        assert manager.update_config("github", "test-github", timeout=60)
        updated = manager.get_config("github", "test-github")
        assert updated.timeout == 60

        # 10. 测试删除配置
        assert manager.delete_config("github", "test-github")
        assert manager.get_config("github", "test-github") is None

        print("✅ 所有测试通过！")

    finally:
        # 清理临时文件
        if os.path.exists(config_file):
            os.remove(config_file)


if __name__ == "__main__":
    test_config_manager()
