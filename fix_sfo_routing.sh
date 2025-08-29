#!/bin/bash
# CloudFront SFO路由问题修复脚本

echo "🔧 CloudFront节点优化脚本"
echo "当前节点: SFO53-P2 (旧金山) ❌"
echo "目标节点: HKG*/NRT*/ICN* (亚太地区) ✅"
echo "=" * 50

# 检查AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ 请先安装 AWS CLI"
    echo "下载地址: https://aws.amazon.com/cli/"
    exit 1
fi

# 获取分发ID
echo "请输入您的CloudFront Distribution ID:"
read DISTRIBUTION_ID

if [ -z "$DISTRIBUTION_ID" ]; then
    echo "❌ Distribution ID 不能为空"
    exit 1
fi

echo "🔍 获取当前配置..."

# 获取当前配置
CURRENT_CONFIG=$(aws cloudfront get-distribution --id $DISTRIBUTION_ID --query 'Distribution.DistributionConfig' --output json)

if [ $? -ne 0 ]; then
    echo "❌ 获取分发配置失败，请检查:"
    echo "1. AWS CLI 是否正确配置"
    echo "2. Distribution ID 是否正确"
    echo "3. 是否有足够的权限"
    exit 1
fi

# 获取当前ETag
ETAG=$(aws cloudfront get-distribution --id $DISTRIBUTION_ID --query 'ETag' --output text)

echo "✅ 当前配置获取成功"
echo "📋 当前Price Class: $(echo $CURRENT_CONFIG | jq -r '.PriceClass')"

# 创建新配置
NEW_CONFIG=$(echo $CURRENT_CONFIG | jq '.PriceClass = "PriceClass_All" | .CallerReference = "'$(date +%s)'"')

# 保存配置到临时文件
echo $NEW_CONFIG > /tmp/cloudfront_config.json

echo "🚀 更新配置为 PriceClass_All..."

# 更新分发
UPDATE_RESULT=$(aws cloudfront update-distribution \
    --id $DISTRIBUTION_ID \
    --distribution-config file:///tmp/cloudfront_config.json \
    --if-match $ETAG \
    --output json)

if [ $? -eq 0 ]; then
    echo "✅ 配置更新成功！"
    echo "📊 新的Price Class: PriceClass_All"
    echo "⏱️ 部署时间: 15-20分钟"
    echo "🎯 预期效果:"
    echo "   - 延迟从 200ms 降低到 40ms"
    echo "   - 将路由到香港/东京节点"
    echo "   - 成本增加约 30-50%"
    
    # 清理临时文件
    rm -f /tmp/cloudfront_config.json
    
    echo ""
    echo "📋 后续验证步骤:"
    echo "1. 等待 20 分钟部署完成"
    echo "2. 执行: curl -I https://your-domain.com"
    echo "3. 检查 X-Amz-Cf-Pop 是否变为 HKG*/NRT*/ICN*"
    echo "4. 测试访问速度"
    
else
    echo "❌ 配置更新失败"
    echo "请检查错误信息并重试"
    rm -f /tmp/cloudfront_config.json
    exit 1
fi

echo ""
echo "🌟 优化完成！"
echo "如需进一步优化，建议考虑 AWS 中国区域" 