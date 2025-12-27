import hashlib
import json
import os
import time
import platform
import threading
from multiprocessing import Pool
import functools
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
from loguru import logger
from byzerllm import SimpleByzerLLM, ByzerLLM
from autocoder.utils.llms import get_llm_names

try:
    import duckdb
except ImportError:
    logger.error(
        "DuckDB is not installed, please install it using 'pip install duckdb'"
    )
    raise

from autocoder.common import AutoCoderArgs
from autocoder.common import SourceCode
from autocoder.rag.cache.base_cache import (
    BaseCacheManager,
    DeleteEvent,
    AddOrUpdateEvent,
    FileInfo,
    CacheItem,
)
from autocoder.rag.utils import (
    process_file_in_multi_process,
    process_file_local,
)
from autocoder.rag.variable_holder import VariableHolder
from .failed_files_utils import save_failed_files

if platform.system() != "Windows":
    import fcntl
else:
    fcntl = None


default_ignore_dirs = [
    "__pycache__",
    "node_modules",
    "_images",
    ".auto-coder",
    ".cache",
]


def generate_file_md5(file_path: str) -> str:
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


class DuckDBLocalContext:
    def __init__(self, database_path: str):
        self.database_path = database_path
        self._conn = None

    def _install_load_extension(self, ext_list):
        for ext in ext_list:
            self._conn.install_extension(ext)
            self._conn.load_extension(ext)

    def __enter__(self) -> "duckdb.DuckDBPyConnection":
        if not os.path.exists(os.path.dirname(self.database_path)):
            raise ValueError(
                f"Directory {os.path.dirname(self.database_path)} " f"does not exist."
            )

        self._conn = duckdb.connect(self.database_path)
        self._install_load_extension(["json", "fts", "vss"])

        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._conn:
            self._conn.close()


