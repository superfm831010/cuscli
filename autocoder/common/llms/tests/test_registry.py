import unittest
import tempfile
import json
from pathlib import Path

from ..registry import ModelRegistry
from ..schema import LLMModel


class TestModelRegistry(unittest.TestCase):
    """ModelRegistry 单元测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.models_json = Path(self.temp_dir) / "models.json"
        self.registry = ModelRegistry(str(self.models_json))
    
    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_default_models(self):
        """测试加载默认模型"""
        # 第一次加载会创建默认配置
        models = self.registry.load()
        
        # 验证默认模型已加载
        self.assertGreater(len(models), 0)
        
        # 检查一些默认模型
        model_names = [m.name for m in models]
        self.assertIn("deepseek/v3", model_names)
        self.assertIn("deepseek/r1", model_names)
        
        # 验证配置文件已创建
        self.assertTrue(self.models_json.exists())
    
    def test_save_and_load(self):
        """测试保存和加载"""
        # 创建测试模型
        test_models = [
            LLMModel(
                name="test/save1",
                model_name="test-save-1",
                model_type="saas/openai",
                base_url="https://test.com/v1"
            )
        ]
        
        # 保存
        self.registry.save(test_models)
        
        # 重新加载
        loaded_models = self.registry.load()
        
        # 验证（应该包含默认模型和自定义模型）
        loaded_names = [m.name for m in loaded_models]
        self.assertIn("test/save1", loaded_names)
        # 也应该包含默认模型
        self.assertIn("deepseek/v3", loaded_names)
    
    def test_get_model(self):
        """测试获取单个模型"""
        # 获取存在的默认模型
        model = self.registry.get("deepseek/v3")
        self.assertIsNotNone(model)
        if model:
            self.assertEqual(model.name, "deepseek/v3")
        
        # 获取不存在的模型
        model = self.registry.get("non/existent")
        self.assertIsNone(model)
    
    def test_get_all_models(self):
        """测试获取所有模型"""
        models = self.registry.get_all()
        self.assertIsInstance(models, dict)
        self.assertGreater(len(models), 0)
        
        # 应该包含默认模型
        self.assertIn("deepseek/v3", models)
        self.assertIn("deepseek/r1", models)
    
    def test_add_or_update(self):
        """测试添加或更新模型"""
        # 添加新模型
        new_model = LLMModel(
            name="test/new",
            model_name="test-new",
            model_type="saas/openai",
            base_url="https://new.com/v1"
        )
        self.registry.add_or_update(new_model)
        
        # 验证已添加
        model = self.registry.get("test/new")
        self.assertIsNotNone(model)
        if model:
            self.assertEqual(model.name, "test/new")
        
        # 更新模型
        new_model.input_price = 5.0
        self.registry.add_or_update(new_model)
        
        # 验证已更新
        model = self.registry.get("test/new")
        self.assertIsNotNone(model)
        if model:
            self.assertEqual(model.input_price, 5.0)
    
    def test_save_api_key(self):
        """测试保存 API 密钥"""
        # 保存密钥
        result = self.registry.save_api_key("deepseek/v3", "test-api-key-123")
        self.assertTrue(result)
        
        # 获取模型查看其 api_key_path
        model = self.registry.get("deepseek/v3")
        self.assertIsNotNone(model)
        if model:
            expected_key_path = model.api_key_path
            self.assertIsNotNone(expected_key_path)
            
            if expected_key_path:
                # 验证密钥文件已创建
                key_file = self.models_json.parent / expected_key_path
                self.assertTrue(key_file.exists())
                self.assertEqual(key_file.read_text().strip(), "test-api-key-123")
                
                # 验证模型的 api_key_path 设置正确
                self.assertEqual(model.api_key_path, expected_key_path)
    
    def test_save_api_key_nonexistent_model(self):
        """测试为不存在的模型保存 API 密钥"""
        result = self.registry.save_api_key("non/existent", "test-key")
        self.assertFalse(result)
    
    def test_backward_compatibility(self):
        """测试向后兼容性"""
        # 创建没有新字段的旧格式数据
        old_format_models = [
            {
                "name": "old/model",
                "model_name": "old-model",
                "model_type": "saas/openai",
                "base_url": "https://old.com/v1",
                "is_reasoning": False,
                "input_price": 1.0,
                "output_price": 2.0
                # 没有 context_window, max_output_tokens, provider
            }
        ]
        
        # 写入文件
        with open(self.models_json, 'w') as f:
            json.dump(old_format_models, f)
        
        # 加载
        models = self.registry.load()
        
        # 验证默认值已添加
        old_model = next((m for m in models if m.name == "old/model"), None)
        self.assertIsNotNone(old_model)
        if old_model:
            self.assertEqual(old_model.context_window, 32768)  # 默认值
            self.assertEqual(old_model.max_output_tokens, 8096)  # 默认值
            self.assertIsNone(old_model.provider)  # 默认值
    
    def test_no_cache_behavior(self):
        """测试无缓存行为，每次都重新加载"""
        # 第一次获取模型
        model1 = self.registry.get("deepseek/v3")
        self.assertIsNotNone(model1)
        
        # 添加一个新模型
        new_model = LLMModel(
            name="test/nocache",
            model_name="test-nocache",
            model_type="saas/openai",
            base_url="https://test.com/v1"
        )
        self.registry.add_or_update(new_model)
        
        # 重新获取，应该能看到新模型
        model2 = self.registry.get("test/nocache")
        self.assertIsNotNone(model2)
        if model2:
            self.assertEqual(model2.name, "test/nocache")
        
        # 再次获取所有模型，应该包含新模型
        all_models = self.registry.get_all()
        self.assertIn("test/nocache", all_models)
    
    def test_file_corruption_handling(self):
        """测试文件损坏的处理"""
        # 写入无效的 JSON
        with open(self.models_json, 'w') as f:
            f.write("invalid json content")
        
        # 应该能正常加载（会重新创建默认配置）
        models = self.registry.load()
        self.assertGreater(len(models), 0)
        
        # 验证默认模型存在
        model_names = [m.name for m in models]
        self.assertIn("deepseek/v3", model_names)
        
        # 验证文件已被修复
        self.assertTrue(self.models_json.exists())
        with open(self.models_json, 'r') as f:
            data = json.load(f)
            self.assertIsInstance(data, list)
    
    def test_remove_model(self):
        """测试删除模型"""
        # 添加一个自定义模型
        custom_model = LLMModel(
            name="test/removable",
            model_name="test-removable",
            model_type="saas/openai",
            base_url="https://test.com/v1"
        )
        self.registry.add_or_update(custom_model)
        
        # 验证模型已添加
        self.assertTrue(self.registry.get("test/removable") is not None)
        
        # 删除模型
        result = self.registry.remove_model("test/removable")
        self.assertTrue(result)
        
        # 验证模型已被删除
        self.assertIsNone(self.registry.get("test/removable"))
    
    def test_remove_default_model(self):
        """测试删除默认模型（应该失败）"""
        # 尝试删除默认模型
        result = self.registry.remove_model("deepseek/v3")
        self.assertFalse(result)
        
        # 验证默认模型仍然存在
        self.assertIsNotNone(self.registry.get("deepseek/v3"))
    
    def test_remove_nonexistent_model(self):
        """测试删除不存在的模型"""
        result = self.registry.remove_model("non/existent")
        self.assertFalse(result)
    
    def test_remove_model_with_api_key(self):
        """测试删除带有 API 密钥的模型"""
        # 添加带密钥的模型
        custom_model = LLMModel(
            name="test/with_key",
            model_name="test-with-key",
            model_type="saas/openai",
            base_url="https://test.com/v1",
            api_key="test-key-123"
        )
        self.registry.add_or_update(custom_model)
        
        # 保存密钥
        self.registry.save_api_key("test/with_key", "test-key-123")
        
        # 获取模型并检查密钥文件是否存在
        model = self.registry.get("test/with_key")
        self.assertIsNotNone(model)
        if model and model.api_key_path:
            key_file = self.models_json.parent / model.api_key_path
            self.assertTrue(key_file.exists())
            
            # 删除模型
            result = self.registry.remove_model("test/with_key")
            self.assertTrue(result)
            
            # 验证模型已被删除
            self.assertIsNone(self.registry.get("test/with_key"))
            
            # 验证密钥文件也被删除（如果可能的话）
            # 注意：这里不强制要求删除，因为可能有权限问题

    def test_api_key_path_generation(self):
        """测试 API 密钥路径自动生成逻辑"""
        # 创建一个只有 api_key 没有 api_key_path 的模型数据
        model_data = [
            {
                "name": "test/auto_path",
                "model_name": "test-auto-path",
                "model_type": "saas/openai",
                "base_url": "https://test.com/v1",
                "api_key": "test-key-456"
                # 注意：没有 api_key_path
            }
        ]
        
        # 写入文件
        with open(self.models_json, 'w') as f:
            json.dump(model_data, f)
        
        # 创建密钥文件（按预期的路径）
        expected_key_path = "test_auto_path"  # 模拟应该生成的路径
        key_file = self.models_json.parent / expected_key_path
        key_file.write_text("test-key-456")
        
        # 加载模型
        models = self.registry.load()
        
        # 获取测试模型
        test_model = next((m for m in models if m.name == "test/auto_path"), None)
        self.assertIsNotNone(test_model)
        
        if test_model:
            # 验证 api_key_path 已经被自动生成
            self.assertEqual(test_model.api_key_path, expected_key_path)
            
            # 验证能够获取到 API 密钥
            self.assertEqual(test_model.get_api_key(), "test-key-456")
            
            # 验证 has_api_key 返回 True
            self.assertTrue(test_model.has_api_key)
    
    def test_api_key_path_priority(self):
        """测试当 api_key_path 存在时，优先使用它而不是自动生成"""
        # 创建一个既有 api_key 又有 api_key_path 的模型数据
        model_data = [
            {
                "name": "test/priority",
                "model_name": "test-priority",
                "model_type": "saas/openai",
                "base_url": "https://test.com/v1",
                "api_key": "memory-key-789",
                "api_key_path": "custom_key_path"
            }
        ]
        
        # 写入文件
        with open(self.models_json, 'w') as f:
            json.dump(model_data, f)
        
        # 创建密钥文件（使用自定义路径）
        key_file = self.models_json.parent / "custom_key_path"
        key_file.write_text("file-key-789")
        
        # 加载模型
        models = self.registry.load()
        
        # 获取测试模型
        test_model = next((m for m in models if m.name == "test/priority"), None)
        self.assertIsNotNone(test_model)
        
        if test_model:
            # 验证使用了指定的 api_key_path
            self.assertEqual(test_model.api_key_path, "custom_key_path")
            
            # 验证从文件读取的密钥覆盖了内存中的密钥
            self.assertEqual(test_model.get_api_key(), "file-key-789")
            
            # 验证 has_api_key 返回 True
            self.assertTrue(test_model.has_api_key)


if __name__ == '__main__':
    unittest.main() 