# Kubernetes 高可用集群故障恢复策略

## 🚨 故障恢复等级定义

### 故障等级分类
```yaml
P0 - 严重故障 (Critical):
  - 整个集群不可用
  - 多个 Master 节点失效
  - etcd 集群失效
  - 响应时间: 15 分钟内
  - 恢复目标: 1 小时内

P1 - 重要故障 (High):
  - 单个 Master 节点失效
  - 核心服务不可用
  - 网络分区
  - 响应时间: 30 分钟内
  - 恢复目标: 4 小时内

P2 - 一般故障 (Medium):
  - Worker 节点失效
  - 应用服务异常
  - 性能问题
  - 响应时间: 2 小时内
  - 恢复目标: 24 小时内

P3 - 轻微故障 (Low):
  - 监控告警
  - 资源使用率高
  - 日志异常
  - 响应时间: 4 小时内
  - 恢复目标: 72 小时内
```

## 🔍 故障诊断流程

### 1. 快速诊断检查清单

#### 集群整体状态检查
```bash
# 1. 检查节点状态
kubectl get nodes -o wide

# 2. 检查系统 Pod 状态
kubectl get pods -n kube-system

# 3. 检查集群组件状态
kubectl get cs

# 4. 检查 API Server 可达性
kubectl cluster-info

# 5. 检查 etcd 集群状态
kubectl -n kube-system exec -it etcd-master1 -- etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health

# 6. 检查网络连通性
kubectl run test-pod --image=busybox --rm -it --restart=Never -- nslookup kubernetes.default
```

#### 节点级别诊断
```bash
# 1. 检查节点资源使用
kubectl top nodes

# 2. 检查节点事件
kubectl describe node <node-name>

# 3. 检查 kubelet 状态
systemctl status kubelet

# 4. 检查容器运行时状态
systemctl status containerd

# 5. 检查网络插件状态
kubectl get pods -n kube-system -l app=flannel

# 6. 检查系统资源
free -h
df -h
top
```

### 2. 日志收集脚本

```bash
#!/bin/bash
# Kubernetes 故障诊断日志收集脚本

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_DIR="/tmp/k8s-diagnostics-$TIMESTAMP"
mkdir -p $LOG_DIR

echo "🔍 开始收集 Kubernetes 诊断信息..."

# 收集集群信息
echo "📊 收集集群基本信息..."
kubectl cluster-info > $LOG_DIR/cluster-info.txt
kubectl get nodes -o wide > $LOG_DIR/nodes.txt
kubectl get pods --all-namespaces -o wide > $LOG_DIR/all-pods.txt
kubectl get svc --all-namespaces > $LOG_DIR/all-services.txt
kubectl get events --all-namespaces --sort-by='.lastTimestamp' > $LOG_DIR/events.txt

# 收集系统组件日志
echo "📋 收集系统组件日志..."
kubectl logs -n kube-system -l component=kube-apiserver --tail=1000 > $LOG_DIR/apiserver.log
kubectl logs -n kube-system -l component=kube-controller-manager --tail=1000 > $LOG_DIR/controller-manager.log
kubectl logs -n kube-system -l component=kube-scheduler --tail=1000 > $LOG_DIR/scheduler.log
kubectl logs -n kube-system -l component=etcd --tail=1000 > $LOG_DIR/etcd.log

# 收集网络组件日志
echo "🌐 收集网络组件日志..."
kubectl logs -n kube-system -l app=flannel --tail=1000 > $LOG_DIR/flannel.log
kubectl logs -n kube-system -l k8s-app=kube-proxy --tail=1000 > $LOG_DIR/kube-proxy.log

# 收集节点系统日志
echo "💻 收集节点系统日志..."
journalctl -u kubelet --since="1 hour ago" > $LOG_DIR/kubelet.log
journalctl -u containerd --since="1 hour ago" > $LOG_DIR/containerd.log

# 收集配置文件
echo "⚙️ 收集配置文件..."
cp -r /etc/kubernetes $LOG_DIR/
cp /var/lib/kubelet/config.yaml $LOG_DIR/kubelet-config.yaml 2>/dev/null || true

# 收集网络配置
echo "🔌 收集网络配置..."
ip addr > $LOG_DIR/ip-addr.txt
ip route > $LOG_DIR/ip-route.txt
iptables -L -n > $LOG_DIR/iptables.txt
iptables -t nat -L -n > $LOG_DIR/iptables-nat.txt

# 打包日志文件
tar -czf k8s-diagnostics-$TIMESTAMP.tar.gz -C /tmp k8s-diagnostics-$TIMESTAMP

echo "✅ 诊断信息收集完成: k8s-diagnostics-$TIMESTAMP.tar.gz"
```

## 🛠️ 常见故障恢复方案

### 1. etcd 集群故障恢复

