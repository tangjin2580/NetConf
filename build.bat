@echo off
REM 医保网络配置工具 - 打包脚本
REM 用于将Python项目打包成Windows可执行文件

echo ======================================
echo 医保网络配置工具 - 打包脚本
echo ======================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python
    pause
    exit /b 1
)

echo [1/4] 检查依赖...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [安装] 正在安装PyInstaller...
    pip install pyinstaller
)

echo [2/4] 清理旧文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

echo [3/4] 开始打包主程序...
pyinstaller --clean main.spec

if errorlevel 1 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo [4/4] 打包服务器程序（可选）...
pyinstaller --clean --onefile --name="医保配置服务器" server.py

echo.
echo ======================================
echo ✅ 打包完成!
echo ======================================
echo.
echo 生成的文件位于 dist 目录:
dir dist /b
echo.
echo 使用说明:
echo 1. 医保网络配置工具.exe - 主程序（需管理员权限）
echo 2. 医保配置服务器.exe - HTTP服务器（可选）
echo.
pause
