#!/bin/bash

# Kubernetes 高可用集群部署脚本
# 支持 kubeadm 方式部署 3 Master + N Worker 架构

set -e

# 配置变量
CLUSTER_NAME="k8s-ha-cluster"
POD_SUBNET="10.244.0.0/16"
SERVICE_SUBNET="10.96.0.0/12"
KUBERNETES_VERSION="1.28.0"
CONTAINERD_VERSION="1.7.2"
RUNC_VERSION="1.1.8"
CNI_VERSION="1.3.0"

# 节点信息 (需根据实际环境修改)
MASTER_NODES=(
    "10.0.1.10:master1"
    "10.0.1.11:master2" 
    "10.0.1.12:master3"
)

WORKER_NODES=(
    "10.0.1.20:worker1"
    "10.0.1.21:worker2"
    "10.0.1.22:worker3"
)

# 负载均衡器 VIP
LB_VIP="10.0.1.100"
LB_PORT="6443"

# 颜色输出函数
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查系统要求
check_system() {
    log_step "检查系统要求..."
    
    # 检查操作系统
    if [[ ! -f /etc/os-release ]]; then
        log_error "无法确定操作系统版本"
        exit 1
    fi
    
    source /etc/os-release
    log_info "操作系统: $PRETTY_NAME"
    
    # 检查内核版本
    KERNEL_VERSION=$(uname -r)
    log_info "内核版本: $KERNEL_VERSION"
    
    # 检查内存
    MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
    if [[ $MEMORY_GB -lt 2 ]]; then
        log_error "内存不足，至少需要 2GB"
        exit 1
    fi
    log_info "内存: ${MEMORY_GB}GB"
    
    # 检查 CPU
    CPU_CORES=$(nproc)
    if [[ $CPU_CORES -lt 2 ]]; then
        log_error "CPU 核心数不足，至少需要 2 核"
        exit 1
    fi
    log_info "CPU 核心数: $CPU_CORES"
}

# 配置系统环境
setup_system() {
    log_step "配置系统环境..."
    
    # 禁用 swap
    log_info "禁用 swap..."
    swapoff -a
    sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab
    
    # 加载内核模块
    log_info "加载内核模块..."
    cat <<EOF > /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF
    
    modprobe overlay
    modprobe br_netfilter
    
    # 配置内核参数
    log_info "配置内核参数..."
    cat <<EOF > /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
vm.swappiness                       = 0
vm.panic_on_oom                     = 0
vm.overcommit_memory                = 1
kernel.panic                        = 10
kernel.panic_on_oops                = 1
kernel.keys.root_maxkeys            = 1000000
kernel.keys.root_maxbytes           = 25000000
EOF
    
    sysctl --system
    
    # 配置时间同步
    log_info "配置时间同步..."
    if command -v chronyd &> /dev/null; then
        systemctl enable chronyd
        systemctl start chronyd
    elif command -v ntpd &> /dev/null; then
        systemctl enable ntpd
        systemctl start ntpd
    fi
    
    # 配置防火墙 (如果启用)
    if systemctl is-active --quiet firewalld; then
        log_info "配置防火墙规则..."
        # Master 节点端口
        firewall-cmd --permanent --add-port=6443/tcp  # API Server
        firewall-cmd --permanent --add-port=2379-2380/tcp  # etcd
        firewall-cmd --permanent --add-port=10250/tcp  # kubelet
        firewall-cmd --permanent --add-port=10251/tcp  # kube-scheduler
        firewall-cmd --permanent --add-port=10252/tcp  # kube-controller-manager
        
        # Worker 节点端口
        firewall-cmd --permanent --add-port=10250/tcp  # kubelet
        firewall-cmd --permanent --add-port=30000-32767/tcp  # NodePort
        
        # CNI 端口 (Flannel)
        firewall-cmd --permanent --add-port=8285/udp
        firewall-cmd --permanent --add-port=8472/udp
        
        firewall-cmd --reload
    fi
}

# 安装容器运行时 (containerd)
install_containerd() {
    log_step "安装 containerd..."
    
    # 安装依赖
    if [[ "$ID" == "ubuntu" ]] || [[ "$ID" == "debian" ]]; then
        apt-get update
        apt-get install -y ca-certificates curl gnupg lsb-release
        
        # 添加 Docker 官方 GPG key
        curl -fsSL https://download.docker.com/linux/$ID/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        
        # 添加仓库
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$ID $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
        
        apt-get update
        apt-get install -y containerd.io
        
    elif [[ "$ID" == "centos" ]] || [[ "$ID" == "rhel" ]]; then
        yum install -y yum-utils
        yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        yum install -y containerd.io
    fi
    
    # 配置 containerd
    log_info "配置 containerd..."
    mkdir -p /etc/containerd
    containerd config default > /etc/containerd/config.toml
    
    # 配置 systemd cgroup 驱动
    sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
    
    # 启动 containerd
    systemctl enable containerd
    systemctl start containerd
    
    log_info "containerd 安装完成"
}

