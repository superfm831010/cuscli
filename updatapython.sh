#!/bin/bash

# 安装编译依赖
echo "安装必要的依赖包..."
sudo apt update
sudo apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev \
    libnss3-dev libssl-dev libreadline-dev libffi-dev wget libbz2-dev

# 下载Python 3.11.9源码
echo "下载Python 3.11.9..."
wget https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz

# 解压源码包
echo "解压源码包..."
tar -xf Python-3.11.9.tgz
cd Python-3.11.9

# 配置编译选项
echo "配置编译选项..."
./configure --enable-optimizations --prefix=/usr/local/python3.11

# 编译并安装
echo "开始编译安装..."
make -j $(nproc)  # 使用所有可用的CPU核心加速编译
sudo make altinstall  # 使用altinstall避免替换系统默认Python

# 清理安装文件
echo "清理安装文件..."
cd ..
rm -rf Python-3.11.9 Python-3.11.9.tgz

# 创建软链接
echo "创建软链接..."
sudo ln -s /usr/local/python3.11/bin/python3.11 /usr/bin/python3.11
sudo ln -s /usr/local/python3.11/bin/pip3.11 /usr/bin/pip3.11

# 验证安装
echo "验证安装..."
python3.11 --version
pip3.11 --version

echo "Python 3.11.9 安装完成！"

