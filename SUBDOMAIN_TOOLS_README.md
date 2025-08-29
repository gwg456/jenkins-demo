# 🔍 Python 子域名发现工具集

## ⚠️ **重要声明**
**本工具仅用于合法授权的安全测试和渗透测试！**
**未经授权的网络扫描可能违反法律法规！**

## 📋 **工具列表**

### 1. **简单子域名发现器** (`simple_subdomain_finder.py`)
- 轻量级工具
- 内置常用子域名字典
- 支持HTTP/HTTPS检查
- 多线程加速

### 2. **推荐的第三方工具**

## 🛠️ **安装和使用**

### 环境准备
```bash
# 安装依赖
pip install -r requirements_subdomain.txt

# 或者单独安装
pip install requests dnspython urllib3
```

### 使用简单工具
```bash
# 基本用法
python simple_subdomain_finder.py example.com

# 示例输出
🎯 扫描目标: example.com
========================================
✅ 发现: www.example.com [200]
✅ 发现: mail.example.com [200]
✅ 发现: api.example.com [200]

📋 扫描结果:
发现 3 个子域名:
  www.example.com -> https://www.example.com
  mail.example.com -> https://mail.example.com
  api.example.com -> https://api.example.com
```

## 🔧 **进阶工具推荐**

### 1. **Sublist3r** (推荐)
```bash
# 安装
pip install sublist3r

# 基本使用
sublist3r -d example.com

# 高级用法
sublist3r -d example.com -t 100 -v -o results.txt -e google,yahoo,bing

# 参数说明
# -d: 目标域名
# -t: 线程数
# -v: 详细输出
# -o: 输出文件
# -e: 指定搜索引擎
```

### 2. **SubFinder**
```bash
# 安装 (需要Go环境)
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

# 使用
subfinder -d example.com -o results.txt

# 静默模式
subfinder -d example.com -silent
```

### 3. **Amass** (功能最强大)
```bash
# Ubuntu/Debian 安装
sudo apt install amass

# 使用
amass enum -d example.com

# 被动扫描
amass enum -passive -d example.com

# 主动扫描 (更激进)
amass enum -active -d example.com
```

## 📊 **工具对比**

| 工具 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **自制简单工具** | 轻量、可定制 | 功能有限 | 快速测试 |
| **Sublist3r** | 多引擎、易用 | 依赖搜索引擎 | 日常使用 |
| **SubFinder** | 快速、准确 | 需要Go环境 | 自动化脚本 |
| **Amass** | 功能全面、专业 | 资源消耗大 | 深度测试 |

## 🎯 **最佳实践**

### 1. **分层扫描策略**
```bash
# 第一层：快速发现
python simple_subdomain_finder.py target.com

# 第二层：广泛收集  
sublist3r -d target.com -o sublist_results.txt

# 第三层：深度扫描
amass enum -d target.com -o amass_results.txt
```

### 2. **结果去重合并**
```python
# 合并多个工具的结果
def merge_results(files):
    all_subdomains = set()
    for file in files:
        with open(file, 'r') as f:
            for line in f:
                subdomain = line.strip()
                if subdomain:
                    all_subdomains.add(subdomain)
    
    return sorted(all_subdomains)

# 使用示例
results = merge_results(['sublist_results.txt', 'amass_results.txt'])
print(f"总共发现 {len(results)} 个唯一子域名")
```

## 📚 **自定义字典**

创建自己的子域名字典：

```bash
# 创建字典文件 wordlist.txt
echo "www
mail  
ftp
admin
test
dev
staging
api
app
blog
forum
shop
support
docs
wiki
git
jenkins" > wordlist.txt
```

## 🔒 **安全注意事项**

### 1. **合法使用**
- ✅ 仅在授权范围内使用
- ✅ 遵守目标网站的robots.txt
- ✅ 控制扫描频率，避免DDoS
- ❌ 不要扫描未授权的目标

### 2. **技术注意**
- 使用代理池避免IP封禁
- 设置合理的超时时间
- 添加随机延迟
- 使用真实的User-Agent

### 3. **代理配置示例**
```python
import requests

proxies = {
    'http': 'http://proxy:port',
    'https': 'https://proxy:port'
}

response = requests.get(url, proxies=proxies, timeout=10)
```

## 📈 **扩展功能**

### 1. **端口扫描集成**
```python
def scan_ports(domain, ports=[80, 443, 8080, 8443]):
    import socket
    open_ports = []
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((domain, port))
        if result == 0:
            open_ports.append(port)
        sock.close()
    return open_ports
```

### 2. **截图功能**
```python
# 需要安装 selenium 和 webdriver
from selenium import webdriver

def take_screenshot(url, filename):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(url)
        driver.save_screenshot(filename)
    finally:
        driver.quit()
```

## 🚀 **自动化脚本示例**

```bash
#!/bin/bash
# 完整的子域名发现流程

TARGET="$1"
OUTPUT_DIR="results_$TARGET"

if [ -z "$TARGET" ]; then
    echo "用法: $0 <domain>"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

echo "🎯 开始扫描 $TARGET"

# 1. 快速扫描
echo "📍 Step 1: 快速扫描"
python simple_subdomain_finder.py "$TARGET" > "$OUTPUT_DIR/quick_scan.txt"

# 2. Sublist3r 扫描
echo "📍 Step 2: Sublist3r 扫描"  
sublist3r -d "$TARGET" -o "$OUTPUT_DIR/sublist3r.txt"

# 3. 合并去重
echo "📍 Step 3: 合并结果"
cat "$OUTPUT_DIR"/*.txt | sort -u > "$OUTPUT_DIR/final_results.txt"

echo "✅ 扫描完成，结果保存在 $OUTPUT_DIR/"
```

## 📞 **免责声明**

本工具集仅供学习和授权的安全测试使用。使用者需要：

1. 确保获得目标系统的明确授权
2. 遵守当地法律法规
3. 承担使用工具的所有责任
4. 不得用于恶意攻击或非法活动

**请负责任地使用这些工具！** 🛡️ 