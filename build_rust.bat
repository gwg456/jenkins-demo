@echo off
REM Jenkins CLI Rust 跨平台编译脚本

setlocal enabledelayedexpansion

echo 🦀 Jenkins CLI Rust 版本编译脚本
echo.

REM 检查 Rust 是否安装
cargo --version >nul 2>&1
if !errorlevel! neq 0 (
    echo ❌ 错误: 未检测到 Rust 环境
    echo 请先运行 install_rust.bat 安装 Rust
    echo 或手动安装: https://rustup.rs/
    exit /b 1
)

echo ✅ 检测到 Rust 环境
cargo --version
echo.

set BUILD_DIR=rust-dist
set APP_NAME=jenkins-cli

echo 📁 创建构建目录: %BUILD_DIR%
if exist %BUILD_DIR% rmdir /s /q %BUILD_DIR%
mkdir %BUILD_DIR%

echo.
echo 🔨 开始编译所有平台版本...
echo.

REM 编译 Windows AMD64
echo 编译 Windows AMD64...
cargo build --bin jenkins-cli --release
if !errorlevel! equ 0 (
    copy target\release\jenkins-cli.exe %BUILD_DIR%\jenkins-cli-windows-amd64.exe
    echo ✅ Windows AMD64 编译成功
) else (
    echo ❌ Windows AMD64 编译失败
)

echo.

REM 添加目标平台支持
echo 添加编译目标平台...
rustup target add x86_64-apple-darwin >nul 2>&1
rustup target add aarch64-apple-darwin >nul 2>&1
rustup target add x86_64-unknown-linux-gnu >nul 2>&1
rustup target add aarch64-unknown-linux-gnu >nul 2>&1

REM 编译 macOS AMD64
echo 编译 macOS AMD64...
cargo build --bin jenkins-cli --release --target x86_64-apple-darwin
if !errorlevel! equ 0 (
    copy target\x86_64-apple-darwin\release\jenkins-cli %BUILD_DIR%\jenkins-cli-macos-amd64
    echo ✅ macOS AMD64 编译成功
) else (
    echo ⚠️  macOS AMD64 编译失败 (可能需要额外配置)
)

REM 编译 macOS ARM64
echo 编译 macOS ARM64 (Apple Silicon)...
cargo build --bin jenkins-cli --release --target aarch64-apple-darwin
if !errorlevel! equ 0 (
    copy target\aarch64-apple-darwin\release\jenkins-cli %BUILD_DIR%\jenkins-cli-macos-arm64
    echo ✅ macOS ARM64 编译成功
) else (
    echo ⚠️  macOS ARM64 编译失败 (可能需要额外配置)
)

REM 编译 Linux AMD64
echo 编译 Linux AMD64...
cargo build --bin jenkins-cli --release --target x86_64-unknown-linux-gnu
if !errorlevel! equ 0 (
    copy target\x86_64-unknown-linux-gnu\release\jenkins-cli %BUILD_DIR%\jenkins-cli-linux-amd64
    echo ✅ Linux AMD64 编译成功
) else (
    echo ⚠️  Linux AMD64 编译失败 (可能需要额外配置)
)

REM 编译 Linux ARM64
echo 编译 Linux ARM64...
cargo build --bin jenkins-cli --release --target aarch64-unknown-linux-gnu
if !errorlevel! equ 0 (
    copy target\aarch64-unknown-linux-gnu\release\jenkins-cli %BUILD_DIR%\jenkins-cli-linux-arm64
    echo ✅ Linux ARM64 编译成功
) else (
    echo ⚠️  Linux ARM64 编译失败 (可能需要额外配置)
)

echo.
echo 🎉 编译完成！
echo 📁 输出目录: %BUILD_DIR%
echo.
echo 📋 编译结果:
dir %BUILD_DIR%

echo.
echo 🔧 使用方法:
echo   Windows:  .\%BUILD_DIR%\jenkins-cli-windows-amd64.exe help
echo   macOS:    ./%BUILD_DIR%/jenkins-cli-macos-amd64 help
echo   Linux:    ./%BUILD_DIR%/jenkins-cli-linux-amd64 help
echo.
echo 💡 注意: 跨平台编译可能需要额外的链接器配置
echo    如果某些平台编译失败，请在对应平台上直接编译

endlocal
