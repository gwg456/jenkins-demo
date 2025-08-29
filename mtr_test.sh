#!/bin/bash

# MTR 网络诊断脚本
# 作用：测试到 2.2.3.2 的网络连通性和路由追踪

echo "==================================="
echo "🌐 MTR 网络诊断工具"
echo "目标主机: 2.2.3.2"
echo "==================================="

# 检查 mtr 是否安装
if ! command -v mtr &> /dev/null; then
    echo "❌ 错误: mtr 工具未安装"
    echo "请安装 mtr："
    echo "  Ubuntu/Debian: sudo apt-get install mtr-tiny"
    echo "  CentOS/RHEL:   sudo yum install mtr"
    echo "  macOS:         brew install mtr"
    exit 1
fi

# 执行 MTR 测试
echo "🚀 开始执行 MTR 测试..."
echo "生成综合报告中，请稍候..."
echo ""

# 生成报告文件名
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="mtr_comprehensive_report_${TIMESTAMP}.txt"

# 创建综合报告
echo "📊 正在生成 MTR 综合报告..."

# 写入报告头部信息
{
    echo "📋 详细 MTR 报告 (宽格式):"
    echo "----------------------------------------"
} > "${REPORT_FILE}"

# 执行详细的 MTR 测试并追加到报告
mtr -4 -r -c 10 --report-wide 2.2.3.2 >> "${REPORT_FILE}"



# 在控制台显示结果
echo "📋 MTR 测试结果："
echo "=================================="
cat "${REPORT_FILE}"
echo "=================================="

echo ""
echo "✅ MTR 测试完成"
echo "📄 综合报告已保存到: ${REPORT_FILE}" 