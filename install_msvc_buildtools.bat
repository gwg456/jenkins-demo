@echo off
REM Microsoft C++ Build Tools 安装脚本

echo 🔧 Jenkins CLI Rust - Microsoft C++ Build Tools 安装
echo.
echo 在Windows上编译Rust程序需要Microsoft的构建工具
echo.

echo 📋 需要安装的组件:
echo   - Microsoft C++ Build Tools
echo   - Windows SDK
echo   - MSVC编译器工具集
echo.

echo 🌐 方法1: 自动下载并安装 Visual Studio Build Tools
echo.

REM 下载 Visual Studio Build Tools
echo 正在下载 Visual Studio Build Tools...
powershell -Command "Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vs_buildtools.exe' -OutFile 'vs_buildtools.exe'"

if exist vs_buildtools.exe (
    echo ✅ 下载完成！
    echo.
    echo 🚀 启动安装程序...
    echo.
    echo 📝 请在安装程序中选择以下组件:
    echo   ✓ C++ build tools
    echo   ✓ Windows 11 SDK (最新版本)
    echo   ✓ MSVC v143 - VS 2022 C++ x64/x86 build tools
    echo   ✓ CMake tools for Visual Studio
    echo.
    
    REM 启动安装程序并等待用户手动选择组件
    start /wait vs_buildtools.exe --add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.Windows11SDK.22621 --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 --quiet
    
    echo.
    echo ✅ 安装完成！
    echo.
    echo 🔄 请重新启动命令提示符，然后运行:
    echo    cargo build --bin jenkins-cli
    
    del vs_buildtools.exe
) else (
    echo ❌ 下载失败，请手动安装:
    echo.
    echo 🌐 方法2: 手动安装
    echo   1. 访问: https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo   2. 下载 "Build Tools for Visual Studio 2022"
    echo   3. 运行安装程序
    echo   4. 选择 "C++ build tools" 工作负载
    echo   5. 确保包含:
    echo      - MSVC v143 编译器工具集
    echo      - Windows SDK
    echo      - CMake tools
    echo.
    echo 🌐 方法3: 安装完整 Visual Studio Community
    echo   1. 访问: https://visualstudio.microsoft.com/vs/community/
    echo   2. 下载并安装 Visual Studio Community
    echo   3. 选择 "使用C++的桌面开发" 工作负载
)

echo.
echo 📖 安装完成后的验证步骤:
echo   1. 重新启动命令提示符
echo   2. 运行: rustc --version
echo   3. 运行: cargo build --bin jenkins-cli
echo   4. 检查: target\debug\jenkins-cli.exe
echo.
echo 💡 如果还有问题，可以尝试:
echo   rustup default stable-x86_64-pc-windows-msvc
echo   rustup component add rust-src

