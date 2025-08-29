# Jenkins CLI Makefile
# 支持跨平台编译

APP_NAME := jenkins-cli
BUILD_DIR := dist
SOURCE := jenkins-cli.go

# 默认目标
.PHONY: all clean build-windows build-darwin build-linux help

all: clean build-all

# 清理构建目录
clean:
	@echo "🧹 清理构建目录..."
	@rm -rf $(BUILD_DIR)
	@mkdir -p $(BUILD_DIR)

# 构建所有平台
build-all: build-windows build-darwin build-linux
	@echo ""
	@echo "🎉 所有平台编译完成！"
	@echo "📁 输出目录: $(BUILD_DIR)"
	@ls -la $(BUILD_DIR)/

# Windows 平台编译
build-windows:
	@echo "🔨 编译 Windows AMD64..."
	@GOOS=windows GOARCH=amd64 go build -a -ldflags="-w -s" -o $(BUILD_DIR)/$(APP_NAME)-windows-amd64.exe $(SOURCE)
	@echo "✅ Windows AMD64 编译完成"

# macOS 平台编译
build-darwin:
	@echo "🔨 编译 macOS AMD64..."
	@GOOS=darwin GOARCH=amd64 go build -a -ldflags="-w -s" -o $(BUILD_DIR)/$(APP_NAME)-darwin-amd64 $(SOURCE)
	@echo "✅ macOS AMD64 编译完成"
	@echo "🔨 编译 macOS ARM64 (Apple Silicon)..."
	@GOOS=darwin GOARCH=arm64 go build -a -ldflags="-w -s" -o $(BUILD_DIR)/$(APP_NAME)-darwin-arm64 $(SOURCE)
	@echo "✅ macOS ARM64 编译完成"

# Linux 平台编译
build-linux:
	@echo "🔨 编译 Linux AMD64..."
	@GOOS=linux GOARCH=amd64 go build -a -ldflags="-w -s" -o $(BUILD_DIR)/$(APP_NAME)-linux-amd64 $(SOURCE)
	@echo "✅ Linux AMD64 编译完成"
	@echo "🔨 编译 Linux ARM64..."
	@GOOS=linux GOARCH=arm64 go build -a -ldflags="-w -s" -o $(BUILD_DIR)/$(APP_NAME)-linux-arm64 $(SOURCE)
	@echo "✅ Linux ARM64 编译完成"

# 只编译当前平台
build-local:
	@echo "🔨 编译当前平台..."
	@go build -a -ldflags="-w -s" -o $(BUILD_DIR)/$(APP_NAME) $(SOURCE)
	@echo "✅ 当前平台编译完成"

# 显示帮助信息
help:
	@echo "Jenkins CLI 编译工具"
	@echo ""
	@echo "可用命令:"
	@echo "  make all           - 清理并编译所有平台"
	@echo "  make build-all     - 编译所有平台"
	@echo "  make build-windows - 只编译 Windows 版本"
	@echo "  make build-darwin  - 只编译 macOS 版本"
	@echo "  make build-linux   - 只编译 Linux 版本"
	@echo "  make build-local   - 只编译当前平台"
	@echo "  make clean         - 清理构建目录"
	@echo "  make help          - 显示此帮助信息"
	@echo ""
	@echo "支持的平台:"
	@echo "  Windows AMD64"
	@echo "  macOS AMD64"
	@echo "  macOS ARM64 (Apple Silicon)"
	@echo "  Linux AMD64"
	@echo "  Linux ARM64"
