@echo off
echo ========================================
echo   安全局域网聊天工具启动脚本
echo ========================================
echo.

echo 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.6+
    pause
    exit /b 1
)

echo 检查依赖包...
pip list | findstr "flask" >nul
if errorlevel 1 (
    echo 安装Flask...
    pip install flask
)

pip list | findstr "pywebview" >nul
if errorlevel 1 (
    echo 安装pywebview...
    pip install pywebview
)

echo.
echo 启动聊天工具...
python main.py

echo.
echo 应用已关闭
pause