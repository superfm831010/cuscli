# Phase 1: 配置管理框架搭建

## 🎯 阶段目标

创建核心配置管理模块，为 GitHub 和 GitLab 配置管理提供基础框架。

## 📋 前置条件

- ✅ 已阅读 `00-overview.md` 总体概述
- ✅ 熟悉插件系统的配置管理机制

## 🔧 实施步骤

### 步骤 1: 创建配置管理模块

**文件：** `autocoder/common/git_platform_config.py`

这是一个全新文件，包含所有配置管理的核心逻辑。

```python
"""
Git 平台配置管理模块

提供 GitHub 和 GitLab 配置的统一管理功能。
"""
import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from cryptography.fernet import Fernet
from loguru import logger


# 加密密钥管理
def _get_or_create_key() -> bytes:
    """获取或创建加密密钥"""
    key_file = Path.home() / ".auto-coder" / "keys" / ".platform_key"
    key_file.parent.mkdir(parents=True, exist_ok=True)

    if key_file.exists():
        return key_file.read_bytes()
    else:
        key = Fernet.generate_key()
        key_file.write_bytes(key)
        key_file.chmod(0o600)  # 仅所有者可读写
        return key


_CIPHER = Fernet(_get_or_create_key())


def _encrypt(text: str) -> str:
    """加密文本"""
    return _CIPHER.encrypt(text.encode()).decode()


def _decrypt(encrypted: str) -> str:
    """解密文本"""
    try:
        return _CIPHER.decrypt(encrypted.encode()).decode()
    except Exception as e:
        logger.error(f"解密失败: {e}")
        return ""


@dataclass
class GitPlatformConfig:
    """Git 平台配置"""
    name: str                           # 配置名称（如"公司GitLab"）
    platform: str                       # 平台类型: github/gitlab
    base_url: str                       # API 基础 URL
    token: str                          # 访问令牌
    verify_ssl: bool = True             # 是否验证 SSL
    timeout: int = 30                   # 超时时间（秒）
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_tested: Optional[str] = None   # 最后测试时间

    def to_dict(self, encrypt_token: bool = True) -> Dict[str, Any]:
        """转换为字典（用于序列化）"""
        data = asdict(self)
        if encrypt_token and self.token:
            data['token'] = _encrypt(self.token)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], decrypt_token: bool = True) -> 'GitPlatformConfig':
        """从字典创建（用于反序列化）"""
        data = data.copy()
        if decrypt_token and data.get('token'):
            data['token'] = _decrypt(data['token'])
        return cls(**data)

    def update_last_tested(self):
        """更新最后测试时间"""
        self.last_tested = datetime.now().isoformat()


class GitPlatformManager:
    """Git 平台配置管理器"""

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径，默认为插件配置文件
        """
        self.config_file = config_file
        self.configs: Dict[str, Dict[str, GitPlatformConfig]] = {
            "github": {},
            "gitlab": {}
        }
        self.current_platform: str = "github"  # 默认平台
        self.current_config: Dict[str, str] = {
            "github": "",
            "gitlab": ""
        }

        if self.config_file:
            self.load_configs()

    def load_configs(self) -> bool:
        """
        从文件加载配置

        Returns:
            bool: 是否成功加载
        """
        if not self.config_file or not os.path.exists(self.config_file):
            return False

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 加载平台配置
            platforms_data = data.get('platforms', {})
            for platform, configs in platforms_data.items():
                if platform not in self.configs:
                    self.configs[platform] = {}
                for name, config_data in configs.items():
                    self.configs[platform][name] = GitPlatformConfig.from_dict(
                        config_data, decrypt_token=True
                    )

            # 加载当前选择
            self.current_platform = data.get('current_platform', 'github')
            self.current_config = data.get('current_config', {"github": "", "gitlab": ""})

            logger.info(f"已加载 Git 平台配置: {sum(len(c) for c in self.configs.values())} 个配置")
            return True

        except Exception as e:
            logger.error(f"加载 Git 平台配置失败: {e}")
            return False

    def save_configs(self) -> bool:
        """
        保存配置到文件

        Returns:
            bool: 是否成功保存
        """
        if not self.config_file:
            return False

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            # 构建保存数据
            platforms_data = {}
            for platform, configs in self.configs.items():
                platforms_data[platform] = {
                    name: config.to_dict(encrypt_token=True)
                    for name, config in configs.items()
                }

            data = {
                'current_platform': self.current_platform,
                'current_config': self.current_config,
                'platforms': platforms_data
            }

            # 保存到文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Git 平台配置已保存到: {self.config_file}")
            return True

        except Exception as e:
            logger.error(f"保存 Git 平台配置失败: {e}")
            return False

    def add_config(self, config: GitPlatformConfig) -> bool:
        """
        添加新配置

        Args:
            config: 配置对象

        Returns:
            bool: 是否成功添加
        """
        if config.platform not in self.configs:
            logger.error(f"不支持的平台: {config.platform}")
            return False

        if config.name in self.configs[config.platform]:
            logger.warning(f"配置 '{config.name}' 已存在，将被覆盖")

        self.configs[config.platform][config.name] = config

        # 如果是该平台的第一个配置，设为默认
        if not self.current_config.get(config.platform):
            self.current_config[config.platform] = config.name

        self.save_configs()
        logger.info(f"已添加 {config.platform} 配置: {config.name}")
        return True

    def update_config(self, platform: str, name: str, **updates) -> bool:
        """
        更新配置

        Args:
            platform: 平台类型
            name: 配置名称
            **updates: 要更新的字段

        Returns:
            bool: 是否成功更新
        """
        config = self.get_config(platform, name)
        if not config:
            logger.error(f"配置不存在: {platform}/{name}")
            return False

        # 更新字段
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)

        self.save_configs()
        logger.info(f"已更新 {platform} 配置: {name}")
        return True

    def delete_config(self, platform: str, name: str) -> bool:
        """
        删除配置

        Args:
            platform: 平台类型
            name: 配置名称

        Returns:
            bool: 是否成功删除
        """
        if platform not in self.configs:
            return False

        if name not in self.configs[platform]:
            logger.warning(f"配置不存在: {platform}/{name}")
            return False

        del self.configs[platform][name]

        # 如果删除的是当前配置，清除当前配置
        if self.current_config.get(platform) == name:
            # 尝试选择该平台的其他配置
            remaining = list(self.configs[platform].keys())
            self.current_config[platform] = remaining[0] if remaining else ""

        self.save_configs()
        logger.info(f"已删除 {platform} 配置: {name}")
        return True

    def get_config(self, platform: str, name: str) -> Optional[GitPlatformConfig]:
        """
        获取配置

        Args:
            platform: 平台类型
            name: 配置名称

        Returns:
            GitPlatformConfig: 配置对象，不存在返回 None
        """
        return self.configs.get(platform, {}).get(name)

    def list_configs(self, platform: str) -> List[GitPlatformConfig]:
        """
        列出指定平台的所有配置

        Args:
            platform: 平台类型

        Returns:
            List[GitPlatformConfig]: 配置列表
        """
        return list(self.configs.get(platform, {}).values())

    def get_current_config(self) -> Optional[GitPlatformConfig]:
        """
        获取当前激活的配置

        Returns:
            GitPlatformConfig: 当前配置对象，未设置返回 None
        """
        config_name = self.current_config.get(self.current_platform)
        if not config_name:
            return None
        return self.get_config(self.current_platform, config_name)

    def switch_platform(self, platform: str, config_name: Optional[str] = None) -> Optional[GitPlatformConfig]:
        """
        切换平台

        Args:
            platform: 目标平台
            config_name: 配置名称（可选，默认使用该平台的当前配置）

        Returns:
            GitPlatformConfig: 切换后的配置对象，失败返回 None
        """
        if platform not in self.configs:
            logger.error(f"不支持的平台: {platform}")
            return None

        # 如果未指定配置名，使用该平台的当前配置
        if not config_name:
            config_name = self.current_config.get(platform)

        # 如果该平台没有配置，返回 None
        if not config_name or config_name not in self.configs[platform]:
            logger.error(f"平台 {platform} 没有可用的配置")
            return None

        # 切换平台和配置
        self.current_platform = platform
        self.current_config[platform] = config_name

        self.save_configs()

        config = self.get_config(platform, config_name)
        logger.info(f"已切换到 {platform}/{config_name}")
        return config

    def has_config(self, platform: str) -> bool:
        """
        检查平台是否有配置

        Args:
            platform: 平台类型

        Returns:
            bool: 是否有配置
        """
        return len(self.configs.get(platform, {})) > 0
```