#### 场景 1: 单个 etcd 节点失效
```bash
# 1. 确认失效节点
ETCDCTL_API=3 etcdctl \
  --endpoints=https://10.0.1.10:2379,https://10.0.1.11:2379,https://10.0.1.12:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health

# 2. 从集群中移除失效节点
ETCDCTL_API=3 etcdctl \
  --endpoints=https://10.0.1.10:2379,https://10.0.1.11:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  member remove <member-id>

# 3. 在新节点上重新加入集群
# 在新节点上执行:
ETCDCTL_API=3 etcdctl \
  --endpoints=https://10.0.1.10:2379,https://10.0.1.11:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  member add etcd-node3 --peer-urls=https://10.0.1.12:2380

# 4. 启动新的 etcd 实例
systemctl start etcd
```

#### 场景 2: etcd 集群完全失效 (从备份恢复)
```bash
# 1. 停止所有 etcd 实例
systemctl stop etcd

# 2. 清理数据目录
rm -rf /var/lib/etcd/*

# 3. 从备份恢复 (在每个节点上执行)
ETCDCTL_API=3 etcdctl snapshot restore /backup/etcd-snapshot-latest.db \
  --name etcd-node1 \
  --initial-cluster etcd-node1=https://10.0.1.10:2380,etcd-node2=https://10.0.1.11:2380,etcd-node3=https://10.0.1.12:2380 \
  --initial-cluster-token etcd-cluster-ha \
  --initial-advertise-peer-urls https://10.0.1.10:2380 \
  --data-dir /var/lib/etcd

# 4. 启动所有 etcd 实例
systemctl start etcd

# 5. 验证集群状态
ETCDCTL_API=3 etcdctl \
  --endpoints=https://10.0.1.10:2379,https://10.0.1.11:2379,https://10.0.1.12:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health
```

### 2. API Server 故障恢复

#### 场景 1: 单个 API Server 失效
```bash
# 1. 检查 API Server 状态
systemctl status kube-apiserver

# 2. 检查配置文件
cat /etc/kubernetes/manifests/kube-apiserver.yaml

# 3. 检查证书有效性
openssl x509 -in /etc/kubernetes/pki/apiserver.crt -text -noout

# 4. 重启 API Server
systemctl restart kubelet

# 5. 验证 API Server 健康状态
curl -k https://localhost:6443/healthz
```

#### 场景 2: 所有 API Server 失效
```bash
# 1. 检查负载均衡器状态
systemctl status haproxy

# 2. 检查 API Server 进程
ps aux | grep kube-apiserver

# 3. 重启所有 Master 节点的 kubelet
for master in master1 master2 master3; do
  ssh $master "systemctl restart kubelet"
done

# 4. 等待 API Server 恢复
while ! kubectl get nodes; do
  echo "等待 API Server 恢复..."
  sleep 10
done
```

### 3. 网络故障恢复

#### CNI 网络插件故障
```bash
# 1. 检查 CNI 插件状态
kubectl get pods -n kube-system -l app=flannel

# 2. 重启 CNI 插件
kubectl delete pods -n kube-system -l app=flannel

# 3. 检查网络配置
cat /etc/cni/net.d/*

# 4. 验证 Pod 间通信
kubectl run test1 --image=busybox --rm -it --restart=Never -- ping <pod-ip>
```

### 4. 节点故障恢复

#### Worker 节点失效
```bash
# 1. 标记节点为不可调度
kubectl cordon <node-name>

# 2. 驱逐节点上的 Pod
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# 3. 删除失效节点
kubectl delete node <node-name>

# 4. 在新节点上重新加入集群
kubeadm join <control-plane-endpoint> --token <token> --discovery-token-ca-cert-hash <hash>
```

## 🔄 自动化恢复脚本

