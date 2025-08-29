@echo off
REM Rust 安装脚本

echo 🦀 Jenkins CLI Rust 版本安装指南
echo.
echo 1. 正在下载并安装 Rust...
echo    如果下载失败，请手动访问: https://rustup.rs/
echo.

REM 下载并运行 rustup 安装器
echo 正在下载 Rust 安装器...
curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs -o rustup-init.sh

if exist rustup-init.sh (
    echo 运行安装器...
    bash rustup-init.sh -y
    echo.
    echo ✅ Rust 安装完成！
    echo.
    echo 2. 请重新启动命令提示符或运行以下命令来更新环境变量:
    echo    source ~/.cargo/env
    echo.
    echo 3. 然后运行 build_rust.bat 来编译 Jenkins CLI
    del rustup-init.sh
) else (
    echo ❌ 下载失败，请手动安装 Rust:
    echo    1. 访问 https://rustup.rs/
    echo    2. 下载并运行 rustup-init.exe
    echo    3. 按照安装向导完成安装
    echo    4. 重新启动命令提示符
    echo    5. 运行 build_rust.bat
)

echo.
echo 📖 安装完成后，你可以使用以下命令:
echo    cargo --version     # 检查 Cargo 版本
echo    rustc --version     # 检查 Rust 编译器版本
echo    .\build_rust.bat    # 编译 Jenkins CLI
