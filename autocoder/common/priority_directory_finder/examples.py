"""
优先级目录查找器使用示例

展示不同的使用场景和配置方式。
"""

import os
import tempfile
from typing import List

from . import (
    PriorityDirectoryFinder, QuickFinder, FinderConfig, DirectoryConfig,
    SearchStrategy, ValidationMode, FileTypeFilter,
    find_command_directories, create_file_filter
)


def example_basic_usage():
    """基础使用示例"""
    print("=== 基础使用示例 ===")
    
    # 简单查找命令目录
    result = find_command_directories()
    print(f"查找命令目录: 成功={result.success}")
    if result.success:
        print(f"选择的目录: {result.primary_directory}")
    
    # 手动配置查找器
    config = FinderConfig()
    config.add_directory(".autocodercommands", priority=1)
    config.add_directory("~/commands", priority=2)
    
    finder = PriorityDirectoryFinder(config)
    result = finder.find_directories()
    print(f"手动配置查找: 成功={result.success}")
    

def example_different_strategies():
    """不同查找策略示例"""
    print("\n=== 不同查找策略示例 ===")
    
    # 创建测试目录
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dirs = []
        for i in range(3):
            dir_path = os.path.join(temp_dir, f"test_{i}")
            os.makedirs(dir_path)
            # 创建测试文件
            with open(os.path.join(dir_path, f"file_{i}.md"), 'w') as f:
                f.write(f"Test file {i}")
            test_dirs.append(dir_path)
        
        config = FinderConfig()
        for i, dir_path in enumerate(test_dirs):
            config.add_directory(dir_path, priority=i)
        
        # 测试不同策略
        strategies = [
            (SearchStrategy.FIRST_MATCH, "顺序查找"),
            (SearchStrategy.LIST_ALL, "全部查找"),
            (SearchStrategy.MERGE_ALL, "合并查找")
        ]
        
        for strategy, name in strategies:
            config.strategy = strategy
            finder = PriorityDirectoryFinder(config)
            result = finder.find_directories()
            print(f"{name}: 找到 {len(result.selected_directories)} 个目录")


def example_file_type_filtering():
    """文件类型过滤示例"""
    print("\n=== 文件类型过滤示例 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建不同类型的文件
        md_dir = os.path.join(temp_dir, "md_files")
        py_dir = os.path.join(temp_dir, "py_files")
        empty_dir = os.path.join(temp_dir, "empty")
        
        os.makedirs(md_dir)
        os.makedirs(py_dir)
        os.makedirs(empty_dir)
        
        # 创建测试文件
        with open(os.path.join(md_dir, "test.md"), 'w') as f:
            f.write("# Test")
        with open(os.path.join(py_dir, "test.py"), 'w') as f:
            f.write("print('test')")
        
        # 配置不同的文件过滤器
        filters = [
            (create_file_filter(extensions=[".md"]), "Markdown文件"),
            (create_file_filter(extensions=[".py"]), "Python文件"),
            (create_file_filter(extensions=[".txt"]), "文本文件"),
        ]
        
        for file_filter, description in filters:
            config = FinderConfig()
            config.add_directory(md_dir, priority=1, 
                               validation_mode=ValidationMode.HAS_SPECIFIC_FILES,
                               file_filter=file_filter)
            config.add_directory(py_dir, priority=2,
                               validation_mode=ValidationMode.HAS_SPECIFIC_FILES, 
                               file_filter=file_filter)
            config.add_directory(empty_dir, priority=3,
                               validation_mode=ValidationMode.HAS_SPECIFIC_FILES,
                               file_filter=file_filter)
            
            finder = PriorityDirectoryFinder(config)
            result = finder.find_directories()
            print(f"{description}: 找到目录 = {result.primary_directory or 'None'}")


def example_custom_validation():
    """自定义验证示例"""
    print("\n=== 自定义验证示例 ===")
    
    def has_large_files(directory: str) -> bool:
        """检查目录是否包含大文件（>1KB）"""
        try:
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isfile(item_path) and os.path.getsize(item_path) > 1024:
                    return True
            return False
        except:
            return False
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建小文件目录
        small_dir = os.path.join(temp_dir, "small_files")
        os.makedirs(small_dir)
        with open(os.path.join(small_dir, "small.txt"), 'w') as f:
            f.write("small")
        
        # 创建大文件目录
        large_dir = os.path.join(temp_dir, "large_files") 
        os.makedirs(large_dir)
        with open(os.path.join(large_dir, "large.txt"), 'w') as f:
            f.write("x" * 2048)  # 2KB文件
        
        config = FinderConfig()
        config.add_directory(small_dir, priority=1,
                           validation_mode=ValidationMode.CUSTOM,
                           custom_validator=has_large_files)
        config.add_directory(large_dir, priority=2,
                           validation_mode=ValidationMode.CUSTOM,
                           custom_validator=has_large_files)
        
        finder = PriorityDirectoryFinder(config)
        result = finder.find_directories()
        print(f"包含大文件的目录: {result.primary_directory or 'None'}")


def example_standard_paths():
    """标准路径模式示例"""
    print("\n=== 标准路径模式示例 ===")
    
    # 使用QuickFinder查找标准结构
    result = QuickFinder.find_standard_directories(
        base_name=".autocodercommands",
        file_extensions=["md"],
        strategy=SearchStrategy.LIST_ALL
    )
    
    print(f"标准命令目录查找: 成功={result.success}")
    print(f"所有有效目录: {result.all_valid_directories}")
    
    if result.metadata:
        print("目录配置详情:")
        for config in result.metadata.get("directory_configs", []):
            print(f"  {config['path']} -> {config['expanded_path']} (有效: {config['is_valid']})")


def example_file_collection():
    """文件收集示例"""
    print("\n=== 文件收集示例 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试目录和文件
        for i in range(2):
            sub_dir = os.path.join(temp_dir, f"dir_{i}")
            os.makedirs(sub_dir)
            for j in range(3):
                with open(os.path.join(sub_dir, f"file_{i}_{j}.md"), 'w') as f:
                    f.write(f"Content {i}-{j}")
        
        # 查找目录
        config = FinderConfig(strategy=SearchStrategy.LIST_ALL)
        for i in range(2):
            config.add_directory(os.path.join(temp_dir, f"dir_{i}"))
        
        finder = PriorityDirectoryFinder(config)
        result = finder.find_directories()
        
        # 收集文件
        md_filter = create_file_filter(extensions=[".md"])
        files = finder.collect_files_from_directories(
            result.selected_directories, 
            md_filter
        )
        
        print(f"收集到的Markdown文件: {len(files)}")
        for file_path in files:
            print(f"  {os.path.basename(file_path)}")


def main():
    """运行所有示例"""
    examples = [
        example_basic_usage,
        example_different_strategies,
        example_file_type_filtering,
        example_custom_validation,
        example_standard_paths,
        example_file_collection,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"运行示例 {example.__name__} 时发生错误: {e}")
    
    print("\n=== 所有示例运行完成 ===")


if __name__ == "__main__":
    main() 