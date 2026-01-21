@echo off
chcp 65001 >nul

:: 最小化自身
if "%1"=="min" goto run
start /min "" "%~f0" min
exit

:run
cd /d "%~dp0"

echo 正在启动后台服务...

:: 启动 Python Web 服务（无窗口）
start "" pythonw SimpleDownloadAnime.py

:: 等待端口 8105 就绪（最多等 10 秒）
for /L %%i in (1,1,10) do (
    timeout /t 1 >nul
    powershell -command "if(Test-NetConnection 127.0.0.1 -Port 8105 -InformationLevel Quiet){exit 0}else{exit 1}" && goto open
)

echo 服务启动超时
exit

:open
start "" "http://127.0.0.1:8105"
exit
