# Phase 5: 测试计划

## 测试目标

确保 Git 检查功能在各种场景下都能正常工作，特别是跨平台兼容性。

## 测试环境

### 1. 平台测试
- ✅ Linux (Ubuntu 22.04)
- ✅ Windows 10/11
- 可选: macOS

### 2. Python 版本
- Python 3.8+
- Python 3.10 (推荐)

### 3. Git 版本
- Git 2.x
- 测试多种 Git 配置（CRLF、编码等）

## 单元测试

### 1. GitFileHelper 测试

**文件**: `tests/checker/test_git_helper.py`

```python
import pytest
import os
import tempfile
from git import Repo
from autocoder.checker.git_helper import GitFileHelper

class TestGitFileHelper:
    """GitFileHelper 单元测试"""

    @pytest.fixture
    def git_repo(self):
        """创建测试用 Git 仓库"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Repo.init(tmpdir)
            repo.config_writer().set_value("user", "name", "Test").release()
            repo.config_writer().set_value("user", "email", "test@test.com").release()

            # 创建初始文件
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write("print('hello')\n")

            repo.index.add(['test.py'])
            repo.index.commit("Initial commit")

            yield tmpdir

    def test_init_valid_repo(self, git_repo):
        """测试初始化有效仓库"""
        helper = GitFileHelper(git_repo)
        assert helper.repo is not None
        assert helper.repo_path == os.path.abspath(git_repo)

    def test_init_invalid_repo(self):
        """测试初始化无效仓库"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(RuntimeError, match="不是有效的 Git 仓库"):
                GitFileHelper(tmpdir)

    def test_get_staged_files(self, git_repo):
        """测试获取暂存区文件"""
        # 创建新文件并 add
        new_file = os.path.join(git_repo, "new.py")
        with open(new_file, 'w') as f:
            f.write("print('new')\n")

        repo = Repo(git_repo)
        repo.index.add(['new.py'])

        helper = GitFileHelper(git_repo)
        files = helper.get_staged_files()

        assert len(files) == 1
        assert files[0].endswith('new.py')

    def test_get_unstaged_files(self, git_repo):
        """测试获取工作区修改文件"""
        # 修改现有文件
        test_file = os.path.join(git_repo, "test.py")
        with open(test_file, 'a') as f:
            f.write("print('modified')\n")

        helper = GitFileHelper(git_repo)
        files = helper.get_unstaged_files()

        assert len(files) == 1
        assert files[0].endswith('test.py')

    def test_get_commit_files(self, git_repo):
        """测试获取 commit 文件"""
        helper = GitFileHelper(git_repo)
        repo = Repo(git_repo)
        last_commit = repo.head.commit.hexsha

        files = helper.get_commit_files(last_commit)

        assert len(files) == 1
        assert 'test.py' in files[0]

    def test_get_commit_files_short_hash(self, git_repo):
        """测试使用短哈希获取 commit 文件"""
        helper = GitFileHelper(git_repo)
        repo = Repo(git_repo)
        short_hash = repo.head.commit.hexsha[:7]

        files = helper.get_commit_files(short_hash)
        assert len(files) == 1

    def test_get_commit_files_invalid_hash(self, git_repo):
        """测试无效的 commit hash"""
        helper = GitFileHelper(git_repo)

        with pytest.raises(ValueError, match="Commit 不存在"):
            helper.get_commit_files("invalid_hash")

    def test_get_diff_files(self, git_repo):
        """测试获取 diff 文件"""
        repo = Repo(git_repo)

        # 创建第二个 commit
        test_file = os.path.join(git_repo, "test2.py")
        with open(test_file, 'w') as f:
            f.write("print('test2')\n")

        repo.index.add(['test2.py'])
        commit2 = repo.index.commit("Add test2")

        helper = GitFileHelper(git_repo)
        files = helper.get_diff_files("HEAD~1", "HEAD")

        assert len(files) == 1
        assert 'test2.py' in files[0]

    def test_get_file_content_at_commit(self, git_repo):
        """测试获取历史文件内容"""
        helper = GitFileHelper(git_repo)
        repo = Repo(git_repo)
        commit_hash = repo.head.commit.hexsha

        content = helper.get_file_content_at_commit("test.py", commit_hash)

        assert content is not None
        assert "print('hello')" in content

    def test_is_binary_file(self, git_repo):
        """测试二进制文件检测"""
        # 创建文本文件
        text_file = os.path.join(git_repo, "text.txt")
        with open(text_file, 'w') as f:
            f.write("text content")

        # 创建二进制文件
        binary_file = os.path.join(git_repo, "binary.bin")
        with open(binary_file, 'wb') as f:
            f.write(b'\x00\x01\x02\x03')

        helper = GitFileHelper(git_repo)

        assert not helper.is_binary_file("text.txt")
        assert helper.is_binary_file("binary.bin")

    def test_skip_deleted_files(self, git_repo):
        """测试跳过删除的文件"""
        repo = Repo(git_repo)

        # 创建并提交新文件
        new_file = os.path.join(git_repo, "to_delete.py")
        with open(new_file, 'w') as f:
            f.write("print('will be deleted')\n")
        repo.index.add(['to_delete.py'])
        repo.index.commit("Add file to delete")

        # 删除文件并提交
        os.remove(new_file)
        repo.index.remove(['to_delete.py'])
        delete_commit = repo.index.commit("Delete file")

        helper = GitFileHelper(git_repo)
        files = helper.get_commit_files(delete_commit.hexsha)

        # 删除的文件应该被跳过
        assert len(files) == 0
```

