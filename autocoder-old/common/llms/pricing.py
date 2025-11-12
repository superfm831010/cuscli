from typing import Optional

from .schema import LLMModel
from .registry import ModelRegistry


class PricingManager:
    """模型价格管理器"""
    
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
    
    def update_input_price(self, name: str, price: float) -> bool:
        """
        更新模型输入价格
        
        Args:
            name: 模型名称
            price: 新的输入价格（美元/百万tokens），必须大于等于0
            
        Returns:
            bool: 是否成功更新
            
        Raises:
            ValueError: 如果价格为负数
        """
        if price < 0:
            raise ValueError("价格不能为负数")
        
        model = self.registry.get(name)
        if not model:
            return False
        
        model.input_price = float(price)
        self.registry.add_or_update(model)
        return True
    
    def update_output_price(self, name: str, price: float) -> bool:
        """
        更新模型输出价格
        
        Args:
            name: 模型名称
            price: 新的输出价格（美元/百万tokens），必须大于等于0
            
        Returns:
            bool: 是否成功更新
            
        Raises:
            ValueError: 如果价格为负数
        """
        if price < 0:
            raise ValueError("价格不能为负数")
        
        model = self.registry.get(name)
        if not model:
            return False
        
        model.output_price = float(price)
        self.registry.add_or_update(model)
        return True
    
    def update_prices(self, name: str, input_price: Optional[float] = None, 
                     output_price: Optional[float] = None) -> bool:
        """
        同时更新输入和输出价格
        
        Args:
            name: 模型名称
            input_price: 新的输入价格（可选）
            output_price: 新的输出价格（可选）
            
        Returns:
            bool: 是否成功更新
            
        Raises:
            ValueError: 如果任一价格为负数
        """
        if input_price is not None and input_price < 0:
            raise ValueError("输入价格不能为负数")
        if output_price is not None and output_price < 0:
            raise ValueError("输出价格不能为负数")
        
        model = self.registry.get(name)
        if not model:
            return False
        
        updated = False
        if input_price is not None:
            model.input_price = float(input_price)
            updated = True
        if output_price is not None:
            model.output_price = float(output_price)
            updated = True
        
        if updated:
            self.registry.add_or_update(model)
        
        return updated
    
    def get_cost_estimate(self, name: str, input_tokens: int, output_tokens: int) -> Optional[float]:
        """
        估算使用成本
        
        Args:
            name: 模型名称
            input_tokens: 输入 token 数量
            output_tokens: 输出 token 数量
            
        Returns:
            估算的总成本（美元），如果模型不存在则返回 None
        """
        model = self.registry.get(name)
        if not model:
            return None
        
        # 计算成本：价格单位是 美元/百万tokens
        input_cost = (input_tokens / 1_000_000) * model.input_price
        output_cost = (output_tokens / 1_000_000) * model.output_price
        
        return input_cost + output_cost 