import byzerllm
from pathlib import Path
from typing import Dict
import os
from loguru import logger

@byzerllm.prompt()
def init_command_template(source_dir:str):
    '''
    ## More details about the configuration file can be found in: https://github.com/allwefantasy/auto-coder/tree/master/docs/en
    ## 关于配置文件的更多细节可以在这里找到: https://gitcode.com/allwefantasy11/auto-coder/tree/master/docs/zh
    
    ## Location of your project
    ## 你项目的路径
    source_dir: {{ source_dir }}

    ## The target file to store the prompt/generated code or other information
    target_file: {{ source_dir }}/output.txt
    
    ## The urls of some documents which can help the model to understand your current work
    ## 一些文档的URL，可以帮助模型了解你当前的工作
    ## Multiple documents can be separated by comma
    ## 多个文档可以用逗号分隔
    # urls: <SOME DOCUMENTATION URLs>

    ## The type of your project. py,ts or you can use the suffix e.g. .java .scala .go 
    ## If you use the suffix, you can combind multiple types with comma e.g. .java,.scala
    ## 你项目的类型，py,ts或者你可以使用后缀，例如.java .scala .go
    ## 如果你使用后缀，你可以使用逗号来组合多个类型，例如.java,.scala
    project_type: py

    ## The model you want to drive AutoCoder to run
    model: v3_chat
    chat_model: r1_chat
    generate_rerank_model: r1_chat
    code_model: v3_chat
    index_filter_model: r1_chat


    ## Enable the index building which can help you find the related files by your query
    ## 启用索引构建，可以帮助您通过查询找到相关文件
    skip_build_index: false
    ## The model to build index for the project (Optional)
    ## 用于为项目构建索引的模型（可选）
    index_model: v3_chat

    ## the filter level to find the related files
    ## 0: only find the files with the file name
    ## 1: find the files with the file name and the symbols in the file
    ## 2. find the related files reffered by the files in 0 and 1
    ## 0 is recommended for the first time
    ## 用于查找相关文件的过滤级别
    ## 0: 仅查找文件名
    ## 1: 查找文件名和文件中的符号
    ## 2. 查找0和1中的文件引用的相关文件
    ## 第一次建议使用0
    index_filter_level: 0
    index_model_max_input_length: 30000

    ## The number of workers to filter the files
    ## 过滤文件的线程数量
    ## If you have a large project, you can increase this number
    ## 如果您有一个大项目，可以增加这个数字
    ## Make sure you you have the proper workers when you use `byzerllm` to deploy model.
    ## 当您使用 `byzerllm` 部署模型时，请确保你也配置了合适的 num_workers 参数。
    index_filter_workers: 1
    
    ## The number of workers to build the index
    ## 构建索引的线程数量
    ## If you have a large project, you can increase this number
    ## 如果您有一个大项目，可以增加这个数字
    ## Make sure you you have the proper workers when you use `byzerllm` to deploy model.
    ## 当您使用 `byzerllm` 部署模型时，请确保你也配置了合适的 num_workers 参数。
    index_build_workers: 1    

    ## enable RAG context
    ## 启用RAG上下文
    enable_rag_context: false
    ## or you can give a query directly and enable the RAG at the same time
    ## 或者您可以直接给出一个查询，并同时启用RAG
    # enable_rag_context_query: YOUR QUERY TO GET SOME CONTEXT BY RAG

    ## enable Search Engine
    ## 启用搜索引擎
    ## google/bing
    # search_engine: bing
    ## Get the search engine token in the environment variable
    ## 在环境变量中获取搜索引擎令牌
    ## Ask for Bing Search API Token. You can visit https://www.microsoft.com/en-us/bing/apis/bing-web-search-api to get the token.
    ## 申请 Bing 搜索API Token。你可以访问 https://www.microsoft.com/en-us/bing/apis/bing-web-search-api 获取 token。
    # search_engine_token: ENV {{BING_SEARCH_TOKEN}} 
    
    
    ##  The model to build index for the project
    ## 用于为项目构建索引的模型
    # emb_model: gpt_emb

    ## The model will generate the code for you
    ## 模型将为您生成代码
    execute: true
    
    ## AutoCoder will merge the generated code into your project
    ## AutoCoder将合并生成的代码到您的项目中
    auto_merge: true

    ## AutoCoder will ask you to deliver the content to the Web Model,
    ## then paste the answer back to the terminal
    ## AutoCoder将要求您将内容传递给Web模型，然后将答案粘贴回终端
    human_as_model: true

    ## What you want the model to do
    ## 你想让模型做什么
    query: |  
      YOUR QUERY HERE   
  
    
    ## You can execute this file with the following command
    ## And check the output in the target file
    ## 您可以使用以下命令执行此文件
    ## 并在目标文件中检查输出
    ## auto-coder --file 101_current_work.yml
    '''

