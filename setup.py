#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cuscli - Setup配置文件
基于 auto-coder v1.0.39 进行二次开发，打造定制化的AI编程助手工具
"""

from setuptools import setup, find_packages
import os

# 读取 requirements.txt
def read_requirements():
    """读取依赖配置"""
    requirements = []
    req_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(req_file):
        with open(req_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if line and not line.startswith('#'):
                    requirements.append(line)
    return requirements

# 读取 README
def read_readme():
    """读取README文件"""
    readme_file = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_file):
        with open(readme_file, 'r', encoding='utf-8') as f:
            return f.read()
    return ''

setup(
    name='cuscli',
    version='0.9.0b1',  # Beta 测试版本 (PEP 440 合法格式)
    author='superfm831010 (Based on allwefantasy/auto-coder)',
    author_email='superfm831010@gmail.com',
    description='Cuscli: AI-powered coding assistant tool with custom enhancements (Beta Version)',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/superfm831010/cuscli',

    # 包配置
    packages=find_packages(exclude=['tests', 'tests.*', 'dist-info', 'rules', 'docs', 'actions', 'codecheck']),

    # Python 版本要求
    python_requires='>=3.10,<=3.12',

    # 依赖配置
    install_requires=read_requirements(),

    # 包数据 - 确保规则模板文件被打包
    package_data={
        'autocoder': [
            'data/rules/*.md',
            'data/rules/*.json',
            'data/*.json',
        ]
    },

    # 入口点配置 - 从 dist-info/entry_points.txt 提取
    entry_points={
        'console_scripts': [
            # CUS-CLI 主入口点
            'cuscli=autocoder.chat_auto_coder:main',
            # 原 auto-coder 入口点（保留以兼容旧脚本）
            'auto-coder=autocoder.auto_coder:main',
            'auto-coder.chat=autocoder.chat_auto_coder:main',
            'auto-coder.chat.beta=autocoder.auto_coder_terminal:main',
            'auto-coder.chat.beta3=autocoder.auto_coder_terminal_v3:main',
            'auto-coder.cli=autocoder.sdk.cli:main',
            'auto-coder.core=autocoder.auto_coder:main',
            'auto-coder.rag=autocoder.auto_coder_rag:main',
            'auto-coder.run=autocoder.sdk.cli:main',
            'chat-auto-coder=autocoder.chat_auto_coder:main',
        ],
    },

    # 分类器
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],

    # 关键词
    keywords='cuscli,autocoder,ai,coding,automation,assistant',

    # 包含非Python文件
    include_package_data=True,

    # zip_safe=False 确保包以目录形式安装，而不是zip文件
    # 这对于开发模式很重要
    zip_safe=False,
)
