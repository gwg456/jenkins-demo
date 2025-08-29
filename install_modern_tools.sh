#!/bin/bash
# 现代子域名发现工具安装脚本

echo "🛠️ 安装现代子域名发现工具"

# 1. 安装 subfinder (推荐)
echo "📦 安装 Subfinder..."
if command -v go &> /dev/null; then
    go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
    echo "✅ Subfinder 安装完成"
else
    echo "❌ 需要先安装 Go 语言环境"
fi

# 2. 安装 amass
echo "📦 安装 Amass..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Ubuntu/Debian
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y amass
    fi
    # CentOS/RHEL
    if command -v yum &> /dev/null; then
        sudo yum install -y amass
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if command -v brew &> /dev/null; then
        brew install amass
    fi
fi

# 3. 安装 assetfinder
echo "📦 安装 Assetfinder..."
if command -v go &> /dev/null; then
    go install github.com/tomnomnom/assetfinder@latest
    echo "✅ Assetfinder 安装完成"
fi

# 4. 安装 Python 工具
echo "📦 安装 Python 工具..."
pip3 install requests dnspython

echo "🎉 安装完成！"
echo ""
echo "使用示例:"
echo "subfinder -d example.com -o results.txt"
echo "amass enum -d example.com"
echo "assetfinder example.com"
echo "python3 stable_subdomain_finder.py example.com" 