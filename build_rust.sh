#!/bin/bash

# Jenkins CLI Rust 跨平台编译脚本 (Linux/macOS 版本)

set -e

APP_NAME="jenkins-cli"
BUILD_DIR="rust-dist"

echo "🦀 Jenkins CLI Rust 版本编译脚本"
echo

# 检查 Rust 是否安装
if ! command -v cargo &> /dev/null; then
    echo "❌ 错误: 未检测到 Rust 环境"
    echo "请先安装 Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    exit 1
fi

echo "✅ 检测到 Rust 环境"
cargo --version
echo

echo "📁 创建构建目录: $BUILD_DIR"
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR

echo
echo "🔨 开始编译所有平台版本..."
echo

# 添加目标平台支持
echo "添加编译目标平台..."
rustup target add x86_64-pc-windows-gnu 2>/dev/null || true
rustup target add x86_64-apple-darwin 2>/dev/null || true
rustup target add aarch64-apple-darwin 2>/dev/null || true
rustup target add x86_64-unknown-linux-gnu 2>/dev/null || true
rustup target add aarch64-unknown-linux-gnu 2>/dev/null || true

# 编译当前平台 (默认)
echo "编译当前平台..."
cargo build --bin jenkins-cli --release
if [ $? -eq 0 ]; then
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        cp target/release/jenkins-cli.exe $BUILD_DIR/jenkins-cli-current.exe
    else
        cp target/release/jenkins-cli $BUILD_DIR/jenkins-cli-current
    fi
    echo "✅ 当前平台编译成功"
else
    echo "❌ 当前平台编译失败"
fi

# 编译 Windows AMD64 (如果不是在 Windows 上)
if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "cygwin" ]]; then
    echo "编译 Windows AMD64..."
    if cargo build --bin jenkins-cli --release --target x86_64-pc-windows-gnu 2>/dev/null; then
        cp target/x86_64-pc-windows-gnu/release/jenkins-cli.exe $BUILD_DIR/jenkins-cli-windows-amd64.exe
        echo "✅ Windows AMD64 编译成功"
    else
        echo "⚠️  Windows AMD64 编译失败 (可能需要 mingw-w64)"
    fi
fi

# 编译 macOS AMD64
echo "编译 macOS AMD64..."
if cargo build --bin jenkins-cli --release --target x86_64-apple-darwin 2>/dev/null; then
    cp target/x86_64-apple-darwin/release/jenkins-cli $BUILD_DIR/jenkins-cli-macos-amd64
    echo "✅ macOS AMD64 编译成功"
else
    echo "⚠️  macOS AMD64 编译失败 (可能需要额外配置)"
fi

# 编译 macOS ARM64
echo "编译 macOS ARM64 (Apple Silicon)..."
if cargo build --bin jenkins-cli --release --target aarch64-apple-darwin 2>/dev/null; then
    cp target/aarch64-apple-darwin/release/jenkins-cli $BUILD_DIR/jenkins-cli-macos-arm64
    echo "✅ macOS ARM64 编译成功"
else
    echo "⚠️  macOS ARM64 编译失败 (可能需要额外配置)"
fi

# 编译 Linux AMD64
echo "编译 Linux AMD64..."
if cargo build --bin jenkins-cli --release --target x86_64-unknown-linux-gnu 2>/dev/null; then
    cp target/x86_64-unknown-linux-gnu/release/jenkins-cli $BUILD_DIR/jenkins-cli-linux-amd64
    echo "✅ Linux AMD64 编译成功"
else
    echo "⚠️  Linux AMD64 编译失败 (可能需要额外配置)"
fi

# 编译 Linux ARM64
echo "编译 Linux ARM64..."
if cargo build --bin jenkins-cli --release --target aarch64-unknown-linux-gnu 2>/dev/null; then
    cp target/aarch64-unknown-linux-gnu/release/jenkins-cli $BUILD_DIR/jenkins-cli-linux-arm64
    echo "✅ Linux ARM64 编译成功"
else
    echo "⚠️  Linux ARM64 编译失败 (可能需要额外配置)"
fi

echo
echo "🎉 编译完成！"
echo "📁 输出目录: $BUILD_DIR"
echo
echo "📋 编译结果:"
ls -la $BUILD_DIR/

echo
echo "🔧 使用方法:"
echo "  Windows:  ./$BUILD_DIR/jenkins-cli-windows-amd64.exe help"
echo "  macOS:    ./$BUILD_DIR/jenkins-cli-macos-amd64 help"
echo "  Linux:    ./$BUILD_DIR/jenkins-cli-linux-amd64 help"
echo
echo "💡 注意: 跨平台编译可能需要额外的链接器配置"
echo "   如果某些平台编译失败，请在对应平台上直接编译"

