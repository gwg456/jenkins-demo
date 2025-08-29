#!/bin/bash

# Jenkins CLI 跨平台编译脚本
# 支持 Windows, macOS, Linux 的 AMD64 和 ARM64 架构

set -e

APP_NAME="jenkins-cli"
VERSION=$(date +%Y%m%d%H%M%S)
BUILD_DIR="dist"

echo "🚀 开始编译 Jenkins CLI..."
echo "📦 版本: $VERSION"

# 创建构建目录
mkdir -p $BUILD_DIR
rm -rf $BUILD_DIR/*

# 编译目标平台配置
declare -a platforms=(
    "windows/amd64"
    "darwin/amd64"
    "darwin/arm64" 
    "linux/amd64"
    "linux/arm64"
)

# 遍历所有平台进行编译
for platform in "${platforms[@]}"
do
    platform_split=(${platform//\// })
    GOOS=${platform_split[0]}
    GOARCH=${platform_split[1]}
    
    output_name=$APP_NAME'-'$GOOS'-'$GOARCH
    if [ $GOOS = "windows" ]; then
        output_name+='.exe'
    fi
    
    echo "🔨 编译 $GOOS/$GOARCH..."
    
    env GOOS=$GOOS GOARCH=$GOARCH go build -a -ldflags="-w -s" -o $BUILD_DIR/$output_name jenkins-cli.go
    
    if [ $? -ne 0 ]; then
        echo "❌ 编译失败: $GOOS/$GOARCH"
        exit 1
    fi
    
    echo "✅ 编译成功: $BUILD_DIR/$output_name"
done

echo ""
echo "🎉 所有平台编译完成！"
echo "📁 输出目录: $BUILD_DIR"
echo ""
echo "📋 编译结果:"
ls -la $BUILD_DIR/

echo ""
echo "🔧 使用方法:"
echo "  Windows:  .\\$BUILD_DIR\\jenkins-cli-windows-amd64.exe help"
echo "  macOS:    ./$BUILD_DIR/jenkins-cli-darwin-amd64 help"
echo "  Linux:    ./$BUILD_DIR/jenkins-cli-linux-amd64 help"
