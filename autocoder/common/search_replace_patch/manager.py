"""
Search Replace Manager - unified interface for different replacement strategies
"""

from typing import List, Tuple, Optional, Dict, Any
from loguru import logger

from .base import BaseReplacer, ReplaceResult, ReplaceStrategy
from .string_replacer import StringReplacer
from .patch_replacer import PatchReplacer
from .similarity_replacer import SimilarityReplacer


class SearchReplaceManager:
    """搜索替换管理器 - 统一管理多种替换策略"""
    
    def __init__(self, default_strategy: ReplaceStrategy = ReplaceStrategy.STRING):
        """
        初始化搜索替换管理器
        
        Args:
            default_strategy: 默认的替换策略
        """
        self.default_strategy = default_strategy
        self.replacers: Dict[ReplaceStrategy, BaseReplacer] = {}
        self._initialize_replacers()
    
    def _initialize_replacers(self):
        """初始化所有替换器"""
        try:
            # 初始化字符串替换器
            self.replacers[ReplaceStrategy.STRING] = StringReplacer(lenient_mode=True)
            logger.info("Initialized StringReplacer")
        except Exception as e:
            logger.error(f"Failed to initialize StringReplacer: {e}")
        
        try:
            # 初始化补丁替换器
            self.replacers[ReplaceStrategy.PATCH] = PatchReplacer(use_patch_ng=True)
            logger.info("Initialized PatchReplacer")
        except Exception as e:
            logger.error(f"Failed to initialize PatchReplacer: {e}")
        
        try:
            # 初始化相似度替换器
            self.replacers[ReplaceStrategy.SIMILARITY] = SimilarityReplacer(similarity_threshold=0.99)
            logger.info("Initialized SimilarityReplacer")
        except Exception as e:
            logger.error(f"Failed to initialize SimilarityReplacer: {e}")
    
    def get_replacer(self, strategy: ReplaceStrategy) -> Optional[BaseReplacer]:
        """
        获取指定策略的替换器
        
        Args:
            strategy: 替换策略
            
        Returns:
            对应的替换器实例，如果不存在则返回 None
        """
        return self.replacers.get(strategy)
    
    def replace(self, content: str, search_blocks: List[Tuple[str, str]], 
                strategy: Optional[ReplaceStrategy] = None) -> ReplaceResult:
        """
        执行文本替换
        
        Args:
            content: 原始文件内容
            search_blocks: 搜索替换块列表
            strategy: 指定的替换策略，如果为None则使用默认策略
            
        Returns:
            ReplaceResult: 替换结果
        """
        if strategy is None:
            strategy = self.default_strategy
        
        replacer = self.get_replacer(strategy)
        if not replacer:
            return ReplaceResult(
                success=False,
                message=f"Replacer for strategy '{strategy.value}' not available",
                total_count=len(search_blocks)
            )
        
        logger.info(f"Using {strategy.value} strategy for replacement")
        return replacer.replace(content, search_blocks)
    
    def replace_with_fallback(self, content: str, search_blocks: List[Tuple[str, str]], 
                              fallback_strategies: Optional[List[ReplaceStrategy]] = None) -> ReplaceResult:
        """
        使用回退策略进行文本替换
        
        Args:
            content: 原始文件内容
            search_blocks: 搜索替换块列表
            fallback_strategies: 回退策略列表，默认为 [STRING, SIMILARITY, PATCH]
            
        Returns:
            ReplaceResult: 替换结果
        """
        if fallback_strategies is None:
            fallback_strategies = [
                ReplaceStrategy.STRING,
                ReplaceStrategy.SIMILARITY,
                ReplaceStrategy.PATCH,
            ]
        
        last_result = None
        
        for strategy in fallback_strategies:
            replacer = self.get_replacer(strategy)
            if not replacer:
                logger.warning(f"Replacer for strategy '{strategy.value}' not available, skipping")
                continue
            
            if not replacer.can_handle(content, search_blocks):
                logger.warning(f"Replacer '{strategy.value}' cannot handle the given content, skipping")
                continue
            
            logger.info(f"Trying {strategy.value} strategy for replacement")
            result = replacer.replace(content, search_blocks)
            
            if result.success:
                logger.info(f"Successfully replaced using {strategy.value} strategy")
                result.metadata['used_strategy'] = strategy.value
                result.metadata['fallback_used'] = len(fallback_strategies) > 1
                return result
            else:
                logger.warning(f"Failed to replace using {strategy.value} strategy: {result.message}")
                last_result = result
        
        # 如果所有策略都失败了，返回最后一个结果
        if last_result:
            last_result.metadata['all_strategies_failed'] = True
            last_result.metadata['tried_strategies'] = [s.value for s in fallback_strategies]
            return last_result
        
        return ReplaceResult(
            success=False,
            message="No suitable replacer found for the given content",
            total_count=len(search_blocks)
        )
    
    def get_available_strategies(self) -> List[ReplaceStrategy]:
        """
        获取所有可用的替换策略
        
        Returns:
            可用的替换策略列表
        """
        return list(self.replacers.keys())
    
    def set_default_strategy(self, strategy: ReplaceStrategy):
        """
        设置默认替换策略
        
        Args:
            strategy: 新的默认策略
        """
        if strategy in self.replacers:
            self.default_strategy = strategy
            logger.info(f"Default strategy set to {strategy.value}")
        else:
            logger.warning(f"Strategy {strategy.value} not available, default strategy unchanged")
    
    def configure_replacer(self, strategy: ReplaceStrategy, **kwargs):
        """
        配置指定替换器的参数
        
        Args:
            strategy: 替换策略
            **kwargs: 配置参数
        """
        replacer = self.get_replacer(strategy)
        if not replacer:
            logger.warning(f"Replacer for strategy '{strategy.value}' not available")
            return
        
        try:
            if strategy == ReplaceStrategy.STRING and isinstance(replacer, StringReplacer):
                if 'lenient_mode' in kwargs:
                    replacer.lenient_mode = kwargs['lenient_mode']
                    logger.info(f"StringReplacer lenient_mode set to {kwargs['lenient_mode']}")
            
            elif strategy == ReplaceStrategy.PATCH and isinstance(replacer, PatchReplacer):
                if 'use_patch_ng' in kwargs:
                    replacer.use_patch_ng = kwargs['use_patch_ng']
                    replacer._load_patch_module()
                    logger.info(f"PatchReplacer use_patch_ng set to {kwargs['use_patch_ng']}")
            
            elif strategy == ReplaceStrategy.SIMILARITY and isinstance(replacer, SimilarityReplacer):
                if 'similarity_threshold' in kwargs:
                    replacer.set_similarity_threshold(kwargs['similarity_threshold'])
                    
        except Exception as e:
            logger.error(f"Failed to configure {strategy.value} replacer: {e}")
    
    def get_replacer_info(self, strategy: ReplaceStrategy) -> Dict[str, Any]:
        """
        获取替换器信息
        
        Args:
            strategy: 替换策略
            
        Returns:
            替换器信息字典
        """
        replacer = self.get_replacer(strategy)
        if not replacer:
            return {'available': False, 'strategy': strategy.value}
        
        info = {
            'available': True,
            'strategy': strategy.value,
            'class_name': replacer.__class__.__name__
        }
        
        # 添加特定替换器的信息
        try:
            if strategy == ReplaceStrategy.STRING and isinstance(replacer, StringReplacer):
                info['lenient_mode'] = replacer.lenient_mode
            elif strategy == ReplaceStrategy.PATCH and isinstance(replacer, PatchReplacer):
                info['use_patch_ng'] = replacer.use_patch_ng
                info['patch_module_available'] = replacer._patch_module is not None
            elif strategy == ReplaceStrategy.SIMILARITY and isinstance(replacer, SimilarityReplacer):
                info['similarity_threshold'] = replacer.similarity_threshold
        except Exception as e:
            logger.warning(f"Failed to get detailed info for {strategy.value}: {e}")
        
        return info
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取管理器状态
        
        Returns:
            状态信息字典
        """
        return {
            'default_strategy': self.default_strategy.value,
            'available_strategies': [s.value for s in self.get_available_strategies()],
            'replacer_info': {
                strategy.value: self.get_replacer_info(strategy)
                for strategy in ReplaceStrategy
            }
        } 