class LocalDuckdbStorage:

    def __init__(
        self,
        llm: Union[ByzerLLM, SimpleByzerLLM] = None,
        database_name: str = ":memory:",
        table_name: str = "documents",
        embed_dim: Optional[int] = None,
        persist_dir: str = "./storage",
        args: Optional[AutoCoderArgs] = None,
    ) -> None:
        self.llm = llm
        self.database_name = database_name
        self.table_name = table_name
        self.embed_dim = embed_dim
        self.persist_dir = persist_dir
        self.cache_dir = os.path.join(self.persist_dir, ".cache")
        self.args = args

        # 缓存投影矩阵，避免每次 embedding 都重新生成
        self._projection_matrix_cache: Dict[Tuple[int, int], np.ndarray] = {}
        # 写入锁，保护并发写入操作
        self._write_lock = threading.Lock()

        logger.info("正在启动 DuckDBVectorStore.")

        if self.database_name != ":memory:":
            self.database_path = os.path.join(self.cache_dir, self.database_name)

        if self.database_name == ":memory:":
            self._conn = duckdb.connect(self.database_name)
            self._install_load_extension(["json", "fts", "vss"])
            self._initialize()
        else:
            if not os.path.exists(self.database_path):
                if not os.path.exists(self.cache_dir):
                    os.makedirs(self.cache_dir)
                self._initialize()
            self._conn = None
        logger.info(
            f"DuckDBVectorStore 初始化完成, 存储目录: {self.cache_dir}, "
            f"数据库名称: {self.database_name}, "
            f"数据表名称: {self.table_name}"
        )

    @classmethod
    def class_name(cls) -> str:
        return "DuckDBVectorStore"

    @property
    def client(self) -> Any:
        """Return client."""
        return self._conn

    def _install_load_extension(self, ext_list):
        for ext in ext_list:
            self._conn.install_extension(ext)
            self._conn.load_extension(ext)

    def _get_projection_matrix(self, source_dim: int, target_dim: int) -> np.ndarray:
        """获取或创建投影矩阵，使用缓存避免重复生成"""
        cache_key = (source_dim, target_dim)
        if cache_key not in self._projection_matrix_cache:
            # 使用固定种子生成投影矩阵
            rng = np.random.RandomState(42)
            self._projection_matrix_cache[cache_key] = rng.randn(
                source_dim, target_dim
            ) / np.sqrt(source_dim)
        return self._projection_matrix_cache[cache_key]

    def _apply_pca(self, embedding, target_dim):
        """使用随机投影降维，投影矩阵会被缓存复用"""
        source_dim = len(embedding)
        projection_matrix = self._get_projection_matrix(source_dim, target_dim)
        # 执行投影
        reduced = np.dot(embedding, projection_matrix)
        return reduced

    def _embedding(
        self, context: str, norm: bool = True, dim: int | None = None
    ) -> List[float]:
        """
        生成文本的向量嵌入

        参数:
            context: 要嵌入的文本
            norm: 是否对向量进行归一化
            dim: 目标维度（如果需要降维）

        返回:
            向量列表

        异常:
            RuntimeError: 多次重试后仍然失败
        """
        max_retries = 3
        retry_count = 0

        # 预处理：处理空文本和超长文本
        if not context or not context.strip():
            logger.warning("Empty context provided for embedding, using placeholder")
            context = "[EMPTY]"

        # 限制文本长度，避免超过模型限制
        max_text_length = getattr(self.args, "rag_emb_max_text_length", 8000)
        if len(context) > max_text_length:
            logger.debug(
                f"Text too long ({len(context)} chars), truncating to {max_text_length}"
            )
            context = context[:max_text_length]

        while retry_count < max_retries:
            try:
                result = self.llm.emb_query(context)

                # 验证结果
                if not result or len(result) == 0:
                    raise ValueError("Embedding API returned empty result")

                embedding = result[0].output

                # 验证 embedding 维度
                if not embedding or len(embedding) == 0:
                    raise ValueError("Embedding vector is empty")

                # 转换为 numpy 数组以便处理
                embedding = np.array(embedding)

                # 检查是否包含 NaN 或 Inf
                if np.any(np.isnan(embedding)) or np.any(np.isinf(embedding)):
                    raise ValueError("Embedding contains NaN or Inf values")

                if dim and dim < len(embedding):
                    embedding = self._apply_pca(embedding, target_dim=dim)

                if norm:
                    norm_value = np.linalg.norm(embedding)
                    if norm_value > 0:
                        embedding = embedding / norm_value
                    else:
                        logger.warning(
                            "Zero norm vector detected, skipping normalization"
                        )

                return embedding.tolist()

            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(
                        f"Failed to get embedding after {max_retries} "
                        f"attempts: {str(e)}"
                    )
                    raise RuntimeError(
                        f"Embedding generation failed after {max_retries} retries: {str(e)}"
                    ) from e

                # 指数退避重试
                sleep_time = min(1 * (2**retry_count), 10)  # 最多等待10秒
                logger.warning(
                    f"Embedding API call failed (attempt {retry_count}/"
                    f"{max_retries}). Error: {str(e)}. Retrying in "
                    f"{sleep_time:.1f} seconds..."
                )
                time.sleep(sleep_time)

        # 理论上不会到达这里，但为了类型安全
        raise RuntimeError("Unexpected error in embedding generation")

    def _initialize(self) -> None:
        if self.embed_dim is None:
            _query = f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    _id VARCHAR,
                    file_path VARCHAR,
                    content TEXT,
                    raw_content TEXT,
                    vector FLOAT[],
                    mtime FLOAT
                );
            """
        else:
            _query = f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    _id VARCHAR,
                    file_path VARCHAR,
                    content TEXT,
                    raw_content TEXT,
                    vector FLOAT[],
                    mtime FLOAT
                );
            """

        if self.database_name == ":memory:":
            self._conn.execute(_query)
        elif self.database_path is not None:
            with DuckDBLocalContext(self.database_path) as _conn:
                _conn.execute(_query)

    def truncate_table(self):
        _truncate_query = f"""TRUNCATE TABLE {self.table_name};"""
        if self.database_name == ":memory:":
            self._conn.execute(_truncate_query)
        elif self.database_path is not None:
            with DuckDBLocalContext(self.database_path) as _conn:
                _conn.execute(_truncate_query)

    def query_by_path(self, file_path: str):
        _exists_query = f"""SELECT _id FROM {self.table_name} WHERE file_path = ?"""
        query_params = [file_path]
        _final_results = []
        if self.database_name == ":memory:":
            _final_results = self._conn.execute(_exists_query, query_params).fetchall()
        elif self.database_path is not None:
            with DuckDBLocalContext(self.database_path) as _conn:
                _final_results = _conn.execute(_exists_query, query_params).fetchall()
        return _final_results

    def delete_by_ids(self, _ids: List[str]):
        _delete_query = f"""DELETE FROM {self.table_name} WHERE _id IN (?);"""
        query_params = [",".join(_ids)]
        if self.database_name == ":memory:":
            _final_results = self._conn.execute(_delete_query, query_params).fetchall()
        elif self.database_path is not None:
            with DuckDBLocalContext(self.database_path) as _conn:
                _final_results = _conn.execute(_delete_query, query_params).fetchall()
        return _final_results

    def _node_to_table_row(
        self, context_chunk: Dict[str, str | float], dim: int | None = None
    ) -> Any:
        """
        将文档块转换为数据库行格式

        参数:
            context_chunk: 文档块字典
            dim: 目标向量维度

        返回:
            数据库行元组
        """
        raw_content = context_chunk.get("raw_content", "")
        if not raw_content or not raw_content.strip():
            raw_content = "empty"

        # 限制文本大小
        max_size = getattr(self.args, "rag_emb_text_size", 8000)
        raw_content = raw_content[:max_size]

        try:
            embedding = self._embedding(raw_content, norm=True, dim=dim)
        except Exception as e:
            logger.error(
                f"Failed to generate embedding for chunk {context_chunk.get('_id', 'unknown')}: {str(e)}"
            )
            raise

        return (
            context_chunk.get("_id", ""),
            context_chunk.get("file_path", ""),
            context_chunk.get("content", ""),
            raw_content,
            embedding,
            context_chunk.get("mtime", 0.0),
        )

    def add_doc(self, context_chunk: Dict[str, str | float], dim: int | None = None):
        """
        添加文档到向量存储

        参数:
            context_chunk: 文档块字典，包含以下字段：
                - _id: 文档唯一标识
                - file_path: 文件路径
                - content: 文档内容
                - raw_content: 原始内容（用于生成向量）
                - mtime: 修改时间
            dim: 目标向量维度（可选，用于降维）
        """
        # 使用写入锁保护并发写入
        with self._write_lock:
            try:
                _row = self._node_to_table_row(context_chunk, dim=dim)

                if self.database_name == ":memory:":
                    _table = self._conn.table(self.table_name)
                    _table.insert(_row)
                elif self.database_path is not None:
                    with DuckDBLocalContext(self.database_path) as _conn:
                        _table = _conn.table(self.table_name)
                        _table.insert(_row)

            except Exception as e:
                logger.error(
                    f"Failed to add document {context_chunk.get('_id', 'unknown')}: {str(e)}"
                )
                raise

    def add_docs_batch(
        self, context_chunks: List[Dict[str, str | float]], dim: int | None = None
    ) -> Tuple[int, int]:
        """
        批量添加文档到向量存储，使用事务保证原子性

        参数:
            context_chunks: 文档块列表
            dim: 目标向量维度

        返回:
            (成功数, 失败数) 元组
        """
        success_count = 0
        failed_count = 0
        failed_ids = []

        with self._write_lock:
            if self.database_name == ":memory:":
                for chunk in context_chunks:
                    try:
                        _row = self._node_to_table_row(chunk, dim=dim)
                        _table = self._conn.table(self.table_name)
                        _table.insert(_row)
                        success_count += 1
                    except Exception as e:
                        failed_count += 1
                        failed_ids.append(chunk.get("_id", "unknown"))
                        logger.warning(f"Failed to insert chunk: {str(e)}")
            elif self.database_path is not None:
                with DuckDBLocalContext(self.database_path) as _conn:
                    try:
                        # 开启事务
                        _conn.execute("BEGIN TRANSACTION")

                        for chunk in context_chunks:
                            try:
                                _row = self._node_to_table_row(chunk, dim=dim)
                                _table = _conn.table(self.table_name)
                                _table.insert(_row)
                                success_count += 1
                            except Exception as e:
                                failed_count += 1
                                failed_ids.append(chunk.get("_id", "unknown"))
                                logger.warning(
                                    f"Failed to insert chunk {chunk.get('_id', 'unknown')}: {str(e)}"
                                )

                        # 提交事务
                        _conn.execute("COMMIT")

                    except Exception as e:
                        # 回滚事务
                        try:
                            _conn.execute("ROLLBACK")
                        except Exception:
                            pass
                        logger.error(
                            f"Batch insert failed, transaction rolled back: {str(e)}"
                        )
                        raise

        if failed_ids:
            logger.warning(
                f"Failed to insert {failed_count} chunks: {failed_ids[:10]}..."
            )

        return success_count, failed_count

    def vector_search(
        self,
        query: str,
        similarity_value: float = 0.7,
        similarity_top_k: int = 10,
        query_dim: int | None = None,
    ):
        """
        向量相似度搜索

        参数:
            query: 查询文本
            similarity_value: 相似度阈值 (0-1)
            similarity_top_k: 返回的最大结果数
            query_dim: 查询向量维度（降维用）

        返回:
            结果列表，每项为 (_id, file_path, mtime, score) 元组
        """
        # 参数验证
        similarity_value = max(0.0, min(1.0, similarity_value))
        similarity_top_k = max(1, similarity_top_k)

        try:
            query_embedding = self._embedding(query, norm=True, dim=query_dim)
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {str(e)}")
            return []

        _db_query = f"""
            SELECT _id, file_path, mtime, score
            FROM (
                SELECT *, list_cosine_similarity(vector, ?) AS score
                FROM {self.table_name}
            ) sq
            WHERE score IS NOT NULL
            AND score >= ?
            ORDER BY score DESC LIMIT ?;
        """
        query_params = [
            query_embedding,
            similarity_value,
            similarity_top_k,
        ]

        _final_results = []
        try:
            if self.database_name == ":memory:":
                _final_results = self._conn.execute(_db_query, query_params).fetchall()
            elif self.database_path is not None:
                with DuckDBLocalContext(self.database_path) as _conn:
                    _final_results = _conn.execute(_db_query, query_params).fetchall()
        except Exception as e:
            logger.error(f"Vector search query failed: {str(e)}")
            return []

        return _final_results


