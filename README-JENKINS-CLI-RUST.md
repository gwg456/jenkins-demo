# Jenkins CLI - Rust 版本

🦀 基于 Rust 开发的 Jenkins CLI 工具，支持跨平台编译。

## 功能特性

- ✅ 触发 Jenkins Job
- ✅ 查看 Job 状态  
- ✅ 安全的错误处理（不暴露敏感信息）
- ✅ 跨平台支持（Windows、macOS、Linux）
- ✅ 支持 ARM64 架构

## 安装 Rust 环境

### Windows
```bash
# 方法1: 使用提供的脚本
.\install_rust.bat

# 方法2: 手动安装
# 1. 访问 https://rustup.rs/
# 2. 下载并运行 rustup-init.exe
# 3. 按照向导完成安装
# 4. 重新启动命令提示符
```

### Linux/macOS
```bash
# 安装 Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# 验证安装
cargo --version
rustc --version
```

## 编译说明

### Windows 用户
```bash
# 编译所有平台版本
.\build_rust.bat

# 或者只编译当前平台
cargo build --bin jenkins-cli --release
```

### Linux/macOS 用户
```bash
# 编译所有平台版本
./build_rust.sh

# 或者只编译当前平台
cargo build --bin jenkins-cli --release
```

## 编译输出

编译成功后，可执行文件将保存在 `rust-dist/` 目录：

- `jenkins-cli-windows-amd64.exe` - Windows AMD64
- `jenkins-cli-macos-amd64` - macOS AMD64  
- `jenkins-cli-macos-arm64` - macOS ARM64 (Apple Silicon)
- `jenkins-cli-linux-amd64` - Linux AMD64
- `jenkins-cli-linux-arm64` - Linux ARM64

## 使用方法

### 基本命令

```bash
# 触发 Job
jenkins-cli job [job-name]

# 查看 Job 状态
jenkins-cli status [job-name]

# 显示帮助
jenkins-cli help
```

### 示例

```bash
# Windows
.\rust-dist\jenkins-cli-windows-amd64.exe job my-project
.\rust-dist\jenkins-cli-windows-amd64.exe status my-project

# macOS/Linux
./rust-dist/jenkins-cli-macos-amd64 job my-project
./rust-dist/jenkins-cli-linux-amd64 status my-project
```

## 配置

在 `src/jenkins_cli.rs` 中修改以下配置：

```rust
const JENKINS_URL: &str = "http://your-jenkins-server:8080";
const API_TOKEN: &str = "your-api-token-here";
const USERNAME: &str = "your-username";
const JOB_NAME: &str = "jenkins-demo";
```

## 依赖库

- `reqwest` - HTTP 客户端
- `clap` - 命令行参数解析
- `serde_json` - JSON 处理
- `anyhow` - 错误处理
- `base64` - Base64 编码

## 注意事项

1. **跨平台编译**: 某些目标平台可能需要额外的链接器配置
2. **网络访问**: 确保能够访问 Jenkins 服务器
3. **认证**: 需要有效的用户名和 API Token
4. **权限**: 确保用户有触发和查看 Job 的权限

## 故障排除

### 编译失败
```bash
# 更新 Rust 工具链
rustup update

# 添加目标平台
rustup target add x86_64-apple-darwin
rustup target add aarch64-apple-darwin
rustup target add x86_64-unknown-linux-gnu
rustup target add aarch64-unknown-linux-gnu
```

### 跨平台编译问题
如果跨平台编译失败，建议在对应的平台上直接编译：
```bash
# 在目标平台上执行
cargo build --bin jenkins-cli --release
```

## 与 Go 版本的区别

| 特性 | Go 版本 | Rust 版本 |
|------|---------|-----------|
| 编译速度 | 快 | 中等 |
| 可执行文件大小 | 较大 | 较小 |
| 内存安全 | 运行时检查 | 编译时检查 |
| 依赖管理 | go.mod | Cargo.toml |
| 错误处理 | error 接口 | Result<T, E> |
| 命令行解析 | 手工实现 | clap 库 |

## 开发

### 本地测试
```bash
# 运行测试
cargo test

# 检查代码
cargo check

# 格式化代码
cargo fmt

# 代码检查
cargo clippy
```

### 调试模式编译
```bash
cargo build --bin jenkins-cli
./target/debug/jenkins-cli help
```

