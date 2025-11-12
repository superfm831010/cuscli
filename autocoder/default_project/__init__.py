from autocoder.common import SourceCode, AutoCoderArgs
from autocoder import common as FileUtils
from autocoder.utils.rest import HttpDoc
import os
from typing import Optional, Generator, List, Dict, Any, Callable
from git import Repo
import byzerllm
from autocoder.common.search import Search, SearchEngine
from loguru import logger
import re
from pydantic import BaseModel, Field
from rich.console import Console
import json
from autocoder.common import files as FileUtils
from autocoder.common.ignorefiles import should_ignore


class DefaultProject:
    """
    DefaultProject类用于遍历项目目录并收集文件，使用ignorefiles模块进行文件过滤。
    与SuffixProject不同，它不按文件后缀过滤，而是收集所有不被忽略的文件。
    """

    def __init__(
        self,
        args: AutoCoderArgs,
        llm: Optional[byzerllm.ByzerLLM] = None,
        file_filter=None,
    ):
        self.args = args
        self.directory = args.source_dir
        self.git_url = args.git_url
        self.target_file = args.target_file
        self.file_filter = file_filter
        self.sources = []
        self.llm = llm
        # DefaultProject不需要exclude_files和exclude_patterns，因为使用ignorefiles模块处理

    def output(self):
        with open(self.target_file, "r", encoding="utf-8") as file:
            return file.read()

    def is_text_file(self, file_path):
        """判断是否为文本文件"""
        try:
            # 检查常见的文本文件后缀
            text_extensions = {
                ".txt",
                ".md",
                ".py",
                ".js",
                ".ts",
                ".jsx",
                ".tsx",
                ".html",
                ".htm",
                ".css",
                ".scss",
                ".sass",
                ".less",
                ".json",
                ".xml",
                ".yaml",
                ".yml",
                ".toml",
                ".ini",
                ".cfg",
                ".conf",
                ".log",
                ".sql",
                ".sh",
                ".bash",
                ".zsh",
                ".fish",
                ".ps1",
                ".bat",
                ".cmd",
                ".dockerfile",
                ".gitignore",
                ".gitattributes",
                ".editorconfig",
                ".eslintrc",
                ".prettierrc",
                ".babelrc",
                ".env",
                ".properties",
                ".lock",
                ".sum",
                ".mod",
                ".go",
                ".rs",
                ".php",
                ".rb",
                ".pl",
                ".r",
                ".swift",
                ".kt",
                ".java",
                ".c",
                ".cpp",
                ".cc",
                ".cxx",
                ".h",
                ".hpp",
                ".cs",
                ".vb",
                ".fs",
                ".clj",
                ".scala",
                ".groovy",
                ".dart",
                ".elm",
                ".haskell",
                ".hs",
                ".ml",
                ".ocaml",
                ".ex",
                ".exs",
                ".erl",
                ".lua",
                ".vim",
                ".emacs",
                ".lisp",
                ".scheme",
                ".racket",
                ".clojure",
                ".f90",
                ".f95",
                ".f03",
                ".f08",
                ".for",
                ".ftn",
                ".m",
                ".mm",
                ".s",
                ".asm",
                ".nasm",
                ".masm",
                ".pas",
                ".pp",
                ".inc",
                ".dpr",
                ".dfm",
                ".lfm",
                ".lpr",
                ".lpk",
                ".tex",
                ".bib",
                ".sty",
                ".cls",
                ".dtx",
                ".ins",
                ".aux",
                ".toc",
                ".lof",
                ".lot",
                ".idx",
                ".ind",
                ".gls",
                ".glo",
                ".acn",
                ".acr",
                ".alg",
                ".bbl",
                ".blg",
                ".fdb_latexmk",
                ".fls",
                ".figlist",
                ".makefile",
                ".cmake",
                ".mk",
                ".am",
                ".in",
                ".ac",
                ".m4",
                ".autotools",
                ".spec",
                ".ebuild",
                ".pkgbuild",
                ".install",
                ".desktop",
                ".service",
                ".socket",
                ".timer",
                ".mount",
                ".automount",
                ".swap",
                ".target",
                ".path",
                ".slice",
                ".scope",
                ".busname",
                ".device",
                ".network",
                ".netdev",
                ".link",
                ".nspawn",
                ".container",
                ".zone",
                ".policy",
                ".rules",
                ".preset",
                ".wants",
                ".requires",
                ".requisite",
                ".conflicts",
                ".before",
                ".after",
                ".onboot",
                ".onfailure",
                ".onabort",
                ".onerror",
                ".onsuccess",
                ".onfinal",
                ".onrestart",
                ".onstop",
                ".onstart",
                ".onreload",
                ".template",
                ".d",
                ".conf.d",
                ".service.d",
                ".socket.d",
                ".timer.d",
                ".mount.d",
                ".automount.d",
                ".swap.d",
                ".target.d",
                ".path.d",
                ".slice.d",
                ".scope.d",
                ".busname.d",
                ".device.d",
                ".network.d",
                ".netdev.d",
                ".link.d",
                ".nspawn.d",
                ".container.d",
                ".zone.d",
                ".policy.d",
                ".rules.d",
                ".preset.d",
                ".wants.d",
                ".requires.d",
                ".requisite.d",
                ".conflicts.d",
                ".before.d",
                ".after.d",
                ".onboot.d",
                ".onfailure.d",
                ".onabort.d",
                ".onerror.d",
                ".onsuccess.d",
                ".onfinal.d",
                ".onrestart.d",
                ".onstop.d",
                ".onstart.d",
                ".onreload.d",
            }

            _, ext = os.path.splitext(file_path.lower())
            if ext in text_extensions:
                return True

            # 检查没有后缀名的常见文件
            filename = os.path.basename(file_path).lower()
            text_files_no_ext = {
                "readme",
                "license",
                "changelog",
                "authors",
                "contributors",
                "copying",
                "install",
                "news",
                "todo",
                "version",
                "manifest",
                "makefile",
                "dockerfile",
                "vagrantfile",
                "gemfile",
                "rakefile",
                "procfile",
                "pipfile",
                "poetry.lock",
                "requirements",
                "setup.cfg",
                "tox.ini",
                "pytest.ini",
                "mypy.ini",
                "flake8",
                "pylintrc",
                ".gitignore",
                ".gitattributes",
                ".dockerignore",
                ".eslintignore",
                ".prettierignore",
                ".stylelintignore",
                ".editorconfig",
            }

            if filename in text_files_no_ext:
                return True

            # 尝试读取文件前几个字节来判断是否为文本
            try:
                with open(file_path, "rb") as f:
                    chunk = f.read(1024)  # 读取前1024字节
                    if b"\x00" in chunk:  # 包含null字节，可能是二进制文件
                        return False
                    # 尝试解码为UTF-8
                    chunk.decode("utf-8")
                    return True
            except (UnicodeDecodeError, IOError, PermissionError):
                return False

        except Exception as e:
            logger.debug(f"判断文件类型时出错 {file_path}: {e}")
            return False

    def read_file_content(self, file_path):
        return FileUtils.read_file(file_path)

    def convert_to_source_code(self, file_path):
        module_name = file_path
        try:
            source_code = self.read_file_content(file_path)
        except Exception as e:
            logger.warning(f"Failed to read file: {file_path}. Error: {str(e)}")
            return None
        return SourceCode(module_name=module_name, source_code=source_code)

    def get_source_codes(self) -> Generator[SourceCode, None, None]:
        """遍历目录收集源代码文件，使用ignorefiles模块进行过滤"""
        for root, dirs, files in os.walk(self.directory, followlinks=True):
            # 过滤目录，移除应该被忽略的目录
            dirs[:] = [
                d
                for d in dirs
                if not should_ignore(os.path.join(root, d), self.directory)
            ]

            for file in files:
                file_path = os.path.join(root, file)

                # 跳过 .autocoderignore 文件本身
                if file == ".autocoderignore":
                    continue

                # 使用ignorefiles模块检查是否应该忽略此文件
                if should_ignore(file_path, self.directory):                    
                    continue

                # 检查是否为文本文件
                if not self.is_text_file(file_path):                    
                    continue

                # 应用自定义文件过滤器（如果有）
                if self.file_filter is None or self.file_filter(file_path, []):
                    source_code = self.convert_to_source_code(file_path)
                    if source_code is not None:
                        yield source_code

    def get_rest_source_codes(self) -> Generator[SourceCode, None, None]:
        if self.args.urls:
            urls = self.args.urls
            if isinstance(self.args.urls, str):
                urls = self.args.urls.split(",")
            http_doc = HttpDoc(args=self.args, llm=self.llm, urls=urls)
            sources = http_doc.crawl_urls()
            for source in sources:
                source.tag = "REST"
            return sources
        return []

    def get_rag_source_codes(self):
        if not self.args.enable_rag_search and not self.args.enable_rag_context:
            return []

        console = Console()
        console.print(
            f"\n[bold blue]Starting RAG search for:[/bold blue] {self.args.query}"
        )

        from autocoder.rag.rag_entry import RAGFactory

        rag = RAGFactory.get_rag(self.llm, self.args, "")
        docs = rag.search(self.args.query)
        for doc in docs:
            doc.tag = "RAG"

        console = Console()
        console.print(f"[bold green]Found {len(docs)} relevant documents[/bold green]")

        return docs

    def get_search_source_codes(self):
        temp = self.get_rag_source_codes()
        if self.args.search_engine and self.args.search_engine_token:
            if self.args.search_engine == "bing":
                search_engine = SearchEngine.BING
            else:
                search_engine = SearchEngine.GOOGLE

            searcher = Search(
                args=self.args,
                llm=self.llm,
                search_engine=search_engine,
                subscription_key=self.args.search_engine_token,
            )
            search_query = self.args.search or self.args.query
            search_context = searcher.answer_with_the_most_related_context(search_query)
            return temp + [
                SourceCode(
                    module_name="SEARCH_ENGINE",
                    source_code=search_context,
                    tag="SEARCH",
                )
            ]
        return temp + []

    @byzerllm.prompt()
    def get_simple_directory_structure(self) -> str:
        """
        当前项目目录结构：
        1. 项目根目录： {{ directory }}
        2. 项目子目录/文件列表：
        {{ structure }}
        """
        structure = []
        for source_code in self.get_source_codes():
            relative_path = os.path.relpath(source_code.module_name, self.directory)
            structure.append(relative_path)

        subs = "\n".join(sorted(structure))
        return {"directory": self.directory, "structure": subs}

    @byzerllm.prompt()
    def get_tree_like_directory_structure(self) -> str:
        """
        当前项目目录结构：
        1. 项目根目录： {{ directory }}
        2. 项目子目录/文件列表(类似tree 命令输出)：
        {{ structure }}
        """
        structure_dict = {}
        for source_code in self.get_source_codes():
            relative_path = os.path.relpath(source_code.module_name, self.directory)
            parts = relative_path.split(os.sep)
            current_level = structure_dict
            for part in parts:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]

        def generate_tree(d, indent=""):
            tree = []
            for k, v in d.items():
                if v:
                    tree.append(f"{indent}{k}/")
                    tree.extend(generate_tree(v, indent + "    "))
                else:
                    tree.append(f"{indent}{k}")
            return tree

        return {
            "structure": "\n".join(generate_tree(structure_dict)),
            "directory": self.directory,
        }

    def run(self):
        if self.git_url is not None:
            self.clone_repository()

        # 先收集所有sources
        for code in self.get_source_codes():
            self.sources.append(code)

        for code in self.get_rest_source_codes():
            self.sources.append(code)

        for code in self.get_search_source_codes():
            self.sources.append(code)

        # 如果target_file存在，才写入文件
        if self.target_file:
            with open(self.target_file, "w", encoding="utf-8") as file:
                for code in self.sources:
                    file.write(f"##File: {code.module_name}\n")
                    file.write(f"{code.source_code}\n\n")

    def clone_repository(self):
        if self.git_url is None:
            raise ValueError("git_url is required to clone the repository")

        if os.path.exists(self.directory):
            print(f"Directory {self.directory} already exists. Skipping cloning.")
        else:
            print(f"Cloning repository {self.git_url} into {self.directory}")
            Repo.clone_from(self.git_url, self.directory)
