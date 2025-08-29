#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CloudFront 地理路由综合测试工具
专门用于分析中国大陆vs其他地区的路由差异
"""

import requests
import json
import time
import socket
from urllib.parse import urlparse

class CloudFrontRegionalTester:
    def __init__(self, domain):
        self.domain = domain
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
    
    def get_cloudfront_headers(self):
        """获取CloudFront响应头信息"""
        try:
            url = f"https://{self.domain}" if not self.domain.startswith('http') else self.domain
            response = self.session.head(url, timeout=15)
            
            cf_headers = {}
            for header, value in response.headers.items():
                if header.lower().startswith('x-amz-cf') or header.lower() in ['x-cache', 'via', 'server']:
                    cf_headers[header] = value
            
            return {
                'headers': cf_headers,
                'status_code': response.status_code,
                'url': url
            }
        except Exception as e:
            return {'error': str(e)}
    
    def analyze_pop_location(self, pop_code):
        """分析POP节点位置和性能"""
        pop_database = {
            # 亚太地区 - 理想节点
            'HKG': {'country': '🇭🇰 香港', 'region': '亚太', 'china_latency': 'excellent', 'rating': 5},
            'NRT': {'country': '🇯🇵 东京', 'region': '亚太', 'china_latency': 'good', 'rating': 4},
            'ICN': {'country': '🇰🇷 首尔', 'region': '亚太', 'china_latency': 'good', 'rating': 4},
            'SIN': {'country': '🇸🇬 新加坡', 'region': '亚太', 'china_latency': 'fair', 'rating': 3},
            'BOM': {'country': '🇮🇳 孟买', 'region': '亚太', 'china_latency': 'fair', 'rating': 3},
            'SYD': {'country': '🇦🇺 悉尼', 'region': '亚太', 'china_latency': 'poor', 'rating': 2},
            
            # 美国西海岸 - 当前问题节点
            'SFO': {'country': '🇺🇸 旧金山', 'region': '美国西部', 'china_latency': 'poor', 'rating': 2},
            'LAX': {'country': '🇺🇸 洛杉矶', 'region': '美国西部', 'china_latency': 'poor', 'rating': 2},
            'SEA': {'country': '🇺🇸 西雅图', 'region': '美国西部', 'china_latency': 'poor', 'rating': 2},
            'PDX': {'country': '🇺🇸 波特兰', 'region': '美国西部', 'china_latency': 'poor', 'rating': 2},
            
            # 美国中部/东部 - 更差
            'ORD': {'country': '🇺🇸 芝加哥', 'region': '美国中部', 'china_latency': 'very_poor', 'rating': 1},
            'DFW': {'country': '🇺🇸 达拉斯', 'region': '美国中部', 'china_latency': 'very_poor', 'rating': 1},
            'ATL': {'country': '🇺🇸 亚特兰大', 'region': '美国东部', 'china_latency': 'very_poor', 'rating': 1},
            'IAD': {'country': '🇺🇸 弗吉尼亚', 'region': '美国东部', 'china_latency': 'very_poor', 'rating': 1},
            'BOS': {'country': '🇺🇸 波士顿', 'region': '美国东部', 'china_latency': 'very_poor', 'rating': 1},
            'JFK': {'country': '🇺🇸 纽约', 'region': '美国东部', 'china_latency': 'very_poor', 'rating': 1},
            'CMH': {'country': '🇺🇸 俄亥俄', 'region': '美国中部', 'china_latency': 'very_poor', 'rating': 1},
            
            # 欧洲
            'LHR': {'country': '🇬🇧 伦敦', 'region': '欧洲', 'china_latency': 'poor', 'rating': 2},
            'FRA': {'country': '🇩🇪 法兰克福', 'region': '欧洲', 'china_latency': 'poor', 'rating': 2},
            'AMS': {'country': '🇳🇱 阿姆斯特丹', 'region': '欧洲', 'china_latency': 'poor', 'rating': 2},
        }
        
        # 提取POP前缀
        pop_prefix = pop_code[:3] if len(pop_code) >= 3 else pop_code
        
        info = pop_database.get(pop_prefix, {
            'country': f'❓ {pop_code}',
            'region': '未知',
            'china_latency': 'unknown',
            'rating': 0
        })
        
        # 添加延迟和状态信息
        latency_map = {
            'excellent': {'range': '20-40ms', 'status': '✅ 极佳', 'color': 'green'},
            'good': {'range': '50-80ms', 'status': '✅ 良好', 'color': 'green'},
            'fair': {'range': '100-150ms', 'status': '⚠️ 一般', 'color': 'yellow'},
            'poor': {'range': '200-300ms', 'status': '❌ 较差', 'color': 'red'},
            'very_poor': {'range': '300-500ms', 'status': '🚨 极差', 'color': 'red'},
            'unknown': {'range': '未知', 'status': '❓ 未知', 'color': 'gray'}
        }
        
        latency_info = latency_map[info['china_latency']]
        
        return {
            'pop_code': pop_code,
            'location': info['country'],
            'region': info['region'],
            'rating': info['rating'],
            'expected_latency': latency_info['range'],
            'status': latency_info['status'],
            'color': latency_info['color']
        }
    
    def run_comprehensive_analysis(self):
        """运行综合分析"""
        print("🌏 CloudFront 地理路由综合分析")
        print("=" * 60)
        
        print(f"🎯 测试目标: {self.domain}")
        print(f"📅 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 获取当前路由信息
        print(f"\n📍 步骤1: 当前路由分析")
        cf_info = self.get_cloudfront_headers()
        
        if 'error' in cf_info:
            print(f"❌ 获取信息失败: {cf_info['error']}")
            return
        
        headers = cf_info['headers']
        pop_code = headers.get('X-Amz-Cf-Pop', 'Unknown')
        
        print(f"   📊 响应状态: {cf_info['status_code']}")
        print(f"   🌐 测试URL: {cf_info['url']}")
        print(f"   📍 POP节点: {pop_code}")
        
        # 2. 节点详细分析
        print(f"\n🔍 步骤2: 节点详细分析")
        pop_analysis = self.analyze_pop_location(pop_code)
        
        print(f"   📍 节点位置: {pop_analysis['location']}")
        print(f"   🌍 所属区域: {pop_analysis['region']}")
        print(f"   ⭐ 性能评级: {'⭐' * pop_analysis['rating']} ({pop_analysis['rating']}/5)")
        print(f"   ⚡ 预期延迟: {pop_analysis['expected_latency']}")
        print(f"   📊 综合状态: {pop_analysis['status']}")
        
        # 3. 问题诊断
        print(f"\n🩺 步骤3: 路由问题诊断")
        
        if pop_code.startswith(('SFO', 'LAX', 'SEA')):
            print("   🚨 **确认问题**: 中国大陆用户被路由到美国西海岸")
            print("   📋 问题类型: 地理路由策略问题")
            print("   🎯 影响: 延迟增加4-5倍，用户体验差")
            
        elif pop_code.startswith(('ORD', 'CMH', 'ATL', 'IAD')):
            print("   🔥 **严重问题**: 被路由到美国中部/东部")
            print("   📋 问题类型: 极端路由异常")
            print("   🎯 影响: 延迟增加6-8倍，严重影响使用")
            
        elif pop_code.startswith(('HKG', 'NRT', 'ICN')):
            print("   ✅ **路由正常**: 已优化到亚太节点")
            print("   📋 状态: 理想配置")
            print("   🎯 表现: 延迟最优，用户体验佳")
            
        else:
            print(f"   ❓ **需要分析**: 节点 {pop_code} 需要进一步评估")
        
        # 4. CloudFront配置信息
        print(f"\n⚙️ 步骤4: CloudFront配置信息")
        for header, value in headers.items():
            print(f"   {header}: {value}")
        
        # 5. 解决方案建议
        print(f"\n💡 步骤5: 解决方案建议")
        
        if pop_analysis['rating'] <= 2:
            print("   🚨 **立即优化建议**:")
            print("   1. 确认Price Class为 PriceClass_All")
            print("   2. 如无效果，考虑AWS中国区域")
            print("   3. 评估混合CDN架构 (国内CDN + CloudFront)")
            print("   4. 使用智能DNS路由")
            
        elif pop_analysis['rating'] == 3:
            print("   ⚠️ **优化建议**:")
            print("   1. 可考虑进一步优化到香港节点")
            print("   2. 评估AWS中国区域的性价比")
            
        else:
            print("   ✅ **当前配置良好**:")
            print("   1. 路由已优化，无需立即调整")
            print("   2. 可考虑AWS中国区域进一步提升")
        
        # 6. 对比测试建议
        print(f"\n🧪 步骤6: 建议进行的对比测试")
        print("   1. 不同运营商网络测试 (电信/联通/移动)")
        print("   2. VPN测试 (香港/新加坡/日本节点)")
        print("   3. 在线多节点测试 (17ce.com, chinaz.com)")
        print("   4. 不同时段测试 (网络高峰期vs非高峰期)")
        
        return {
            'pop_code': pop_code,
            'pop_analysis': pop_analysis,
            'headers': headers,
            'recommendation': 'optimize' if pop_analysis['rating'] <= 2 else 'good'
        }
    
    def generate_report(self, result):
        """生成测试报告"""
        if not result:
            return
            
        print(f"\n📋 测试报告摘要")
        print("=" * 60)
        print(f"域名: {self.domain}")
        print(f"节点: {result['pop_code']} - {result['pop_analysis']['location']}")
        print(f"评级: {'⭐' * result['pop_analysis']['rating']}/5")
        print(f"状态: {result['pop_analysis']['status']}")
        print(f"建议: {'需要优化' if result['recommendation'] == 'optimize' else '配置良好'}")

def main():
    import sys
    
    if len(sys.argv) != 2:
        print("用法: python cloudfront_regional_test.py <domain>")
        print("示例: python cloudfront_regional_test.py example.com")
        print("     python cloudfront_regional_test.py https://d123456.cloudfront.net")
        sys.exit(1)
    
    domain = sys.argv[1]
    tester = CloudFrontRegionalTester(domain)
    
    try:
        result = tester.run_comprehensive_analysis()
        if result:
            tester.generate_report(result)
    except KeyboardInterrupt:
        print("\n\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")

if __name__ == "__main__":
    main() 