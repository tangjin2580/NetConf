@echo off
chcp 65001 >nul
echo ============================================
echo 医保网络配置工具 - 打包脚本
echo ============================================

REM 检查依赖
echo [1/3] 检查依赖...
python test_dependencies.py
if errorlevel 1 (
    echo ❌ 依赖检查失败，请先安装依赖
    pause
    exit /b 1
)

REM 清理旧文件
echo [2/3] 清理旧文件...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

REM 打包
echo [3/3] 正在打包...
pyinstaller --onefile ^
    --name "医保网络配置工具" ^
    --windowed ^
    --icon=None ^
    Conf.py

echo.
echo ============================================
if exist dist\医保网络配置工具.exe (
    echo ✅ 打包成功！
    echo 文件位置: dist\医保网络配置工具.exe
) else (
    echo ❌ 打包失败
)
echo ============================================
pause
