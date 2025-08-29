@echo off
REM Jenkins CLI 跨平台编译脚本 (Windows版本)
REM 支持 Windows, macOS, Linux 的 AMD64 和 ARM64 架构

setlocal enabledelayedexpansion

set APP_NAME=jenkins-cli
set BUILD_DIR=dist

echo 🚀 开始编译 Jenkins CLI...

REM 创建构建目录
if exist %BUILD_DIR% rmdir /s /q %BUILD_DIR%
mkdir %BUILD_DIR%

echo 🔨 编译 Windows AMD64...
set GOOS=windows
set GOARCH=amd64
go build -a -ldflags="-w -s" -o %BUILD_DIR%\%APP_NAME%-windows-amd64.exe jenkins-cli.go
if !errorlevel! neq 0 (
    echo ❌ 编译失败: Windows AMD64
    exit /b 1
)
echo ✅ 编译成功: %BUILD_DIR%\%APP_NAME%-windows-amd64.exe

echo 🔨 编译 macOS AMD64...
set GOOS=darwin
set GOARCH=amd64
go build -a -ldflags="-w -s" -o %BUILD_DIR%\%APP_NAME%-darwin-amd64 jenkins-cli.go
if !errorlevel! neq 0 (
    echo ❌ 编译失败: macOS AMD64
    exit /b 1
)
echo ✅ 编译成功: %BUILD_DIR%\%APP_NAME%-darwin-amd64

echo 🔨 编译 macOS ARM64 (Apple Silicon)...
set GOOS=darwin
set GOARCH=arm64
go build -a -ldflags="-w -s" -o %BUILD_DIR%\%APP_NAME%-darwin-arm64 jenkins-cli.go
if !errorlevel! neq 0 (
    echo ❌ 编译失败: macOS ARM64
    exit /b 1
)
echo ✅ 编译成功: %BUILD_DIR%\%APP_NAME%-darwin-arm64

echo 🔨 编译 Linux AMD64...
set GOOS=linux
set GOARCH=amd64
go build -a -ldflags="-w -s" -o %BUILD_DIR%\%APP_NAME%-linux-amd64 jenkins-cli.go
if !errorlevel! neq 0 (
    echo ❌ 编译失败: Linux AMD64
    exit /b 1
)
echo ✅ 编译成功: %BUILD_DIR%\%APP_NAME%-linux-amd64

echo 🔨 编译 Linux ARM64...
set GOOS=linux
set GOARCH=arm64
go build -a -ldflags="-w -s" -o %BUILD_DIR%\%APP_NAME%-linux-arm64 jenkins-cli.go
if !errorlevel! neq 0 (
    echo ❌ 编译失败: Linux ARM64
    exit /b 1
)
echo ✅ 编译成功: %BUILD_DIR%\%APP_NAME%-linux-arm64

echo.
echo 🎉 所有平台编译完成！
echo 📁 输出目录: %BUILD_DIR%
echo.
echo 📋 编译结果:
dir %BUILD_DIR%

echo.
echo 🔧 使用方法:
echo   Windows:  .\%BUILD_DIR%\jenkins-cli-windows-amd64.exe help
echo   macOS:    ./%BUILD_DIR%/jenkins-cli-darwin-amd64 help  
echo   Linux:    ./%BUILD_DIR%/jenkins-cli-linux-amd64 help

endlocal