### 健康检查和自动恢复脚本
```bash
#!/bin/bash
# Kubernetes 集群健康检查和自动恢复脚本

LOG_FILE="/var/log/k8s-health-check.log"
SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a $LOG_FILE
}

send_alert() {
    local message="$1"
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"🚨 K8s Cluster Alert: $message\"}" \
        $SLACK_WEBHOOK
}

check_api_server() {
    log "检查 API Server 健康状态..."
    if ! kubectl cluster-info &>/dev/null; then
        log "❌ API Server 不可用"
        send_alert "API Server 不可用，尝试重启..."
        
        # 尝试重启 kubelet
        systemctl restart kubelet
        sleep 30
        
        if kubectl cluster-info &>/dev/null; then
            log "✅ API Server 恢复正常"
            send_alert "API Server 已恢复正常"
        else
            log "❌ API Server 重启失败，需要人工干预"
            send_alert "API Server 重启失败，需要人工干预"
        fi
    else
        log "✅ API Server 正常"
    fi
}

check_etcd_cluster() {
    log "检查 etcd 集群健康状态..."
    
    # 检查 etcd 集群健康状态
    if ! kubectl -n kube-system exec -it $(kubectl -n kube-system get pods -l component=etcd -o jsonpath='{.items[0].metadata.name}') -- \
        etcdctl --endpoints=https://127.0.0.1:2379 \
        --cacert=/etc/kubernetes/pki/etcd/ca.crt \
        --cert=/etc/kubernetes/pki/etcd/server.crt \
        --key=/etc/kubernetes/pki/etcd/server.key \
        endpoint health &>/dev/null; then
        
        log "❌ etcd 集群异常"
        send_alert "etcd 集群异常，需要人工检查"
    else
        log "✅ etcd 集群正常"
    fi
}

check_node_status() {
    log "检查节点状态..."
    
    # 获取 NotReady 节点
    NOT_READY_NODES=$(kubectl get nodes --no-headers | awk '$2 != "Ready" {print $1}')
    
    if [[ -n "$NOT_READY_NODES" ]]; then
        log "❌ 发现异常节点: $NOT_READY_NODES"
        send_alert "发现异常节点: $NOT_READY_NODES"
        
        # 尝试重启异常节点的 kubelet
        for node in $NOT_READY_NODES; do
            log "尝试重启节点 $node 的 kubelet..."
            ssh $node "systemctl restart kubelet"
        done
    else
        log "✅ 所有节点状态正常"
    fi
}

check_system_pods() {
    log "检查系统 Pod 状态..."
    
    # 检查 kube-system 命名空间中的 Pod
    FAILED_PODS=$(kubectl get pods -n kube-system --no-headers | awk '$3 != "Running" && $3 != "Completed" {print $1}')
    
    if [[ -n "$FAILED_PODS" ]]; then
        log "❌ 发现异常系统 Pod: $FAILED_PODS"
        send_alert "发现异常系统 Pod: $FAILED_PODS"
        
        # 尝试重启异常 Pod
        for pod in $FAILED_PODS; do
            log "重启 Pod: $pod"
            kubectl delete pod -n kube-system $pod
        done
    else
        log "✅ 所有系统 Pod 状态正常"
    fi
}

check_resource_usage() {
    log "检查资源使用情况..."
    
    # 检查节点资源使用率
    kubectl top nodes | awk 'NR>1 {
        cpu_usage = substr($3, 1, length($3)-1)
        memory_usage = substr($5, 1, length($5)-1)
        
        if (cpu_usage > 80) {
            print "⚠️ 节点 " $1 " CPU 使用率过高: " $3
        }
        if (memory_usage > 90) {
            print "⚠️ 节点 " $1 " 内存使用率过高: " $5
        }
    }' | while read line; do
        log "$line"
        send_alert "$line"
    done
}

# 主检查流程
main() {
    log "🔍 开始 Kubernetes 集群健康检查..."
    
    check_api_server
    check_etcd_cluster
    check_node_status
    check_system_pods
    check_resource_usage
    
    log "✅ 健康检查完成"
}

# 执行主函数
main
```

### 定期备份脚本
```bash
#!/bin/bash
# etcd 自动备份脚本

BACKUP_DIR="/backup/etcd"
RETENTION_DAYS=7
DATE=$(date +%Y%m%d-%H%M%S)

mkdir -p $BACKUP_DIR

# 创建 etcd 快照
ETCDCTL_API=3 etcdctl snapshot save $BACKUP_DIR/etcd-snapshot-$DATE.db \
  --endpoints=https://10.0.1.10:2379,https://10.0.1.11:2379,https://10.0.1.12:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# 验证备份
ETCDCTL_API=3 etcdctl snapshot status $BACKUP_DIR/etcd-snapshot-$DATE.db

# 清理过期备份
find $BACKUP_DIR -name "etcd-snapshot-*.db" -mtime +$RETENTION_DAYS -delete

# 备份到远程存储 (可选)
# aws s3 cp $BACKUP_DIR/etcd-snapshot-$DATE.db s3://k8s-backups/etcd/

echo "✅ etcd 备份完成: etcd-snapshot-$DATE.db"
```

## 📋 故障恢复检查清单

### 🚨 紧急响应清单 (15分钟内)
- [ ] 确认故障范围和影响
- [ ] 通知相关团队
- [ ] 开始日志收集
- [ ] 检查监控告警
- [ ] 评估是否需要回滚

### 🔧 技术恢复清单 (1小时内)
- [ ] 执行诊断脚本
- [ ] 分析日志和事件
- [ ] 确定根本原因
- [ ] 执行恢复操作
- [ ] 验证服务恢复

### 📊 后续跟进清单 (24小时内)
- [ ] 编写故障报告
- [ ] 更新监控规则
- [ ] 改进自动化脚本
- [ ] 团队复盘会议
- [ ] 预防措施实施

通过这套完整的高可用方案，Kubernetes 集群可以实现：
- **99.9%+ 的服务可用性**
- **自动故障检测和恢复**
- **完整的监控和告警体系**
- **标准化的故障处理流程**

这确保了生产环境的稳定性和可靠性。