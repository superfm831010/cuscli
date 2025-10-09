import os
import json
import platform
import time
from typing import Dict, Optional, Any, List
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime

# 跨平台文件锁导入
try:
    import fcntl
except ImportError:
    fcntl = None

try:
    import msvcrt
except ImportError:
    msvcrt = None


RAGS_JSON = Path.home() / ".auto-coder" / "keys" / "rags_config.json"


class RAGConfigManager:
    """RAG配置管理器，支持并发安全的增删改查操作"""

    def __init__(self, config_path: str = str(RAGS_JSON)):
        self.config_path = config_path
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """确保配置目录存在"""
        config_path = Path(self.config_path)
        config_dir = config_path.parent
        config_dir.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _file_lock(self, mode="r"):
        """
        文件锁上下文管理器，确保并发安全
        支持Unix (fcntl) 和 Windows (msvcrt) 系统
        """
        # 确保文件存在
        config_path = Path(self.config_path)
        if not config_path.exists():
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                json.dump({}, f)

        file_handle = open(config_path, mode)
        lock_acquired = False

        try:
            # 尝试获取文件锁
            if platform.system() != "Windows":
                # Unix系统使用fcntl
                if fcntl is not None:
                    if "w" in mode or "a" in mode or "+" in mode:
                        fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX)  # 独占锁
                    else:
                        fcntl.flock(file_handle.fileno(), fcntl.LOCK_SH)  # 共享锁
                    lock_acquired = True
            else:
                # Windows系统的文件锁实现
                if msvcrt is not None:
                    try:
                        # 在Windows上，我们使用独占锁来简化实现
                        # msvcrt.locking 参数: fd, mode, nbytes
                        # LK_NBLCK: 非阻塞独占锁
                        # LK_LOCK: 阻塞独占锁
                        max_attempts = 10
                        for attempt in range(max_attempts):
                            try:
                                # 尝试锁定文件的第一个字节
                                file_handle.seek(0)
                                msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
                                lock_acquired = True
                                break
                            except IOError:
                                # 如果锁被占用，等待一小段时间后重试
                                if attempt < max_attempts - 1:
                                    time.sleep(0.1)
                                else:
                                    # 最后一次尝试使用阻塞锁
                                    try:
                                        file_handle.seek(0)
                                        msvcrt.locking(
                                            file_handle.fileno(), msvcrt.LK_LOCK, 1
                                        )
                                        lock_acquired = True
                                    except IOError:
                                        # 如果仍然失败，继续执行但不使用锁
                                        pass
                    except Exception:
                        # 如果出现任何异常，继续执行但不使用锁
                        pass

            # 重置文件位置到开始
            file_handle.seek(0)
            yield file_handle

        finally:
            try:
                # 释放文件锁
                if lock_acquired:
                    if platform.system() != "Windows":
                        if fcntl is not None:
                            fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
                    else:
                        if msvcrt is not None:
                            try:
                                file_handle.seek(0)
                                msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
                            except IOError:
                                # 忽略解锁错误
                                pass
            except Exception:
                # 忽略释放锁时的错误
                pass
            finally:
                file_handle.close()

    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        """
        try:
            with self._file_lock("r") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_config(self, config: Dict[str, Any]):
        """
        保存配置文件
        """
        with self._file_lock("w") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def create(self, name: str, config: Dict[str, Any]) -> bool:
        """
        创建新的RAG服务配置

        Args:
            name: RAG服务名称
            config: 配置字典

        Returns:
            bool: 创建成功返回True，如果名称已存在返回False
        """
        all_configs = self._load_config()

        if name in all_configs:
            return False

        # 确保配置包含必要的字段
        config["name"] = name
        if "status" not in config:
            config["status"] = "stopped"
        if "created_at" not in config:
            config["created_at"] = datetime.now().isoformat()
        config["updated_at"] = datetime.now().isoformat()

        all_configs[name] = config
        self._save_config(all_configs)
        return True

    def read(self, name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        读取RAG服务配置

        Args:
            name: RAG服务名称，如果为None则返回所有配置

        Returns:
            Dict: 配置字典，如果name不存在或为None且无配置则返回None
        """
        all_configs = self._load_config()

        if name is None:
            return all_configs if all_configs else None

        return all_configs.get(name)

    def update(self, name: str, config: Dict[str, Any]) -> bool:
        """
        更新RAG服务配置

        Args:
            name: RAG服务名称
            config: 新的配置字典（会与现有配置合并）

        Returns:
            bool: 更新成功返回True，如果名称不存在返回False
        """
        all_configs = self._load_config()

        if name not in all_configs:
            return False

        # 合并配置
        existing_config = all_configs[name]
        existing_config.update(config)
        existing_config["name"] = name  # 确保名称不被覆盖
        existing_config["updated_at"] = datetime.now().isoformat()

        all_configs[name] = existing_config
        self._save_config(all_configs)
        return True

    def delete(self, name: str) -> bool:
        """
        删除RAG服务配置

        Args:
            name: RAG服务名称

        Returns:
            bool: 删除成功返回True，如果名称不存在返回False
        """
        all_configs = self._load_config()

        if name not in all_configs:
            return False

        del all_configs[name]
        self._save_config(all_configs)
        return True

    def list_names(self) -> List[str]:
        """
        获取所有RAG服务名称列表

        Returns:
            List[str]: 服务名称列表
        """
        all_configs = self._load_config()
        return list(all_configs.keys())

    def exists(self, name: str) -> bool:
        """
        检查RAG服务是否存在

        Args:
            name: RAG服务名称

        Returns:
            bool: 存在返回True，否则返回False
        """
        all_configs = self._load_config()
        return name in all_configs

    def get_by_port(self, port: int) -> Optional[Dict[str, Any]]:
        """
        根据端口号查找RAG服务配置

        Args:
            port: 端口号

        Returns:
            Dict: 配置字典，如果未找到返回None
        """
        all_configs = self._load_config()

        for name, config in all_configs.items():
            if config.get("port") == port:
                return config

        return None

    def get_running_services(self) -> Dict[str, Any]:
        """
        获取所有运行中的RAG服务

        Returns:
            Dict: 运行中的服务配置字典
        """
        all_configs = self._load_config()
        running_services = {}

        for name, config in all_configs.items():
            if config.get("status") == "running":
                running_services[name] = config

        return running_services

    def update_status(self, name: str, status: str, **kwargs) -> bool:
        """
        更新RAG服务状态

        Args:
            name: RAG服务名称
            status: 新状态 ('running', 'stopped', 'error', etc.)
            **kwargs: 其他要更新的状态信息（如process_id, stdout_fd等）

        Returns:
            bool: 更新成功返回True，如果名称不存在返回False
        """
        update_data = {"status": status, **kwargs}
        return self.update(name, update_data)

    def cleanup_stopped_services(self):
        """
        清理已停止服务的临时状态信息（如process_id, stdout_fd等）
        """
        all_configs = self._load_config()
        modified = False

        for name, config in all_configs.items():
            if config.get("status") == "stopped":
                # 清理临时状态字段
                temp_fields = [
                    "process_id",
                    "stdout_fd",
                    "stderr_fd",
                    "cache_build_task_id",
                ]
                for field in temp_fields:
                    if field in config:
                        del config[field]
                        modified = True

        if modified:
            self._save_config(all_configs)


