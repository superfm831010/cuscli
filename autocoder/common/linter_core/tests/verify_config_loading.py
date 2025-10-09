

"""
验证 LinterManager 配置文件自动加载功能的脚本

这个脚本演示了如何使用新的配置文件自动加载功能，
并测试不同的配置文件位置和格式。
"""

import os
import json
import yaml
import tempfile
import shutil
from pathlib import Path

from autocoder.common.linter_core.linter_manager import LinterManager


def create_test_config_directories():
    """创建测试配置目录结构"""
    print("=== 创建测试配置目录结构 ===")
    
    # 创建临时目录作为项目根目录
    project_root = tempfile.mkdtemp(prefix="linter_test_")
    print(f"项目根目录: {project_root}")
    
    # 创建不同优先级的配置目录
    config_dirs = {
        "project_level": os.path.join(project_root, ".autocoderlinters"),
        "project_auto_coder": os.path.join(project_root, ".auto-coder", ".autocoderlinters"),
        "global_level": os.path.expanduser("~/.auto-coder/.autocoderlinters")
    }
    
    for name, path in config_dirs.items():
        os.makedirs(path, exist_ok=True)
        print(f"创建目录: {name} -> {path}")
    
    return project_root, config_dirs


def create_sample_configs(config_dirs):
    """创建示例配置文件"""
    print("\n=== 创建示例配置文件 ===")
    
    # 项目级配置（最高优先级）
    project_config = {
        "max_workers": 8,
        "timeout": 600,
        "python_config": {
            "use_mypy": True,
            "flake8_args": ["--max-line-length=120"]
        },
        "source": "project_level"
    }
    
    project_config_file = os.path.join(config_dirs["project_level"], "config.json")
    with open(project_config_file, 'w') as f:
        json.dump(project_config, f, indent=2)
    print(f"创建项目级配置: {project_config_file}")
    
    # .auto-coder 级配置（中等优先级）
    auto_coder_config = {
        "max_workers": 6,
        "timeout": 500,
        "typescript_config": {
            "use_eslint": True,
            "tsc_args": ["--strict"]
        },
        "source": "auto_coder_level"
    }
    
    auto_coder_config_file = os.path.join(config_dirs["project_auto_coder"], "config.yaml")
    with open(auto_coder_config_file, 'w') as f:
        yaml.dump(auto_coder_config, f)
    print(f"创建 .auto-coder 级配置: {auto_coder_config_file}")
    
    # 全局配置（最低优先级）
    global_config = {
        "max_workers": 4,
        "timeout": 300,
        "java_config": {
            "javac_args": ["-Xlint:all"]
        },
        "source": "global_level"
    }
    
    global_config_file = os.path.join(config_dirs["global_level"], "config.yaml")
    with open(global_config_file, 'w') as f:
        yaml.dump(global_config, f)
    print(f"创建全局配置: {global_config_file}")
    
    return {
        "project": project_config,
        "auto_coder": auto_coder_config,
        "global": global_config
    }


def test_config_loading_priority(project_root, config_dirs, sample_configs):
    """测试配置加载优先级"""
    print("\n=== 测试配置加载优先级 ===")
    
    # 保存当前工作目录
    original_cwd = os.getcwd()
    
    try:
        # 切换到项目目录
        os.chdir(project_root)
        
        # 测试1: 所有配置文件都存在，应该加载项目级配置
        print("\n1. 测试所有配置文件都存在的情况:")
        manager = LinterManager()
        print(f"   加载的配置源: {manager.global_config.get('source', 'unknown')}")
        print(f"   max_workers: {manager.max_workers}")
        print(f"   timeout: {manager.timeout}")
        assert manager.global_config['source'] == 'project_level', "应该加载项目级配置"
        
        # 测试2: 删除项目级配置，应该加载 .auto-coder 级配置
        print("\n2. 测试删除项目级配置后:")
        os.remove(os.path.join(config_dirs["project_level"], "config.json"))
        manager = LinterManager()
        print(f"   加载的配置源: {manager.global_config.get('source', 'unknown')}")
        print(f"   max_workers: {manager.max_workers}")
        print(f"   timeout: {manager.timeout}")
        assert manager.global_config['source'] == 'auto_coder_level', "应该加载 .auto-coder 级配置"
        
        # 测试3: 删除 .auto-coder 级配置，应该加载全局配置
        print("\n3. 测试删除 .auto-coder 级配置后:")
        os.remove(os.path.join(config_dirs["project_auto_coder"], "config.yaml"))
        manager = LinterManager()
        print(f"   加载的配置源: {manager.global_config.get('source', 'unknown')}")
        print(f"   max_workers: {manager.max_workers}")
        print(f"   timeout: {manager.timeout}")
        assert manager.global_config['source'] == 'global_level', "应该加载全局配置"
        
        # 测试4: 删除所有配置文件，应该使用默认配置
        print("\n4. 测试删除所有配置文件后:")
        os.remove(os.path.join(config_dirs["global_level"], "config.yaml"))
        manager = LinterManager()
        print(f"   配置为空: {manager.global_config == {}}")
        print(f"   max_workers (默认): {manager.max_workers}")
        print(f"   timeout (默认): {manager.timeout}")
        assert manager.global_config == {}, "应该使用空配置"
        assert manager.max_workers == 4, "应该使用默认 max_workers"
        assert manager.timeout == 300, "应该使用默认 timeout"
        
    finally:
        # 恢复原始工作目录
        os.chdir(original_cwd)