class LocalDuckDBStorageCache(BaseCacheManager):
    def __init__(
        self,
        path,
        ignore_spec,
        required_exts,
        extra_params: Optional[AutoCoderArgs] = None,
        emb_llm: Union[ByzerLLM, SimpleByzerLLM] = None,
        args: Optional[AutoCoderArgs] = None,
        llm: Optional[Union[ByzerLLM, SimpleByzerLLM, str]] = None,
    ):
        self.path = path
        self.ignore_spec = ignore_spec
        self.required_exts = required_exts
        self.extra_params = extra_params
        self.args = args
        self.llm = llm
        self.model_file = args.model_file if args else None
        self.product_mode = args.product_mode if args else "lite"

        self.storage = LocalDuckdbStorage(
            llm=emb_llm,
            database_name="byzerai_store_duckdb.db",
            table_name="rag_duckdb",
            persist_dir=self.path,
            args=args,
        )
        self.queue = []
        self.chunk_size = 1000
        self.max_output_tokens = extra_params.hybrid_index_max_output_tokens

        # 设置缓存文件路径
        self.cache_dir = os.path.join(self.path, ".cache")
        self.cache_file = os.path.join(self.cache_dir, "duckdb_storage_speedup.jsonl")
        self.cache: Dict[str, CacheItem] = {}
        # 创建缓存目录
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        # failed files support
        from .failed_files_utils import load_failed_files

        self.failed_files_path = os.path.join(self.cache_dir, "failed_files.json")
        self.failed_files = load_failed_files(self.failed_files_path)

        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.process_queue)
        self.thread.daemon = True
        self.thread.start()

        # 加载缓存
        self.cache = self._load_cache()

        # 检测 embedding 功能是否正常
        if emb_llm:
            try:
                logger.info("[INIT] Testing embedding functionality...")
                test_embedding = emb_llm.emb_query("ping")[0].output
                if not test_embedding or len(test_embedding) == 0:
                    raise ValueError(
                        "Embedding test failed: emb_query returned empty result"
                    )
                logger.info(
                    f"[INIT] Embedding test successful, vector dimension: {len(test_embedding)}"
                )
            except Exception as e:
                logger.error(f"[INIT] Embedding test failed: {str(e)}")
                raise RuntimeError(
                    f"Embedding functionality check failed: {str(e)}"
                ) from e

    @staticmethod
    def _chunk_text(text, max_length=1000):
        """Split text into chunks"""
        chunks = []
        current_chunk = []
        current_length = 0

        for line in text.split("\n"):
            if current_length + len(line) > max_length and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_length = 0
            current_chunk.append(line)
            current_length += len(line)

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    def _load_cache(self) -> Dict[str, CacheItem]:
        """Load cache from file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    cache = {}
                    for line in lines:
                        try:
                            data = json.loads(line.strip())
                            if isinstance(data, dict) and "file_path" in data:
                                # 转换为 CacheItem 对象
                                cache_item = CacheItem.model_validate(data)
                                cache[data["file_path"]] = cache_item
                        except json.JSONDecodeError:
                            continue
                    return cache
            except Exception as e:
                logger.warning(f"Error loading cache file: {str(e)}")
                logger.exception(e)
                return {}
        return {}

    def write_cache(self):
        cache_file = self.cache_file

        if not fcntl:
            try:
                with open(cache_file, "w", encoding="utf-8") as f:
                    for cache_item in self.cache.values():
                        # 确保序列化 Pydantic 模型
                        json.dump(cache_item.model_dump(), f, ensure_ascii=False)
                        f.write("\n")
            except IOError as e:
                logger.warning(f"Error writing cache file: {str(e)}")
                logger.exception(e)
        else:
            lock_file = cache_file + ".lock"
            with open(lock_file, "w", encoding="utf-8") as lockf:
                try:
                    # 获取文件锁
                    fcntl.flock(lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    # 写入缓存文件
                    with open(cache_file, "w", encoding="utf-8") as f:
                        for cache_item in self.cache.values():
                            # 确保序列化 Pydantic 模型
                            json.dump(cache_item.model_dump(), f, ensure_ascii=False)
                            f.write("\n")

                finally:
                    # 释放文件锁
                    fcntl.flock(lockf, fcntl.LOCK_UN)

    @staticmethod
    def fileinfo_to_tuple(file_info: FileInfo) -> Tuple[str, str, float, str]:
        return (
            file_info.file_path,
            file_info.relative_path,
            file_info.modify_time,
            file_info.file_md5,
        )

    def build_cache(self):
        """Build the cache by reading files and storing in DuckDBVectorStore"""
        logger.info(f"Building cache for path: {self.path}")

        files_to_process = []
        for file_info in self.get_all_files():
            if (
                file_info.file_path not in self.cache
                or self.cache[file_info.file_path].md5 != file_info.file_md5
            ):
                files_to_process.append(file_info)

        if not files_to_process:
            return

        from autocoder.rag.token_counter import initialize_tokenizer

        llm_name = get_llm_names(self.llm)[0] if self.llm else None
        product_mode = self.args.product_mode

        # 计算实际使用的进程数
        workers = self.args.rag_cache_build_workers if self.args else 0
        if workers == 0:
            workers = max(1, os.cpu_count() // 2)
        # 进程数不超过待处理文件数，避免创建过多空闲进程
        num_processes = min(workers, len(files_to_process))

        with Pool(
            processes=num_processes,
            initializer=initialize_tokenizer,
            initargs=(VariableHolder.TOKENIZER_PATH,),
        ) as pool:
            target_files_to_process = []
            for file_info in files_to_process:
                target_files_to_process.append(self.fileinfo_to_tuple(file_info))
            worker_func = functools.partial(
                process_file_in_multi_process,
                llm=llm_name,
                product_mode=product_mode,
                model_file=self.model_file,
            )
            results = pool.map(worker_func, target_files_to_process)

        items = []
        for file_info, result in zip(files_to_process, results):
            content: List[SourceCode] = result
            self.cache[file_info.file_path] = CacheItem(
                file_path=file_info.file_path,
                relative_path=file_info.relative_path,
                content=[c.model_dump() for c in content],
                modify_time=file_info.modify_time,
                md5=file_info.file_md5,
            )

            for doc in content:
                logger.info(f"Processing file: {doc.module_name}")
                chunks = self._chunk_text(doc.source_code, self.chunk_size)
                for chunk_idx, chunk in enumerate(chunks):
                    chunk_item = {
                        "_id": f"{doc.module_name}_{chunk_idx}",
                        "file_path": file_info.file_path,
                        "content": chunk,
                        "raw_content": chunk,
                        "vector": "",
                        "mtime": file_info.modify_time,
                    }
                    items.append(chunk_item)

        # Save to local cache
        logger.info("Saving cache to local file")
        self.write_cache()

        if items:
            logger.info("[BUILD CACHE] Clearing DuckDB Storage cache")
            self.storage.truncate_table()
            logger.info(f"[BUILD CACHE] Preparing to write to DuckDB Storage.")
            logger.info(
                f"[BUILD CACHE] Total chunks: {len(items)}, "
                f"Total files: {len(files_to_process)}"
            )

            # Use a fixed optimal batch size instead of dividing by worker count
            batch_size = 100  # Optimal batch size for Byzer Storage
            item_batches = [
                items[i : i + batch_size] for i in range(0, len(items), batch_size)
            ]

            total_batches = len(item_batches)
            completed_batches = 0

            logger.info(f"[BUILD CACHE] Writing to DuckDB Storage.")
            logger.info(
                f"[BUILD CACHE] Batch size: {batch_size}, "
                f"Total batches: {total_batches}"
            )
            start_time = time.time()

            # Use more workers to process the smaller batches efficiently
            max_workers = min(
                self.extra_params.rag_index_build_workers, total_batches
            )  # Cap at 10 workers or total batch count
            logger.info(
                f"[BUILD CACHE] Using {max_workers} parallel workers for processing"
            )

            def batch_add_doc(_batch):
                """使用批量插入方法处理一批文档"""
                success, failed = self.storage.add_docs_batch(
                    _batch, dim=self.extra_params.rag_duckdb_vector_dim
                )
                return success, failed

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                # Submit all batches to the executor upfront (non-blocking)
                for batch in item_batches:
                    futures.append(executor.submit(batch_add_doc, batch))

                # Wait for futures to complete
                total_success = 0
                total_failed = 0
                for future in as_completed(futures):
                    try:
                        success, failed = future.result()
                        total_success += success
                        total_failed += failed
                        completed_batches += 1
                        elapsed = time.time() - start_time
                        estimated_total = (
                            elapsed / completed_batches * total_batches
                            if completed_batches > 0
                            else 0
                        )
                        remaining = estimated_total - elapsed

                        # Only log progress at reasonable intervals to reduce log spam
                        if (
                            (completed_batches == 1)
                            or (completed_batches == total_batches)
                            or (completed_batches % max(1, total_batches // 10) == 0)
                        ):
                            progress_percent = (
                                completed_batches / total_batches * 100
                                if total_batches > 0
                                else 0
                            )
                            logger.info(
                                f"[BUILD CACHE] Progress: {completed_batches}/"
                                f"{total_batches} ({progress_percent:.1f}%). "
                                f"Success: {total_success}, Failed: {total_failed}. "
                                f"ETA: {remaining:.1f}s"
                            )
                    except Exception as e:
                        completed_batches += 1
                        logger.error(f"[BUILD CACHE] Error saving batch: {str(e)}")
                        logger.exception(e)

            total_time = time.time() - start_time
            logger.info(
                f"[BUILD CACHE] Completed! Total time: {total_time:.2f}s, "
                f"Success: {total_success}, Failed: {total_failed}, "
                f"Success rate: {total_success / max(1, total_success + total_failed) * 100:.1f}%"
            )

    def update_storage(self, file_info: FileInfo, is_delete: bool):
        results = self.storage.query_by_path(file_info.file_path)
        if results:  # [('_id',)]
            for result in results:
                self.storage.delete_by_ids([result[0]])

        items = []
        if not is_delete:
            content = [
                SourceCode.model_validate(doc)
                for doc in self.cache[file_info.file_path].content
            ]
            modify_time = self.cache[file_info.file_path].modify_time
            for doc in content:
                logger.info(f"正在处理更新文件: {doc.module_name}")
                chunks = self._chunk_text(doc.source_code, self.chunk_size)
                for chunk_idx, chunk in enumerate(chunks):
                    chunk_item = {
                        "_id": f"{doc.module_name}_{chunk_idx}",
                        "file_path": file_info.file_path,
                        "content": chunk,
                        "raw_content": chunk,
                        "vector": chunk,
                        "mtime": modify_time,
                    }
                    items.append(chunk_item)
        if items:
            for _chunk in items:
                try:
                    self.storage.add_doc(
                        _chunk, dim=self.extra_params.rag_duckdb_vector_dim
                    )
                    time.sleep(self.extra_params.anti_quota_limit)
                    logger.info(f"Saved chunk {_chunk['_id']} to DuckDB Storage ")
                except Exception as err:
                    logger.error(f"Error in saving chunk: {str(err)}")
                    logger.exception(err)

    def process_queue(self):
        while self.queue:
            file_list = self.queue.pop(0)
            if isinstance(file_list, DeleteEvent):
                for item in file_list.file_paths:
                    logger.info(f"{item} is detected to be removed")
                    del self.cache[item]
                    # remove from failed files if present
                    if item in self.failed_files:
                        self.failed_files.remove(item)
                        save_failed_files(self.failed_files_path, self.failed_files)
                    # 创建一个临时的 FileInfo 对象
                    file_info = FileInfo(
                        file_path=item, relative_path="", modify_time=0, file_md5=""
                    )
                    self.update_storage(file_info, is_delete=True)

            elif isinstance(file_list, AddOrUpdateEvent):
                for file_info in file_list.file_infos:
                    logger.info(f"{file_info.file_path} is detected to be updated")
                    try:
                        content = process_file_local(
                            file_info.file_path,
                            llm=self.llm,
                            product_mode=self.product_mode,
                            model_file=self.model_file,
                        )
                        if content:
                            self.cache[file_info.file_path] = CacheItem(
                                file_path=file_info.file_path,
                                relative_path=file_info.relative_path,
                                content=[c.model_dump() for c in content],
                                modify_time=file_info.modify_time,
                                md5=file_info.file_md5,
                            )
                            self.update_storage(file_info, is_delete=False)
                            # remove from failed files if present
                            if file_info.file_path in self.failed_files:
                                self.failed_files.remove(file_info.file_path)
                                save_failed_files(
                                    self.failed_files_path, self.failed_files
                                )
                        else:
                            logger.warning(
                                f"Empty result for file: {file_info.file_path}, treat as parse failed, skipping cache update"
                            )
                            self.failed_files.add(file_info.file_path)
                            save_failed_files(self.failed_files_path, self.failed_files)
                    except Exception as e:
                        logger.error(f"Error in process_queue: {str(e)}")
                        logger.exception(e)
                        self.failed_files.add(file_info.file_path)
                        save_failed_files(self.failed_files_path, self.failed_files)

            self.write_cache()

    def trigger_update(self):
        logger.info("检查文件是否有更新.....")
        files_to_process = []
        current_files = set()
        for file_info in self.get_all_files():
            current_files.add(file_info.file_path)
            # skip failed files
            if file_info.file_path in self.failed_files:
                logger.info(f"文件 {file_info.file_path} 之前解析失败，跳过此次更新")
                continue
            if (
                file_info.file_path not in self.cache
                or self.cache[file_info.file_path].md5 != file_info.file_md5
            ):
                files_to_process.append(file_info)

        deleted_files = set(self.cache.keys()) - current_files
        logger.info(f"待处理的文件: {len(files_to_process)}个")
        logger.info(f"已删除的文件: {len(deleted_files)}个")
        if deleted_files:
            with self.lock:
                self.queue.append(DeleteEvent(file_paths=deleted_files))
        if files_to_process:
            with self.lock:
                self.queue.append(AddOrUpdateEvent(file_infos=files_to_process))

    def get_all_files(self) -> List[FileInfo]:
        all_files = []
        for root, dirs, files in os.walk(self.path, followlinks=True):
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".") and d not in default_ignore_dirs
            ]

            if self.ignore_spec:
                relative_root = os.path.relpath(root, self.path)
                dirs[:] = [
                    d
                    for d in dirs
                    if not self.ignore_spec.match_file(os.path.join(relative_root, d))
                ]
                files = [
                    f
                    for f in files
                    if not self.ignore_spec.match_file(os.path.join(relative_root, f))
                ]

            for file in files:
                if self.required_exts and not any(
                    file.endswith(ext) for ext in self.required_exts
                ):
                    continue

                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, self.path)
                modify_time = os.path.getmtime(file_path)
                file_md5 = generate_file_md5(file_path)
                all_files.append(
                    FileInfo(
                        file_path=file_path,
                        relative_path=relative_path,
                        modify_time=modify_time,
                        file_md5=file_md5,
                    )
                )

        return all_files

    def _get_single_cache(
        self, query: str, options: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        使用单个查询检索缓存文档

        参数:
            query: 查询字符串
            options: 包含查询选项的字典

        返回:
            包含文档信息的字典列表，每个字典包含_id、file_path、mtime和score字段
        """
        logger.info(f"正在使用向量搜索检索数据, 你的问题: {query}")
        results = []

        # Add vector search if enabled
        if options.get("enable_vector_search", True):
            # 返回值包含  [(_id, file_path, mtime, score,),]
            search_results = self.storage.vector_search(
                query,
                similarity_value=self.extra_params.rag_duckdb_query_similarity,
                similarity_top_k=self.extra_params.rag_duckdb_query_top_k,
                query_dim=self.extra_params.rag_duckdb_vector_dim,
            )

            # Convert tuples to dictionaries for the merger
            for _id, file_path, mtime, score in search_results:
                results.append(
                    {"_id": _id, "file_path": file_path, "mtime": mtime, "score": score}
                )

        logger.info(f"查询 '{query}' 返回 {len(results)} 条记录")
        return results

    def _process_search_results(self, results: List[Dict[str, Any]]) -> Dict[str, Dict]:
        """
        处理搜索结果，提取文件路径并构建结果字典

        参数:
            results: 搜索结果列表，每项包含文档信息的字典

        返回:
            匹配文档的字典，键为文件路径，值为文件内容

        说明:
            该方法会根据查询结果从缓存中提取文件内容，并记录累计token数，
            当累计token数超过max_output_tokens时，将停止处理并返回已处理的结果。
        """
        # 记录被处理的总tokens数
        total_tokens = 0

        # Group results by file_path and reconstruct documents while preserving order
        # 这里还可以有排序优化，综合考虑一篇内容出现的次数以及排序位置
        file_paths = []
        seen = set()
        for result in results:
            file_path = result["file_path"]
            if file_path not in seen:
                seen.add(file_path)
                file_paths.append(file_path)

        # 从缓存中获取文件内容
        result = {}
        for file_path in file_paths:
            if file_path in self.cache:
                cached_data = self.cache[file_path]
                for doc in cached_data.content:
                    if total_tokens + doc["tokens"] > self.max_output_tokens:
                        logger.info(
                            f"当前检索已超出用户设置 Hybrid Index Max Tokens:"
                            f"{self.max_output_tokens}，累计tokens: {total_tokens}, "
                            f"经过向量搜索共检索出 {len(result.keys())} 个文档, "
                            f"共 {len(self.cache.keys())} 个文档"
                        )
                        return result
                    total_tokens += doc["tokens"]
                result[file_path] = cached_data.model_dump()
        logger.info(
            f"用户Hybrid Index Max Tokens设置为:{self.max_output_tokens}，"
            f"累计tokens: {total_tokens}, 经过向量搜索共检索出 "
            f"{len(result.keys())} 个文档, 共 {len(self.cache.keys())} 个文档"
        )
        return result

    def get_cache(self, options: Optional[Dict[str, Any]] = None) -> Dict[str, Dict]:
        """
        获取缓存中的文档信息

        参数:
            options: 包含查询参数的字典，可以包含以下键：
                - queries: 查询列表，可以是单个查询或多个查询
                - enable_vector_search: 是否启用向量搜索，默认为True
                - merge_strategy: 多查询时的合并策略，默认为WEIGHTED_RANK
                - max_results: 最大结果数，默认为None表示不限制

        返回:
            匹配文档的字典，键为文件路径，值为文件内容
        """
        self.trigger_update()  # 检查更新

        # Run-once 模式：同步完成增量更新（包括 DuckDB 向量索引）后再查询
        if self.extra_params and self.extra_params.rag_run_once:
            logger.info(
                "[Run-once mode] Processing incremental updates synchronously for DuckDB storage..."
            )
            start_time = time.time()

            # 同步处理队列，确保增量更新已刷入 DuckDB
            max_iterations = 10
            iteration = 0
            while iteration < max_iterations:
                queue_len_before = len(self.queue)
                if queue_len_before == 0:
                    break

                logger.info(
                    f"[Run-once mode] Processing queue (iteration {iteration + 1}, queue size: {queue_len_before})..."
                )
                self.process_queue()

                queue_len_after = len(self.queue)
                if queue_len_after == 0:
                    elapsed = time.time() - start_time
                    logger.info(
                        f"[Run-once mode] Queue processed successfully in {elapsed:.2f}s, cache has {len(self.cache)} documents"
                    )
                    break
                elif queue_len_after >= queue_len_before:
                    logger.warning(
                        f"[Run-once mode] Queue size not decreasing (before: {queue_len_before}, after: {queue_len_after}), stopping"
                    )
                    break

                iteration += 1

            if iteration >= max_iterations:
                logger.warning(
                    f"[Run-once mode] Reached max iterations ({max_iterations}), some updates may be pending"
                )

        if options is None or "queries" not in options:
            return {
                file_path: self.cache[file_path].model_dump()
                for file_path in self.cache
            }

        queries = options.get("queries", [])

        # 如果没有查询或只有一个查询，使用原来的方法
        if not queries:
            return {
                file_path: self.cache[file_path].model_dump()
                for file_path in self.cache
            }
        elif len(queries) == 1:
            results = self._get_single_cache(queries[0], options)
            return self._process_search_results(results)

        # 导入合并策略
        from autocoder.rag.cache.cache_result_merge import (
            CacheResultMerger,
            MergeStrategy,
        )

        # 获取合并策略
        merge_strategy_name = options.get(
            "merge_strategy", MergeStrategy.WEIGHTED_RANK.value
        )
        try:
            merge_strategy = MergeStrategy(merge_strategy_name)
        except ValueError:
            logger.warning(
                f"未知的合并策略: {merge_strategy_name}, 使用默认策略 WEIGHTED_RANK"
            )
            merge_strategy = MergeStrategy.WEIGHTED_RANK

        # 限制最大结果数
        max_results = options.get("max_results", None)
        merger = CacheResultMerger(max_results=max_results)

        # 并发处理多个查询
        logger.info(
            f"处理多查询请求，查询数量: {len(queries)}, 合并策略: {merge_strategy}"
        )
        query_results = []
        with ThreadPoolExecutor(max_workers=min(len(queries), 10)) as executor:
            future_to_query = {
                executor.submit(self._get_single_cache, query, options): query
                for query in queries
            }
            for future in as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    query_result = future.result()
                    logger.info(f"查询 '{query}' 返回 {len(query_result)} 条记录")
                    query_results.append((query, query_result))
                except Exception as e:
                    logger.error(f"处理查询 '{query}' 时出错: {str(e)}")
                    logger.exception(e)

        logger.info(f"所有查询共返回 {sum(len(r) for _, r in query_results)} 条记录")

        # 使用策略合并结果
        merged_results = merger.merge(query_results, strategy=merge_strategy)
        logger.info(f"合并后的结果共 {len(merged_results)} 条记录")

        # 处理合并后的结果
        return self._process_search_results(merged_results)

    def close(self):
        """
        关闭缓存管理器，释放所有资源

        清理步骤:
            1. 设置停止事件，通知后台线程退出
            2. 等待后台线程结束（最多等待 5 秒）
            3. 关闭 DuckDB 存储连接
        """
        logger.info("[CLOSE] Closing LocalDuckDBStorageCache...")

        # 停止后台线程
        self.stop_event.set()
        if self.thread.is_alive():
            self.thread.join(timeout=5)
            if self.thread.is_alive():
                logger.warning("[CLOSE] Background thread did not stop in time")

        # 关闭存储
        if hasattr(self.storage, "_conn") and self.storage._conn is not None:
            try:
                self.storage._conn.close()
            except Exception as e:
                logger.warning(f"[CLOSE] Error closing DuckDB connection: {str(e)}")

        logger.info("[CLOSE] LocalDuckDBStorageCache closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