def create_actions(source_dir:str,params:Dict[str,str]):    
    mapping =  {        
        "base": base_base.prompt(**params),
        "enable_index": base_enable_index.prompt(),
        "enable_search_engine": base_enable_search_engine.prompt(),
        "enable_rag_search": base_enable_rag_search.prompt(),
        "exclude_files": base_exclude_files.prompt(),
        "enable_diff": base_enable_diff.prompt(),
        "enable_wholefile": base_enable_wholefile.prompt(),
        "000_example": base_000_example.prompt(),
    }
    init_file_path = os.path.join(source_dir, "actions", "101_current_work.yml")
    with open(init_file_path, "w", encoding="utf-8") as f:
        f.write(init_command_template.prompt(source_dir=source_dir))

    for k,v in mapping.items():
        base_dir = os.path.join(source_dir, "actions","base")
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
                     
        file_path = os.path.join(source_dir, "actions","base", f"{k}.yml")
        
        if k == "000_example":
            file_path = os.path.join(source_dir, "actions", f"{k}.yml")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(v)    

@byzerllm.prompt()
def base_000_example()->str:
    '''
    include_file:
      - ./base/base.yml
      - ./base/enable_index.yml
      - ./base/enable_wholefile.yml    

    query: |
      YOUR QUERY HERE
    '''

@byzerllm.prompt()
def base_base(source_dir:str,project_type:str)->str:    
    '''
    project_type: "{{ project_type }}"
    source_dir: {{ source_dir }}
    target_file: {{ target_file }}

    model: v3_chat    
    model_max_input_length: 60000    
    index_filter_workers: 100
    index_build_workers: 100
    index_filter_level: 1

    execute: true
    auto_merge: true
    human_as_model: true
    '''
    return {
        "target_file": Path(source_dir) / "output.txt"
    }

@byzerllm.prompt()
def base_enable_index()->str:
    '''
    skip_build_index: false
    anti_quota_limit: 0
    index_filter_level: 1
    index_filter_workers: 100
    index_build_workers: 100
    '''

@byzerllm.prompt()
def base_enable_search_engine()->str:
    '''
    ## Get the search engine token in the environment variable
    ## 在环境变量中获取搜索引擎令牌
    ## Ask for Bing Search API Token. You can visit https://www.microsoft.com/en-us/bing/apis/bing-web-search-api to get the token.
    ## 申请 Bing 搜索API Token。你可以访问 https://www.microsoft.com/en-us/bing/apis/bing-web-search-api 获取 token。
    search_engine: bing
    search_engine_token: ENV {{BING_SEARCH_TOKEN}}
    '''    

@byzerllm.prompt()
def base_enable_rag_search()->str:
    '''
    collections: default
    enable_rag_search: |
      byzerllm  使用 openai_tts模型的 python 代码
    '''

@byzerllm.prompt()
def base_exclude_files()->str:
    '''
    exclude_files:
      - human://所有包含xxxx目录的路径
      - regex://.*\.git.*
    '''

@byzerllm.prompt()
def base_enable_diff()->str:
    '''
    auto_merge: diff
    '''    

@byzerllm.prompt()
def base_enable_wholefile()->str:
    '''
    auto_merge: wholefile
    '''    