### 2. 临时文件管理测试

**文件**: `tests/checker/test_temp_file_manager.py`

```python
import pytest
import os
from autocoder.plugins.code_checker_plugin import TempFileManager

def test_temp_file_manager_basic():
    """测试基本功能"""
    with TempFileManager() as manager:
        temp_path = manager.create_temp_file(
            "src/main.py",
            "print('hello')\n"
        )

        assert os.path.exists(temp_path)

        with open(temp_path, 'r') as f:
            assert f.read() == "print('hello')\n"

    # 退出后自动清理
    assert not os.path.exists(temp_path)

def test_temp_file_manager_multiple_files():
    """测试多文件管理"""
    with TempFileManager() as manager:
        file1 = manager.create_temp_file("a.py", "# a\n")
        file2 = manager.create_temp_file("b.py", "# b\n")

        assert os.path.exists(file1)
        assert os.path.exists(file2)

        # 路径映射
        assert manager.get_original_path(file1) == "a.py"
        assert manager.get_original_path(file2) == "b.py"

def test_temp_file_manager_nested_paths():
    """测试嵌套路径"""
    with TempFileManager() as manager:
        nested_file = manager.create_temp_file(
            "src/utils/helper.py",
            "# helper\n"
        )

        assert os.path.exists(nested_file)
        assert manager.get_original_path(nested_file) == "src/utils/helper.py"
```

## 集成测试

### 测试场景

#### 场景 1: 暂存区检查

```python
def test_check_git_staged(test_repo):
    """测试暂存区检查"""
    # 1. 修改文件
    # 2. git add
    # 3. 执行 /check /git /staged
    # 4. 验证报告生成
    # 5. 验证报告包含 Git 信息
    pass
```

#### 场景 2: 工作区检查

```python
def test_check_git_unstaged(test_repo):
    """测试工作区检查"""
    # 1. 修改文件（不 add）
    # 2. 执行 /check /git /unstaged
    # 3. 验证报告生成
    pass
```

#### 场景 3: Commit 检查

```python
def test_check_git_commit(test_repo):
    """测试 commit 检查"""
    # 1. 创建包含问题的文件
    # 2. git commit
    # 3. 执行 /check /git /commit <hash>
    # 4. 验证临时文件创建和清理
    # 5. 验证报告正确
    pass
```

#### 场景 4: Diff 检查

```python
def test_check_git_diff(test_repo):
    """测试 diff 检查"""
    # 1. 创建 commit1
    # 2. 修改文件，创建 commit2
    # 3. 执行 /check /git /diff commit1 commit2
    # 4. 验证检查范围正确
    pass
```

## 边界情况测试

### 1. 空仓库

```python
def test_empty_staged():
    """暂存区为空"""
    # 应该提示 "暂存区没有文件"
    pass

def test_empty_unstaged():
    """工作区无修改"""
    # 应该提示 "工作区没有修改文件"
    pass
```

### 2. 初始 Commit

```python
def test_initial_commit():
    """测试初始 commit（无父节点）"""
    # 应该正确处理
    pass
```

### 3. 大文件

```python
def test_large_file():
    """测试大文件（>10MB）"""
    # 应该跳过
    pass
```

### 4. 二进制文件

```python
def test_binary_file():
    """测试二进制文件"""
    # 应该跳过
    pass
```

### 5. 删除的文件

```python
def test_deleted_file():
    """测试删除的文件"""
    # 应该跳过
    pass
```

### 6. 编码错误

```python
def test_encoding_error():
    """测试编码错误的文件"""
    # 应该优雅处理
    pass
```

### 7. 无效 Commit Hash

```python
def test_invalid_commit_hash():
    """测试无效的 commit hash"""
    # 应该提示错误
    pass
```