def test_different_config_formats(project_root):
    """测试不同的配置文件格式"""
    print("\n=== 测试不同的配置文件格式 ===")
    
    original_cwd = os.getcwd()
    
    try:
        os.chdir(project_root)
        
        # 创建配置目录
        config_dir = os.path.join(project_root, ".autocoderlinters")
        os.makedirs(config_dir, exist_ok=True)
        
        # 测试 JSON 格式
        print("\n1. 测试 JSON 格式:")
        json_config = {
            "max_workers": 10,
            "format": "json",
            "python_config": {"use_mypy": True}
        }
        
        json_file = os.path.join(config_dir, "config.json")
        with open(json_file, 'w') as f:
            json.dump(json_config, f)
        
        manager = LinterManager()
        print(f"   格式: {manager.global_config.get('format')}")
        print(f"   max_workers: {manager.max_workers}")
        assert manager.global_config['format'] == 'json'
        
        # 清理并测试 YAML 格式
        os.remove(json_file)
        
        print("\n2. 测试 YAML 格式:")
        yaml_config = {
            "max_workers": 12,
            "format": "yaml",
            "typescript_config": {"use_eslint": True}
        }
        
        yaml_file = os.path.join(config_dir, "config.yaml")
        with open(yaml_file, 'w') as f:
            yaml.dump(yaml_config, f)
        
        manager = LinterManager()
        print(f"   格式: {manager.global_config.get('format')}")
        print(f"   max_workers: {manager.max_workers}")
        assert manager.global_config['format'] == 'yaml'
        
        # 清理并测试 YML 格式
        os.remove(yaml_file)
        
        print("\n3. 测试 YML 格式:")
        yml_config = {
            "max_workers": 14,
            "format": "yml",
            "java_config": {"javac_args": ["-Xlint:all"]}
        }
        
        yml_file = os.path.join(config_dir, "config.yml")
        with open(yml_file, 'w') as f:
            yaml.dump(yml_config, f)
        
        manager = LinterManager()
        print(f"   格式: {manager.global_config.get('format')}")
        print(f"   max_workers: {manager.max_workers}")
        assert manager.global_config['format'] == 'yml'
        
    finally:
        os.chdir(original_cwd)


def test_explicit_config_override():
    """测试显式配置覆盖自动加载"""
    print("\n=== 测试显式配置覆盖自动加载 ===")
    
    explicit_config = {
        "max_workers": 20,
        "timeout": 1000,
        "source": "explicit"
    }
    
    manager = LinterManager(explicit_config)
    print(f"配置源: {manager.global_config.get('source')}")
    print(f"max_workers: {manager.max_workers}")
    print(f"timeout: {manager.timeout}")
    
    assert manager.global_config['source'] == 'explicit'
    assert manager.max_workers == 20
    assert manager.timeout == 1000


def cleanup_test_directories(project_root, config_dirs):
    """清理测试目录"""
    print("\n=== 清理测试目录 ===")
    
    # 删除项目根目录
    if os.path.exists(project_root):
        shutil.rmtree(project_root)
        print(f"删除项目目录: {project_root}")
    
    # 删除全局配置目录（如果是我们创建的）
    global_dir = config_dirs["global_level"]
    if os.path.exists(global_dir):
        try:
            shutil.rmtree(global_dir)
            print(f"删除全局配置目录: {global_dir}")
        except OSError:
            print(f"无法删除全局配置目录: {global_dir} (可能有其他文件)")


def main():
    """主函数"""
    print("开始验证 LinterManager 配置文件自动加载功能")
    print("=" * 60)
    
    try:
        # 创建测试环境
        project_root, config_dirs = create_test_config_directories()
        sample_configs = create_sample_configs(config_dirs)
        
        # 运行测试
        test_config_loading_priority(project_root, config_dirs, sample_configs)
        test_different_config_formats(project_root)
        test_explicit_config_override()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！配置文件自动加载功能工作正常。")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        raise
    
    finally:
        # 清理测试环境
        if 'project_root' in locals() and 'config_dirs' in locals():
            cleanup_test_directories(project_root, config_dirs)
    
    print("\n验证完成！")


if __name__ == '__main__':
    main()

