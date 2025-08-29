# Jenkins Demo - Rust版本

这是将原Go版本转换为Rust的实现。

## 功能

该应用提供以下HTTP端点：

- `GET /` - 返回欢迎信息和分支信息
- `GET /health` - 健康检查端点
- `GET /api/info` - 返回JSON格式的应用信息

## 安装Rust

### Windows (推荐使用rustup)

1. 访问 [https://rustup.rs/](https://rustup.rs/)
2. 下载并运行 `rustup-init.exe`
3. 按照提示完成安装
4. 重启终端或运行 `source ~/.cargo/env`

### 或者使用命令行

```powershell
# PowerShell
Invoke-WebRequest -Uri "https://win.rustup.rs/" -OutFile "rustup-init.exe"
.\rustup-init.exe
```

## 本地开发

### 安装依赖

```bash
cargo build
```

### 运行应用

```bash
# 开发模式
cargo run

# 或者构建并运行发布版本
cargo build --release
./target/release/jenkins-demo
```

### 环境变量

- `PORT`: 服务器端口 (默认: 8080)
- `branch`: Git分支名称
- `VERSION`: 应用版本 (默认: 1.0.0)

## Docker构建

```bash
# 构建镜像
docker build -t jenkins-demo-rust .

# 运行容器
docker run -p 8080:8080 -e branch=main jenkins-demo-rust
```

## 项目结构

```
├── Cargo.toml          # Rust项目配置
├── src/
│   └── main.rs         # 主应用代码
├── Dockerfile          # Docker构建文件
└── README-RUST.md      # 本文档
```

## API端点

### GET /
返回简单的欢迎信息

### GET /health
返回 "OK" 用于健康检查

### GET /api/info
返回JSON格式的应用信息：

```json
{
  "message": "Hello from Jenkins Demo App",
  "branch": "main",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0"
}
```

## 与Go版本的差异

1. **性能**: Rust版本在内存使用和执行速度上通常更优
2. **安全性**: Rust的内存安全保证减少了潜在的运行时错误
3. **并发**: 使用async/await模式处理并发请求
4. **类型系统**: 更强的类型安全保证

## 依赖说明

- `actix-web`: 高性能的异步HTTP服务器框架
- `serde`: 序列化/反序列化库
- `chrono`: 日期时间处理
- `tokio`: 异步运行时
- `env_logger`: 日志记录 