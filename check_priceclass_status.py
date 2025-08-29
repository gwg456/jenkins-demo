#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CloudFront Price Class 检查工具
用于诊断当前分发的Price Class设置
"""

import boto3
import json
from botocore.exceptions import ClientError, NoCredentialsError

class PriceClassChecker:
    def __init__(self):
        try:
            self.cloudfront = boto3.client('cloudfront')
        except NoCredentialsError:
            print("❌ AWS凭证未配置，请先运行: aws configure")
            exit(1)
    
    def check_distribution_priceclass(self, distribution_id):
        """检查指定分发的Price Class"""
        try:
            response = self.cloudfront.get_distribution(Id=distribution_id)
            config = response['Distribution']['DistributionConfig']
            
            price_class = config.get('PriceClass', 'Unknown')
            
            # Price Class 解析
            price_class_info = {
                'PriceClass_100': {
                    'name': 'Use Only US, Canada and Europe',
                    'regions': '🇺🇸🇨🇦🇪🇺 美国、加拿大、欧洲',
                    'china_effect': '❌❌❌ 极慢 (路由到美国)',
                    'cost': '最低',
                    'recommended': False,
                    'reason': '这就是您被路由到SFO的原因！'
                },
                'PriceClass_200': {
                    'name': 'Use US, Canada, Europe, Asia, Middle East and Africa',
                    'regions': '🌍 除南美洲外的所有地区',
                    'china_effect': '⚠️ 一般 (可能路由到新加坡)',
                    'cost': '中等 (+30%)',
                    'recommended': True,
                    'reason': '包含亚太节点，但不是最优'
                },
                'PriceClass_All': {
                    'name': 'Use All Edge Locations (Best Performance)',
                    'regions': '🌎 全球所有边缘节点',
                    'china_effect': '✅ 最佳 (路由到香港/东京)',
                    'cost': '最高 (+50%)',
                    'recommended': True,
                    'reason': '中国大陆访问的最佳选择'
                }
            }
            
            current_info = price_class_info.get(price_class, {
                'name': 'Unknown',
                'regions': '❓ 未知',
                'china_effect': '❓ 需要检查',
                'cost': '未知',
                'recommended': False,
                'reason': '无法识别的Price Class'
            })
            
            return {
                'distribution_id': distribution_id,
                'current_price_class': price_class,
                'info': current_info,
                'all_options': price_class_info
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchDistribution':
                return {'error': f'分发 {distribution_id} 不存在'}
            elif error_code == 'AccessDenied':
                return {'error': '权限不足，请检查IAM权限'}
            else:
                return {'error': f'AWS API错误: {e}'}
    
    def list_all_distributions(self):
        """列出所有CloudFront分发"""
        try:
            response = self.cloudfront.list_distributions()
            distributions = response.get('DistributionList', {}).get('Items', [])
            
            result = []
            for dist in distributions:
                dist_info = {
                    'id': dist['Id'],
                    'domain': dist['DomainName'],
                    'price_class': dist['DistributionConfig']['PriceClass'],
                    'enabled': dist['DistributionConfig']['Enabled'],
                    'status': dist['Status']
                }
                result.append(dist_info)
            
            return result
            
        except ClientError as e:
            return {'error': f'获取分发列表失败: {e}'}
    
    def analyze_sfo_routing(self):
        """分析SFO路由问题"""
        print("🔍 SFO53-P2 路由问题分析")
        print("=" * 50)
        
        print("📍 当前节点: SFO53-P2 (旧金山)")
        print("❌ 问题: 中国大陆用户被路由到美国西海岸")
        print("🎯 根本原因: Price Class 设置限制了亚太节点")
        
        print(f"\n💡 Price Class 对路由的影响:")
        print("PriceClass_100 → 只能使用美国/欧洲节点 → SFO旧金山")
        print("PriceClass_200 → 可以使用亚太节点 → SIN新加坡")
        print("PriceClass_All → 使用最优节点 → HKG香港")
        
        print(f"\n🚀 解决方案:")
        print("1. 立即将Price Class改为 PriceClass_All")
        print("2. 等待15-20分钟部署完成")
        print("3. 验证是否路由到 HKG*/NRT*/ICN* 节点")
        
    def generate_fix_command(self, distribution_id):
        """生成修复命令"""
        return f"""
# AWS CLI 修复命令:
aws cloudfront get-distribution --id {distribution_id} > dist-config.json
# 编辑 dist-config.json，将 PriceClass 改为 "PriceClass_All"
aws cloudfront update-distribution \\
  --id {distribution_id} \\
  --distribution-config file://dist-config.json \\
  --if-match ETAG_VALUE

# 或者使用我们的自动化脚本:
./fix_sfo_routing.sh
"""

def main():
    checker = PriceClassChecker()
    
    print("🔍 CloudFront Price Class 诊断工具")
    print("=" * 50)
    
    # 分析SFO路由问题
    checker.analyze_sfo_routing()
    
    print(f"\n📋 检查您的分发配置:")
    
    # 列出所有分发
    distributions = checker.list_all_distributions()
    
    if isinstance(distributions, dict) and 'error' in distributions:
        print(f"❌ {distributions['error']}")
        print("\n🛠️ 请确保:")
        print("1. AWS CLI 已正确配置 (aws configure)")
        print("2. 账户有CloudFront权限")
        return
    
    if not distributions:
        print("❌ 未找到任何CloudFront分发")
        return
    
    print(f"发现 {len(distributions)} 个分发:")
    print(f"{'ID':<15} {'域名':<30} {'Price Class':<20} {'状态'}")
    print("-" * 80)
    
    for dist in distributions:
        print(f"{dist['id']:<15} {dist['domain']:<30} {dist['price_class']:<20} {dist['status']}")
    
    print(f"\n🔍 详细检查分发 (输入Distribution ID，直接回车跳过):")
    dist_id = input("Distribution ID: ").strip()
    
    if dist_id:
        result = checker.check_distribution_priceclass(dist_id)
        
        if 'error' in result:
            print(f"❌ {result['error']}")
            return
        
        print(f"\n📊 分发 {dist_id} 详细信息:")
        print(f"当前Price Class: {result['current_price_class']}")
        print(f"名称: {result['info']['name']}")
        print(f"包含区域: {result['info']['regions']}")
        print(f"中国访问效果: {result['info']['china_effect']}")
        print(f"成本: {result['info']['cost']}")
        print(f"说明: {result['info']['reason']}")
        
        if not result['info']['recommended']:
            print(f"\n🚨 建议立即优化!")
            print(checker.generate_fix_command(dist_id))

if __name__ == "__main__":
    main() 