---

### 步骤 2: 测试配置管理模块

创建测试脚本验证基本功能：

**文件：** `tests/test_git_platform_config.py`（可选，用于验证）

```python
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
```

---

## 🧪 测试要点

### 手动测试

1. **导入测试**
   ```python
   from autocoder.common.git_platform_config import GitPlatformConfig, GitPlatformManager
   ```

2. **创建配置**
   ```python
   config = GitPlatformConfig(
       name="test",
       platform="github",
       base_url="https://api.github.com",
       token="test-token"
   )
   print(config)
   ```

3. **加密测试**
   ```python
   encrypted_data = config.to_dict(encrypt_token=True)
   print(f"加密后的 token: {encrypted_data['token']}")

   decrypted_config = GitPlatformConfig.from_dict(encrypted_data, decrypt_token=True)
   print(f"解密后的 token: {decrypted_config.token}")
   ```

4. **管理器测试**
   ```python
   manager = GitPlatformManager("/tmp/test_config.json")
   manager.add_config(config)
   manager.save_configs()

   # 验证文件已创建
   import os
   assert os.path.exists("/tmp/test_config.json")
   ```

### 自动化测试

运行测试脚本：
```bash
cd /projects/cuscli
python tests/test_git_platform_config.py
```

预期输出：
```
✅ 所有测试通过！
```

