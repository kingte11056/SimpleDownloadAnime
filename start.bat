@echo off
setlocal
cd /d "%~dp0"
title Mikan Manager Pro (Virtual Env)

:: 设置虚拟环境目录名称
set VENV_DIR=.venv

:: 1. 检查虚拟环境是否存在
if not exist %VENV_DIR%\Scripts\activate (
    color 0E
    echo [提示] 未发现虚拟环境，正在尝试自动创建...
    python -m venv %VENV_DIR%
    if %errorlevel% neq 0 (
        echo [错误] 虚拟环境创建失败，请确保已安装 Python 3.x。
        pause
        exit /b
    )
    echo [成功] 虚拟环境已创建在 %VENV_DIR% 目录下。
    echo [提示] 正在安装依赖库，请稍候...
    %VENV_DIR%\Scripts\pip install -r requirements.txt
)

:: 2. 自动唤起 Web 界面
echo [1/2] 正在打开浏览器访问 http://127.0.0.1:8105 ...
start "" "http://127.0.0.1:8105"

:: 3. 激活虚拟环境并启动程序
echo [2/2] 正在通过虚拟环境启动后端服务...
echo.
%VENV_DIR%\Scripts\python SimpleDownloadAnime.py

if %errorlevel% neq 0 (
    echo.
    echo [警告] 程序异常退出，请检查依赖是否完整。
    pause
)