# 安装 kubeadm, kubelet, kubectl
install_kubernetes() {
    log_step "安装 Kubernetes 组件..."
    
    if [[ "$ID" == "ubuntu" ]] || [[ "$ID" == "debian" ]]; then
        # 添加 Kubernetes 仓库
        curl -fsSLo /usr/share/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg
        echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" > /etc/apt/sources.list.d/kubernetes.list
        
        apt-get update
        apt-get install -y kubelet=$KUBERNETES_VERSION-00 kubeadm=$KUBERNETES_VERSION-00 kubectl=$KUBERNETES_VERSION-00
        apt-mark hold kubelet kubeadm kubectl
        
    elif [[ "$ID" == "centos" ]] || [[ "$ID" == "rhel" ]]; then
        cat <<EOF > /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://packages.cloud.google.com/yum/repos/kubernetes-el7-x86_64
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://packages.cloud.google.com/yum/doc/yum-key.gpg https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
EOF
        
        yum install -y kubelet-$KUBERNETES_VERSION kubeadm-$KUBERNETES_VERSION kubectl-$KUBERNETES_VERSION
        yum versionlock kubelet kubeadm kubectl
    fi
    
    # 启用 kubelet
    systemctl enable kubelet
    
    log_info "Kubernetes 组件安装完成"
}

# 配置负载均衡器 (HAProxy)
setup_load_balancer() {
    log_step "配置负载均衡器..."
    
    # 安装 HAProxy
    if [[ "$ID" == "ubuntu" ]] || [[ "$ID" == "debian" ]]; then
        apt-get install -y haproxy keepalived
    elif [[ "$ID" == "centos" ]] || [[ "$ID" == "rhel" ]]; then
        yum install -y haproxy keepalived
    fi
    
    # 配置 HAProxy
    log_info "配置 HAProxy..."
    cat <<EOF > /etc/haproxy/haproxy.cfg
global
    daemon
    log stdout local0
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin
    stats timeout 30s
    user haproxy
    group haproxy

defaults
    mode tcp
    log global
    option tcplog
    option dontlognull
    option log-health-checks
    timeout connect 10s
    timeout client 1m
    timeout server 1m
    timeout check 10s
    retries 3

# 统计页面
listen stats
    bind *:8404
    mode http
    stats enable
    stats uri /stats
    stats refresh 30s
    stats admin if TRUE

# Kubernetes API Server
frontend k8s-api-frontend
    bind *:$LB_PORT
    default_backend k8s-api-backend

backend k8s-api-backend
    balance roundrobin
    option tcp-check
EOF

    # 添加 master 节点到 HAProxy 配置
    for node in "${MASTER_NODES[@]}"; do
        IFS=':' read -r ip name <<< "$node"
        echo "    server $name $ip:6443 check inter 2000 rise 2 fall 5" >> /etc/haproxy/haproxy.cfg
    done
    
    # 启动 HAProxy
    systemctl enable haproxy
    systemctl start haproxy
    
    log_info "HAProxy 配置完成"
}

# 初始化第一个 Master 节点
init_first_master() {
    log_step "初始化第一个 Master 节点..."
    
    # 创建 kubeadm 配置文件
    cat <<EOF > /tmp/kubeadm-config.yaml
apiVersion: kubeadm.k8s.io/v1beta3
kind: ClusterConfiguration
kubernetesVersion: v$KUBERNETES_VERSION
clusterName: $CLUSTER_NAME
controlPlaneEndpoint: "$LB_VIP:$LB_PORT"
networking:
  podSubnet: $POD_SUBNET
  serviceSubnet: $SERVICE_SUBNET
apiServer:
  advertiseAddress: $(hostname -I | awk '{print $1}')
  certSANs:
  - $LB_VIP
  - localhost
  - 127.0.0.1
$(for node in "${MASTER_NODES[@]}"; do
    IFS=':' read -r ip name <<< "$node"
    echo "  - $ip"
done)
etcd:
  local:
    dataDir: /var/lib/etcd
---
apiVersion: kubeadm.k8s.io/v1beta3
kind: InitConfiguration
localAPIEndpoint:
  advertiseAddress: $(hostname -I | awk '{print $1}')
  bindPort: 6443
nodeRegistration:
  criSocket: unix:///var/run/containerd/containerd.sock
---
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
cgroupDriver: systemd
EOF
    
    # 初始化集群
    log_info "正在初始化集群..."
    kubeadm init --config=/tmp/kubeadm-config.yaml --upload-certs
    
    # 配置 kubectl
    mkdir -p $HOME/.kube
    cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
    chown $(id -u):$(id -g) $HOME/.kube/config
    
    log_info "第一个 Master 节点初始化完成"
}

