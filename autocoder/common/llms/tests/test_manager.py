import unittest
import tempfile
import json
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock

from ..manager import LLMManager
from ..schema import LLMModel


class TestLLMManager(unittest.TestCase):
    """LLMManager 单元测试"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时目录和文件
        self.temp_dir = tempfile.mkdtemp()
        self.models_json = Path(self.temp_dir) / "models.json"
        self.models_json.parent.mkdir(parents=True, exist_ok=True)
        
        # 创建测试用的模型配置
        self.test_models = [
            {
                "name": "test/model1",
                "model_name": "test-model-1",
                "model_type": "saas/openai",
                "base_url": "https://test.api.com/v1",
                "context_window": 32768,
                "max_output_tokens": 4096
            }
        ]
        
        # 写入测试配置
        with open(self.models_json, 'w') as f:
            json.dump(self.test_models, f)
        
        # 创建管理器实例，使用临时目录
        self.manager = LLMManager(str(self.models_json))
    
    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_model(self):
        """测试获取模型"""
        # 获取存在的模型
        model = self.manager.get_model("test/model1")
        self.assertIsInstance(model, LLMModel)
        self.assertIsNotNone(model)
        if model:  # Type guard
            self.assertEqual(model.name, "test/model1")
            self.assertEqual(model.model_name, "test-model-1")
        
        # 获取不存在的模型
        model = self.manager.get_model("non/existent")
        self.assertIsNone(model)
    
    def test_get_all_models(self):
        """测试获取所有模型"""
        models = self.manager.get_all_models()
        self.assertIsInstance(models, dict)
        self.assertGreater(len(models), 0)
        
        # 应该包含测试模型
        self.assertIn("test/model1", models)
        
        # 应该包含一些默认模型
        self.assertIn("deepseek/v3", models)
    
    def test_add_models(self):
        """测试添加模型"""
        new_models = [{
            "name": "test/model2",
            "model_name": "test-model-2",
            "model_type": "saas/openai",
            "base_url": "https://test2.api.com/v1",
            "context_window": 65536
        }]
        
        self.manager.add_models(new_models)  # type: ignore
        
        # 验证模型已添加
        model = self.manager.get_model("test/model2")
        self.assertIsNotNone(model)
        if model:  # Type guard
            self.assertEqual(model.name, "test/model2")
            self.assertEqual(model.context_window, 65536)
    
    def test_has_key(self):
        """测试密钥检查"""
        # 没有密钥的模型
        self.assertFalse(self.manager.has_key("test/model1"))
        
        # 使用 manager 的 update_model_with_api_key 方法来保存密钥
        result = self.manager.update_model_with_api_key("test/model1", "test-api-key")
        self.assertTrue(result)
        
        # 现在应该有密钥了
        self.assertTrue(self.manager.has_key("test/model1"))
    
    def test_update_price(self):
        """测试价格更新"""
        # 更新输入价格
        result = self.manager.update_input_price("test/model1", 1.5)
        self.assertTrue(result)
        
        model = self.manager.get_model("test/model1")
        self.assertIsNotNone(model)
        if model:
            self.assertEqual(model.input_price, 1.5)
        
        # 更新输出价格
        result = self.manager.update_output_price("test/model1", 3.0)
        self.assertTrue(result)
        
        model = self.manager.get_model("test/model1")
        self.assertIsNotNone(model)
        if model:
            self.assertEqual(model.output_price, 3.0)
        
        # 同时更新
        result = self.manager.update_price("test/model1", input_price=2.0, output_price=4.0)
        self.assertTrue(result)
        
        model = self.manager.get_model("test/model1")
        self.assertIsNotNone(model)
        if model:
            self.assertEqual(model.input_price, 2.0)
            self.assertEqual(model.output_price, 4.0)
    
    def test_cost_estimate(self):
        """测试成本估算"""
        # 设置价格
        self.manager.update_price("test/model1", input_price=1.0, output_price=2.0)
        
        # 估算成本
        cost = self.manager.get_cost_estimate("test/model1", 
                                            input_tokens=1_000_000,
                                            output_tokens=500_000)
        
        # 验证计算：1M * $1 + 0.5M * $2 = $2.0
        self.assertEqual(cost, 2.0)
        
        # 测试不存在的模型
        cost = self.manager.get_cost_estimate("non/existent", 
                                            input_tokens=1000,
                                            output_tokens=500)
        self.assertIsNone(cost)
    
    def test_check_model_exists(self):
        """测试模型存在性检查"""
        self.assertTrue(self.manager.check_model_exists("test/model1"))
        self.assertFalse(self.manager.check_model_exists("non/existent"))
        
        # 测试默认模型
        self.assertTrue(self.manager.check_model_exists("deepseek/v3"))
    
    def test_update_model(self):
        """测试更新模型信息"""
        # 更新模型描述
        result = self.manager.update_model("test/model1", {
            "description": "Updated test model",
            "input_price": 2.5
        })
        
        self.assertIsNotNone(result)
        
        # 验证更新
        model = self.manager.get_model("test/model1")
        self.assertIsNotNone(model)
        if model:
            self.assertEqual(model.description, "Updated test model")
            self.assertEqual(model.input_price, 2.5)
        
        # 测试更新不存在的模型
        result = self.manager.update_model("non/existent", {"description": "test"})
        self.assertIsNone(result)
    
    def test_get_model_info_compatibility(self):
        """测试兼容性接口"""
        # lite 模式应该返回模型信息
        model_info = self.manager.get_model_info("test/model1", "lite")
        self.assertIsNotNone(model_info)
        self.assertIsInstance(model_info, dict)
        if model_info:
            self.assertEqual(model_info["name"], "test/model1")
        
        # pro 模式应该返回 None
        model_info = self.manager.get_model_info("test/model1", "pro")
        self.assertIsNone(model_info)
        
        # 不存在的模型应该返回 None
        model_info = self.manager.get_model_info("non/existent", "lite")
        self.assertIsNone(model_info)
    
    @patch('autocoder.common.llms.factory.byzerllm.SimpleByzerLLM')
    def test_get_single_llm_lite(self, mock_llm_class):
        """测试 lite 模式下获取 LLM 实例"""
        # 准备模拟对象
        mock_instance = MagicMock()
        mock_llm_class.return_value = mock_instance
        
        # 添加带密钥的模型
        model_with_key = {
            "name": "test/model_key",
            "model_name": "test-model-key",
            "model_type": "saas/openai",
            "base_url": "https://test.api.com/v1",
            "api_key": "test-key-123"
        }
        self.manager.add_models([model_with_key])
        
        # 获取 LLM 实例
        result = self.manager.get_single_llm("test/model_key", "lite")
        
        # 验证调用
        self.assertIsNotNone(result)
        mock_llm_class.assert_called_once_with(default_model_name="test/model_key")
        mock_instance.deploy.assert_called_once()
        
        # 验证 deploy 参数
        call_args = mock_instance.deploy.call_args
        self.assertEqual(call_args[1]['udf_name'], "test/model_key")
        self.assertEqual(call_args[1]['pretrained_model_type'], "saas/openai")
    
    def test_get_single_llm_no_key(self):
        """测试没有密钥的模型获取 LLM 实例"""
        # 尝试获取没有密钥的模型，现在应该抛出 ValueError
        with self.assertRaises(ValueError) as context:
            self.manager.get_single_llm("test/model1", "lite")
        
        error_message = str(context.exception)
        self.assertIn("Failed to create LLM instance", error_message)
        self.assertIn("test/model1", error_message)
        self.assertIn("has no API key configured", error_message)
    
    def test_get_single_llm_multiple_models(self):
        """测试多个模型名称的处理"""
        # 添加带密钥的模型
        model_with_key = {
            "name": "test/model_key",
            "model_name": "test-model-key",
            "model_type": "saas/openai",
            "base_url": "https://test.api.com/v1",
            "api_key": "test-key-123"
        }
        self.manager.add_models([model_with_key])
        
        # 测试多个模型名称，第一个没有密钥，第二个有密钥
        with patch('autocoder.common.llms.factory.byzerllm.SimpleByzerLLM') as mock_llm_class:
            mock_instance = MagicMock()
            mock_llm_class.return_value = mock_instance
            
            result = self.manager.get_single_llm("test/model1,test/model_key", "lite")
            
            # 应该跳过第一个模型，使用第二个模型
            self.assertIsNotNone(result)
            mock_llm_class.assert_called_once_with(default_model_name="test/model_key")
    
    def test_remove_model(self):
        """测试删除模型"""
        # 添加一个自定义模型
        custom_model = {
            "name": "test/removable",
            "model_name": "test-removable",
            "model_type": "saas/openai",
            "base_url": "https://test.com/v1"
        }
        self.manager.add_models([custom_model])  # type: ignore
        
        # 验证模型已添加
        self.assertTrue(self.manager.check_model_exists("test/removable"))
        
        # 删除模型
        result = self.manager.remove_model("test/removable")
        self.assertTrue(result)
        
        # 验证模型已被删除
        self.assertFalse(self.manager.check_model_exists("test/removable"))
    
    def test_remove_default_model(self):
        """测试删除默认模型（应该失败）"""
        # 尝试删除默认模型
        result = self.manager.remove_model("deepseek/v3")
        self.assertFalse(result)
        
        # 验证默认模型仍然存在
        self.assertTrue(self.manager.check_model_exists("deepseek/v3"))
    
    def test_remove_nonexistent_model(self):
        """测试删除不存在的模型"""
        result = self.manager.remove_model("non/existent")
        self.assertFalse(result)
    
    def test_get_single_llm_detailed_error(self):
        """测试 get_single_llm 在失败时抛出详细错误信息"""
        # 尝试获取不存在的模型
        with self.assertRaises(ValueError) as context:
            self.manager.get_single_llm("non/existent", "lite")
        
        error_message = str(context.exception)
        self.assertIn("Failed to create LLM instance", error_message)
        self.assertIn("non/existent", error_message)
        self.assertIn("Model 'non/existent' not found", error_message)
        
        # 尝试获取存在但没有密钥的模型
        with self.assertRaises(ValueError) as context:
            self.manager.get_single_llm("test/model1", "lite")
        
        error_message = str(context.exception)
        self.assertIn("Failed to create LLM instance", error_message)
        self.assertIn("test/model1", error_message)
        self.assertIn("has no API key configured", error_message)
        
        # 尝试获取多个模型，都不可用
        with self.assertRaises(ValueError) as context:
            self.manager.get_single_llm("non/existent1,test/model1,non/existent2", "lite")
        
        error_message = str(context.exception)
        self.assertIn("Failed to create LLM instance", error_message)
        self.assertIn("non/existent1,test/model1,non/existent2", error_message)
        self.assertIn("Model 'non/existent1' not found", error_message)
        self.assertIn("Model 'test/model1': Model test/model1 has no API key configured", error_message)
        self.assertIn("Model 'non/existent2' not found", error_message)


if __name__ == '__main__':
    unittest.main() 