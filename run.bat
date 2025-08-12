@echo off
rem 设置代码页为UTF-8，以正确显示中文字符
chcp 65001 > nul

rem start.bat
rem 启动FlowWriter后端服务的脚本 (for Windows)

echo --- 正在启动 FlowWriter 后端服务 ---
echo.

rem 步骤1: 检查.env文件是否存在
if not exist .env (
    echo 错误: .env 文件未找到！
    echo 请从.env.example复制一份并命名为.env，然后填入你的API Key。
    rem 暂停脚本，让用户看到错误信息
    pause
    exit /b 1
)

rem 步骤2: 检查虚拟环境是否存在 (注释部分)
rem 在Windows上，检查文件夹的命令是 'if not exist "venv"'
rem if not exist "venv" (
rem     echo 警告: Python虚拟环境 'venv' 不存在。正在尝试创建...
rem     python -m venv venv
rem     if %errorlevel% neq 0 (
rem         echo 错误: 创建虚拟环境失败。请确保你已安装Python和venv模块。
rem         pause
rem         exit /b 1
rem     )
rem     echo 虚拟环境已创建。请先手动激活并安装依赖:
rem     echo.
rem     echo   .\venv\Scripts\activate
rem     echo   pip install -r requirements.txt
rem     echo.
rem     pause
rem     exit /b 1
rem )

rem 步骤3: 激活虚拟环境 (注释部分)
rem 在Windows批处理脚本中，直接调用 'source' 或激活脚本通常只对当前脚本的子进程有效。
rem 对于启动uvicorn来说，更可靠的方法是直接加载环境变量。
rem 如果你需要激活环境，请手动在命令行中运行: venv\Scripts\activate
rem echo Python虚拟环境已激活。

rem 步骤4: 加载环境变量从.env文件
echo 正在从.env文件加载环境变量...
rem 使用FOR /F命令逐行读取.env文件
rem eol=# 表示以#开头的行是注释，将被忽略
rem delims= 表示不使用任何分隔符，读取整行
for /f "usebackq eol=# delims=" %%i in (".env") do (
    rem 将每一有效行设置为环境变量
    set "%%i"
)
echo 环境变量已从.env文件加载。
echo 使用的生成模型: %DEFAULT_GENERATION_MODEL%
echo.

rem 步骤5: 启动Uvicorn服务器
rem --host 0.0.0.0 使服务可以被局域网内的其他设备访问
rem 如果只想本机访问，可以使用 127.0.0.1
echo 正在启动Uvicorn服务器，请访问 http://127.0.0.1:8000
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

echo.
echo --- FlowWriter 服务已停止 ---
pause