# 多阶段构建，使用最新Go版本
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -a -installsuffix cgo -o jenkins-app .

# 最终运行阶段使用轻量级镜像
FROM alpine:latest

# 添加ca证书以支持HTTPS
RUN apk --no-cache add ca-certificates

WORKDIR /root/

# 从构建阶段复制二进制文件
COPY --from=builder /app/jenkins-app .

# 添加非root用户提高安全性
RUN adduser -D -s /bin/sh appuser
USER appuser

EXPOSE 8080

CMD ["./jenkins-app"]
