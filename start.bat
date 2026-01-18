chcp 65001
@echo off
:: 检查是否是以最小化模式运行，如果不是，则调用自己并最小化
if "%1" == "min" goto :run
start /min "" "%~0" min
exit

:run
cd /d "%~dp0"

echo 正在启动后台服务...

:: 启动后台服务 (pythonw 本身不产生窗口)
start /b python SimpleDownloadAnime.py

:: 延迟 2 秒等待服务就绪后打开浏览器
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8105"

echo 服务已在后台运行，本窗口已最小化。
:: 如果你想让窗口一直挂着，可以去掉下面的 exit 或者换成 pause
exit