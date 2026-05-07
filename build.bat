@echo off
echo ==========================================
echo   数据分析系统 Windows 安装程序
echo ==========================================
echo.

:: 1. 从 macOS 下载项目文件
echo [1/3] 下载项目文件...
curl -o shujufenxi.tar.gz http://192.168.10.36:8888/shujufenxi.tar.gz
if errorlevel 1 (
    echo 下载失败！请确认：
    echo   1. 本机与 192.168.10.36 在同一局域网
    echo   2. macOS 已启动 HTTP 服务器
    pause
    exit /b 1
)
echo  下载完成 ✓
echo.

:: 2. 解压
echo [2/3] 解压项目...
tar -xzf shujufenxi.tar.gz
if not exist "shujufenxi" (
    echo 解压失败！
    pause
    exit /b 1
)
echo  解压完成 ✓
echo.

:: 3. 打包
echo [3/3] 开始打包...
cd shujufenxi
python build_windows.py
if errorlevel 1 (
    echo.
    echo 打包失败！
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   打包完成！
echo ==========================================
echo.
echo 可执行文件位置：
echo   %cd%\dist\数据分析系统.exe
echo.
pause