# 创建全局实例
rag_manager = RAGConfigManager()


# 便捷函数
def create_rag_config(name: str, config: Dict[str, Any]) -> bool:
    """创建RAG配置的便捷函数"""
    return rag_manager.create(name, config)


def get_rag_config(name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """获取RAG配置的便捷函数"""
    return rag_manager.read(name)


def update_rag_config(name: str, config: Dict[str, Any]) -> bool:
    """更新RAG配置的便捷函数"""
    return rag_manager.update(name, config)


def delete_rag_config(name: str) -> bool:
    """删除RAG配置的便捷函数"""
    return rag_manager.delete(name)


def list_rag_names() -> List[str]:
    """获取所有RAG服务名称的便捷函数"""
    return rag_manager.list_names()


def rag_exists(name: str) -> bool:
    """检查RAG服务是否存在的便捷函数"""
    return rag_manager.exists(name)


def get_rag_by_port(port: int) -> Optional[Dict[str, Any]]:
    """根据端口获取RAG配置的便捷函数"""
    return rag_manager.get_by_port(port)


def get_running_rags() -> Dict[str, Any]:
    """获取运行中RAG服务的便捷函数"""
    return rag_manager.get_running_services()


def update_rag_status(name: str, status: str, **kwargs) -> bool:
    """更新RAG服务状态的便捷函数"""
    return rag_manager.update_status(name, status, **kwargs)