## 跨平台测试

### Windows 特定测试

```python
@pytest.mark.skipif(os.name != 'nt', reason="Windows only")
def test_windows_path_handling():
    """测试 Windows 路径处理"""
    # 测试反斜杠路径
    # 测试长路径
    # 测试特殊字符
    pass

@pytest.mark.skipif(os.name != 'nt', reason="Windows only")
def test_windows_temp_dir():
    """测试 Windows 临时目录"""
    # 验证临时目录路径
    pass
```

### Linux 特定测试

```python
@pytest.mark.skipif(os.name == 'nt', reason="Linux only")
def test_linux_permissions():
    """测试 Linux 权限处理"""
    # 测试文件权限
    pass
```

## 性能测试

```python
def test_performance_large_commit():
    """测试大型 commit 性能"""
    # 创建包含 100+ 文件的 commit
    # 测试检查时间 < 5 分钟
    pass

def test_performance_concurrent():
    """测试并发性能"""
    # 验证并发加速效果
    pass
```

## 测试运行

### 运行所有测试

```bash
# 运行所有 checker 相关测试
pytest tests/checker/ -v

# 运行特定测试文件
pytest tests/checker/test_git_helper.py -v

# 运行特定测试
pytest tests/checker/test_git_helper.py::TestGitFileHelper::test_get_staged_files -v
```

### 覆盖率测试

```bash
# 生成覆盖率报告
pytest tests/checker/ --cov=autocoder.checker --cov-report=html

# 查看覆盖率
open htmlcov/index.html
```

### 跨平台测试

```bash
# Windows
python -m pytest tests/checker/ -v -m "not linux_only"

# Linux
python -m pytest tests/checker/ -v -m "not windows_only"
```

## 手工测试清单

### 基本功能测试

- [ ] 暂存区检查：有文件时正常检查
- [ ] 暂存区检查：无文件时友好提示
- [ ] 工作区检查：有修改时正常检查
- [ ] 工作区检查：无修改时友好提示
- [ ] Commit 检查：使用完整 hash
- [ ] Commit 检查：使用短 hash（7位）
- [ ] Commit 检查：无效 hash 报错
- [ ] Diff 检查：指定两个 commit
- [ ] Diff 检查：只指定一个 commit（对比 HEAD）

### 参数测试

- [ ] `/repeat 3` 参数生效
- [ ] `/consensus 0.8` 参数生效
- [ ] `/workers 10` 参数生效
- [ ] 组合参数: `/repeat 3 /consensus 0.8 /workers 5`

### 报告测试

- [ ] 报告包含 Git 信息
- [ ] Commit 报告显示 commit 详情
- [ ] Diff 报告显示对比范围
- [ ] 报告文件路径正确（不是临时路径）

### 错误处理测试

- [ ] 不在 Git 仓库执行：友好提示
- [ ] Commit 不存在：友好提示
- [ ] 跳过二进制文件：日志记录
- [ ] 跳过删除的文件：日志记录

### 跨平台测试

- [ ] Windows: 路径处理正确
- [ ] Windows: 临时文件创建和清理
- [ ] Linux: 路径处理正确
- [ ] Linux: 临时文件创建和清理

## 测试数据准备

### 创建测试仓库脚本

```bash
#!/bin/bash
# setup_test_repo.sh

# 创建测试目录
mkdir -p /tmp/test_git_check
cd /tmp/test_git_check

# 初始化 Git
git init
git config user.name "Test User"
git config user.email "test@example.com"

# 创建包含问题的文件
cat > bad_code.py << 'EOF'
def very_long_function():
    # 超过 30 行的函数
    x = 0  # 魔数
    for i in range(100):
        x += i
    # ... 更多行 ...
    return x
EOF

# 提交
git add bad_code.py
git commit -m "Add bad code for testing"

# 创建第二个 commit
cat > another_bad.py << 'EOF'
def another_function():
    magic_number = 42  # 魔数
    return magic_number
EOF

git add another_bad.py
git commit -m "Add another bad file"

echo "测试仓库创建完成: /tmp/test_git_check"
```

## 测试执行计划

1. **开发阶段**: 每个 Phase 完成后运行相关单元测试
2. **集成阶段**: 所有 Phase 完成后运行集成测试
3. **发布前**: 完整测试套件 + 手工测试
4. **跨平台**: Windows 和 Linux 各测试一次

## 成功标准

- ✅ 所有单元测试通过
- ✅ 所有集成测试通过
- ✅ 代码覆盖率 > 80%
- ✅ 手工测试清单全部完成
- ✅ Windows 和 Linux 测试通过
- ✅ 无已知严重 Bug
