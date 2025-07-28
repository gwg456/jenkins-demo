# Jenkins Demo - Go Web 应用

[![Build Status](https://jenkins.example.com/buildStatus/icon?job=jenkins-demo)](https://jenkins.example.com/job/jenkins-demo/)
[![Go Version](https://img.shields.io/badge/Go-1.21-blue.svg)](https://golang.org)
[![Docker](https://img.shields.io/badge/Docker-supported-blue.svg)](https://www.docker.com)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-supported-blue.svg)](https://kubernetes.io)

## 📋 项目简介

这是一个用于演示 Jenkins CI/CD 流程的 Go Web 应用程序。项目展示了如何将一个简单的 Go 应用程序通过 Jenkins 自动构建、测试、打包为 Docker 镜像，并部署到 Kubernetes 集群中。

## 🏗️ 技术架构

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   GitHub    │───▶│   Jenkins   │───▶│   Docker    │───▶│ Kubernetes  │
│   代码仓库   │    │   CI/CD     │    │   镜像仓库   │    │   集群部署   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### 核心组件
- **Go 1.21**: 主要编程语言
- **Docker**: 容器化打包
- **Jenkins**: CI/CD 自动化流水线
- **Kubernetes**: 容器编排和部署
- **阿里云容器镜像服务**: Docker 镜像存储

## 🚀 功能特性

### Web 服务端点
- `GET /` - 主页，显示欢迎信息和分支信息
- `GET /health` - 健康检查端点
- `GET /api/info` - 返回应用信息的 JSON 格式数据

### 示例响应
```bash
# 健康检查
curl http://localhost:8080/health
# 响应: OK

# 应用信息
curl http://localhost:8080/api/info
# 响应:
{
  "message": "Hello from Jenkins Demo App",
  "branch": "master",
  "timestamp": "2024-01-15T10:30:45Z",
  "version": "1.0.0"
}
```

## 🛠️ 本地开发

### 环境要求
- Go 1.21+
- Docker
- Git

### 快速开始
```bash
# 克隆项目
git clone https://github.com/your-username/jenkins-demo.git
cd jenkins-demo

# 运行应用
go mod tidy
go run main.go

# 访问应用
curl http://localhost:8080
```

### 运行测试
```bash
# 运行所有测试
go test -v ./...

# 生成覆盖率报告
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out -o coverage.html

# 性能测试
go test -bench=. ./...
```

## 🐳 Docker 部署

### 构建镜像
```bash
# 构建 Docker 镜像
docker build -t jenkins-demo:latest .

# 运行容器
docker run -p 8080:8080 \
  -e branch=main \
  -e VERSION=1.0.0 \
  jenkins-demo:latest
```

### 多阶段构建优势
- **安全性**: 使用非 root 用户运行
- **体积小**: 最终镜像基于 Alpine Linux
- **性能好**: 静态编译的 Go 二进制文件

## ☸️ Kubernetes 部署

### 部署到集群
```bash
# 应用 Kubernetes 配置
kubectl apply -f k8s.yaml

# 检查部署状态
kubectl get deployments
kubectl get pods
kubectl get services

# 查看应用日志
kubectl logs -l app=jenkins-demo
```

### 配置说明
- **Deployment**: 2 个副本，滚动更新
- **Service**: ClusterIP 类型，端口映射 80:8080
- **HPA**: 自动扩缩容，基于 CPU 和内存使用率
- **健康检查**: Liveness 和 Readiness 探针
- **资源限制**: 内存 128Mi，CPU 100m

## 🔄 CI/CD 流水线

### Jenkins 流水线阶段
1. **准备阶段** - 检出代码，设置构建标签
2. **代码质量** - 并行执行代码规范检查和安全扫描
3. **测试阶段** - 运行单元测试，生成覆盖率报告
4. **构建阶段** - 构建 Docker 镜像，执行安全扫描
5. **推送阶段** - 推送镜像到容器注册中心
6. **部署阶段** - 部署到 Kubernetes 集群
7. **验证阶段** - 部署后健康检查

### 分支策略
- **master 分支**: 自动部署到生产环境（需人工确认）
- **其他分支**: 自动部署到测试环境
- **标签规则**: `分支名-commitId` 或 `commitId`（master分支）

## 📊 监控和观测

### 健康检查
```bash
# Kubernetes 探针检查
kubectl describe pod <pod-name>

# 手动健康检查
kubectl port-forward svc/jenkins-demo-service 8080:80
curl http://localhost:8080/health
```

### 日志查看
```bash
# 查看应用日志
kubectl logs -f deployment/jenkins-demo

# 查看特定 Pod 日志
kubectl logs -f <pod-name>
```

## 🔧 配置管理

### 环境变量
| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `PORT` | 服务端口 | `8080` |
| `branch` | Git 分支名 | `unknown` |
| `VERSION` | 应用版本 | `1.0.0` |

### Jenkins 凭据配置
需要在 Jenkins 中配置以下凭据：
- `aliyun-docker-registry`: 阿里云容器镜像服务的用户名和密码

## 🚨 故障排除

### 常见问题

1. **构建失败**
   ```bash
   # 检查 Go 版本
   go version
   
   # 清理模块缓存
   go clean -modcache
   ```

2. **Docker 构建失败**
   ```bash
   # 检查 Docker 版本
   docker version
   
   # 清理构建缓存
   docker builder prune
   ```

3. **Kubernetes 部署失败**
   ```bash
   # 检查集群状态
   kubectl cluster-info
   
   # 查看部署事件
   kubectl describe deployment jenkins-demo
   ```

## 🔮 未来改进计划

### 短期计划
- [ ] 添加 Prometheus 监控指标
- [ ] 集成日志聚合系统（ELK Stack）
- [ ] 添加更多的单元测试和集成测试
- [ ] 实现优雅关闭机制

### 长期计划  
- [ ] 支持多环境配置管理
- [ ] 实现蓝绿部署策略
- [ ] 添加性能监控和告警
- [ ] 集成 Service Mesh（Istio）

## 🤝 贡献指南

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

- 项目维护者: [Your Name](mailto:your.email@example.com)
- 项目地址: [https://github.com/your-username/jenkins-demo](https://github.com/your-username/jenkins-demo)
- 问题反馈: [GitHub Issues](https://github.com/your-username/jenkins-demo/issues)

---

⭐ 如果这个项目对你有帮助，请给一个 Star！
