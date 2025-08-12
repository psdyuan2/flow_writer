#!/bin/bash

# start.sh
# 启动FlowWriter后端服务的脚本 (for Linux/macOS)

echo "--- 正在启动 FlowWriter 后端服务 ---"



# 步骤1: 检查.env文件是否存在
if [ ! -f .env ]; then
    echo "错误: .env 文件未找到！"
    echo "请从.env.example复制一份并命名为.env，然后填入你的API Key。"
    # 你可以创建一个 .env.example 文件作为模板
    # echo "OPENAI_API_KEY=\"YourSecretKey\"" > .env.example
    exit 1
fi

# 步骤2: 检查虚拟环境是否存在
#if [ ! -d "venv" ]; then
#    echo "警告: Python虚拟环境 'venv' 不存在。正在尝试创建..."
#    python3 -m venv venv
#    if [ $? -ne 0 ]; then
#        echo "错误: 创建虚拟环境失败。请确保你已安装python3和venv模块。"
#        exit 1
#    fi
#    echo "虚拟环境已创建。请先手动激活并安装依赖: "
#    echo "source venv/bin/activate"
#    echo "pip install -r requirements.txt"
#    exit 1
#fi

# 步骤3: 激活虚拟环境
# 注意：在脚本中激活虚拟环境通常只对脚本本身生效，
# 但对于我们启动uvicorn来说已经足够。
#source .venv/bin/activate
#echo "Python虚拟环境已激活。"

# 步骤4: 加载环境变量从.env文件
# 使用 set -a 来导出变量，使其对子进程(uvicorn)可见
set -a
source .env
set +a
echo "环境变量已从.env文件加载。"
echo "使用的生成模型: $DEFAULT_GENERATION_MODEL"

# 步骤5: 启动Uvicorn服务器
# --host 0.0.0.0 使服务可以被局域网内的其他设备访问（比如手机测试）
# 如果只想本机访问，可以使用 127.0.0.1
echo "正在启动Uvicorn服务器，访问 http://127.0.0.1:8000"
uvicorn backend.main:app --host 0.0.0.0 --port 800 --reload

echo "--- FlowWriter 服务已停止 ---"
