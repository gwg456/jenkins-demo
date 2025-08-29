# 项目结构说明

## 📁 目录结构

```
jenkins-demo/
├── 🚀 Web应用 (主要功能)
│   ├── main.go              # Go版本的Web服务
│   ├── go.mod               # Go依赖管理
│   ├── src/main.rs          # Rust版本的Web服务
│   └── Cargo.toml           # Rust依赖管理
├── 🐳 容器化部署
│   ├── Dockerfile           # Docker构建文件
│   └── .dockerignore        # Docker忽略文件
├── ☸️  Kubernetes部署
│   └── k8s.yaml             # K8s部署配置
├── 🔄 CI/CD流水线
│   ├── Jenkinsfile          # Go版本的CI/CD
│   └── Jenkinsfile.rust     # Rust版本的CI/CD
├── 🛠️  网络诊断工具 (辅助功能)
│   ├── network_diagnostic.py      # Python网络诊断
│   ├── network_diagnostic_pure.py # 纯Python版本
│   └── mtr_test.sh               # MTR测试脚本
├── 📚 文档
│   ├── README.md            # 主要文档
│   ├── README-RUST.md       # Rust版本说明
│   └── PROJECT_STRUCTURE.md # 本文档
└── 🔧 配置文件
    ├── .gitignore           # Git忽略规则
    └── demo_usage.py        # 使用示例(待完善)
```

## 🎯 组件说明

### Web应用服务
- **主要功能**: 提供HTTP API服务
- **技术栈**: Go 1.21 / Rust (两个版本)
- **端点**: `/`, `/health`, `/api/info`

### 网络诊断工具
- **作用**: 网络连通性测试和故障排查
- **用途**: 可用于部署后的网络验证
- **独立性**: 与Web应用功能解耦

### CI/CD流水线
- **Go版本**: 使用 `Jenkinsfile`
- **Rust版本**: 使用 `Jenkinsfile.rust`
- **功能**: 自动化构建、测试、部署

## 🔄 使用场景

1. **开发阶段**: 选择Go或Rust版本进行开发
2. **测试阶段**: 使用网络诊断工具验证部署
3. **部署阶段**: 通过Jenkins自动化部署到K8s
4. **运维阶段**: 使用诊断工具排查网络问题 