---

## ✅ 完成标志

- [x] 创建了 `autocoder/common/git_platform_config.py` 文件
- [x] 实现了 `GitPlatformConfig` 数据类
- [x] 实现了 `GitPlatformManager` 管理器类
- [x] Token 加密功能正常工作
- [x] 配置的增删改查功能正常
- [x] 配置文件可以正确保存和加载
- [x] 测试脚本全部通过

---

## 📝 提交代码

```bash
cd /projects/cuscli

# 添加文件
git add autocoder/common/git_platform_config.py
git add tests/test_git_platform_config.py  # 如果创建了测试

# 提交
git commit -m "feat(git-plugin): 添加 Git 平台配置管理框架

- 创建 GitPlatformConfig 数据类
- 创建 GitPlatformManager 配置管理器
- 支持 GitHub 和 GitLab 配置管理
- 实现 Token 加密存储
- 实现配置的增删改查功能
- 支持平台切换
"

# 推送（可选）
# git push
```

---

## 🎉 Phase 1 完成！

恭喜！您已经完成了配置管理框架的搭建。核心配置管理功能已经就绪。

### 下一步

➡️ **进入 Phase 2**: 阅读 `02-phase2-github-config.md`，开始实现 GitHub 配置管理功能。

---

## 💡 常见问题

### Q1: 加密密钥存储在哪里？
**A:** 密钥存储在 `~/.auto-coder/keys/.platform_key`，权限设置为 600（仅所有者可读写）。

### Q2: 如果密钥丢失怎么办？
**A:** 如果密钥丢失，已加密的 token 将无法解密。需要重新配置所有平台。建议备份密钥文件。

### Q3: 配置文件可以手动编辑吗？
**A:** 不建议手动编辑，因为 token 是加密的。应该使用提供的 API 或命令进行管理。

### Q4: 如何调试配置加载问题？
**A:** 检查日志文件 `.auto-coder/logs/auto-coder.log`，所有配置操作都有详细日志记录。
