@echo off
REM 医保网络配置工具 - 本地打包脚本
REM 默认打包 Win7 兼容版（运行库已内置，目标机免安装）
REM 与 CI (.github/workflows/build.yml) 使用同一套 spec，保证本地/云端一致

echo ======================================
echo 医保网络配置工具 - 打包脚本
echo ======================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.8
    pause
    exit /b 1
)

echo [1/4] 检查依赖...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [安装] 正在安装PyInstaller...
    pip install "pyinstaller>=5.13.0,<6.0.0"
)

echo [2/4] 清理旧文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

echo [3/4] 开始打包主程序（Win7 兼容版，运行库已内置）...
pyinstaller --clean Conf-win7.spec

if errorlevel 1 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo [4/4] 打包服务器程序（可选，运行库已内置）...
pyinstaller --clean server-win7.spec

echo.
echo ======================================
echo 打包完成!
echo ======================================
echo.
echo 生成的文件位于 dist 目录:
dir dist /b
echo.
echo 使用说明:
echo 1. 医保网络配置工具-Win7\ 主程序（需管理员权限，运行库已内置）
echo 2. 医保配置服务器\   独立 HTTP 服务器（可选，运行库已内置）
echo.
echo 如需打包 Win10/11 版本，请将 Conf-win7.spec 替换为 Conf-win10.spec
echo.
pause