# 安装 CNI 网络插件 (Flannel)
install_cni() {
    log_step "安装 CNI 网络插件..."
    
    # 等待 API Server 就绪
    log_info "等待 API Server 就绪..."
    while ! kubectl get nodes &> /dev/null; do
        sleep 5
    done
    
    # 安装 Flannel
    log_info "安装 Flannel CNI..."
    kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml
    
    # 等待 Flannel Pod 就绪
    log_info "等待 Flannel Pod 就绪..."
    kubectl wait --for=condition=Ready pod -l app=flannel -n kube-system --timeout=300s
    
    log_info "CNI 网络插件安装完成"
}

# 添加其他 Master 节点
join_master_nodes() {
    log_step "添加其他 Master 节点..."
    
    # 获取加入命令
    CERT_KEY=$(kubeadm init phase upload-certs --upload-certs | tail -n 1)
    JOIN_COMMAND=$(kubeadm token create --print-join-command)
    MASTER_JOIN_COMMAND="$JOIN_COMMAND --control-plane --certificate-key $CERT_KEY"
    
    log_info "Master 节点加入命令: $MASTER_JOIN_COMMAND"
    
    # 这里需要在其他 master 节点上执行加入命令
    log_warn "请在其他 Master 节点上执行以下命令:"
    echo "$MASTER_JOIN_COMMAND"
}

# 添加 Worker 节点
join_worker_nodes() {
    log_step "添加 Worker 节点..."
    
    # 获取 Worker 节点加入命令
    WORKER_JOIN_COMMAND=$(kubeadm token create --print-join-command)
    
    log_info "Worker 节点加入命令: $WORKER_JOIN_COMMAND"
    
    # 这里需要在 worker 节点上执行加入命令
    log_warn "请在 Worker 节点上执行以下命令:"
    echo "$WORKER_JOIN_COMMAND"
}

# 验证集群状态
verify_cluster() {
    log_step "验证集群状态..."
    
    log_info "节点状态:"
    kubectl get nodes -o wide
    
    log_info "系统 Pod 状态:"
    kubectl get pods -n kube-system
    
    log_info "集群信息:"
    kubectl cluster-info
    
    # 检查集群健康状态
    log_info "集群健康检查:"
    kubectl get cs
    
    log_info "etcd 集群状态:"
    kubectl -n kube-system exec -it $(kubectl -n kube-system get pods -l component=etcd -o jsonpath='{.items[0].metadata.name}') -- etcdctl \
        --endpoints=https://127.0.0.1:2379 \
        --cacert=/etc/kubernetes/pki/etcd/ca.crt \
        --cert=/etc/kubernetes/pki/etcd/server.crt \
        --key=/etc/kubernetes/pki/etcd/server.key \
        endpoint health
}

# 安装常用插件
install_addons() {
    log_step "安装常用插件..."
    
    # 安装 Metrics Server
    log_info "安装 Metrics Server..."
    kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
    
    # 修改 Metrics Server 配置以支持非 TLS 连接
    kubectl patch deployment metrics-server -n kube-system --type='json' -p='[
        {
            "op": "add",
            "path": "/spec/template/spec/containers/0/args/-",
            "value": "--kubelet-insecure-tls"
        }
    ]'
    
    # 安装 Dashboard (可选)
    read -p "是否安装 Kubernetes Dashboard? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "安装 Kubernetes Dashboard..."
        kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml
        
        # 创建 Dashboard 管理员用户
        cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: admin-user
  namespace: kubernetes-dashboard
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: admin-user
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: admin-user
  namespace: kubernetes-dashboard
EOF
        
        log_info "Dashboard 管理员用户已创建"
        log_info "获取 Dashboard 访问令牌:"
        kubectl -n kubernetes-dashboard create token admin-user
    fi
}

# 主函数
main() {
    log_info "开始部署 Kubernetes 高可用集群..."
    log_info "集群名称: $CLUSTER_NAME"
    log_info "Kubernetes 版本: $KUBERNETES_VERSION"
    log_info "负载均衡器 VIP: $LB_VIP:$LB_PORT"
    
    # 检查是否为 root 用户
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要 root 权限运行"
        exit 1
    fi
    
    # 执行部署步骤
    check_system
    setup_system
    install_containerd
    install_kubernetes
    
    # 根据节点类型执行不同操作
    read -p "请选择节点类型: [1] 第一个 Master 节点 [2] 其他 Master 节点 [3] Worker 节点 [4] 负载均衡器: " choice
    
    case $choice in
        1)
            setup_load_balancer  # 如果第一个 master 也作为 LB
            init_first_master
            install_cni
            join_master_nodes
            join_worker_nodes
            verify_cluster
            install_addons
            ;;
        2)
            log_info "请在第一个 Master 节点获取加入命令后手动执行"
            ;;
        3)
            log_info "请在第一个 Master 节点获取加入命令后手动执行"
            ;;
        4)
            setup_load_balancer
            ;;
        *)
            log_error "无效选择"
            exit 1
            ;;
    esac
    
    log_info "Kubernetes 高可用集群部署完成!"
}

# 执行主函数
main "$@"