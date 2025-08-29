#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CloudFront路由测试脚本
专门用于验证SFO路由问题的修复效果
"""

import requests
import time
import statistics

class CloudFrontTester:
    def __init__(self, domain):
        self.domain = domain
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
    
    def get_cloudfront_info(self):
        """获取CloudFront节点信息"""
        try:
            response = self.session.head(f"https://{self.domain}", timeout=10)
            
            info = {
                'pop': response.headers.get('X-Amz-Cf-Pop', 'Unknown'),
                'cache_status': response.headers.get('X-Cache', 'Unknown'),
                'age': response.headers.get('Age', 'Unknown'),
                'server': response.headers.get('Server', 'Unknown'),
                'via': response.headers.get('Via', 'Unknown'),
                'status_code': response.status_code
            }
            
            return info
        except Exception as e:
            return {'error': str(e)}
    
    def test_latency(self, count=5):
        """测试延迟"""
        latencies = []
        
        print(f"🔍 测试 {self.domain} 的延迟...")
        
        for i in range(count):
            try:
                start_time = time.time()
                response = self.session.head(f"https://{self.domain}", timeout=10)
                end_time = time.time()
                
                if response.status_code < 400:
                    latency = (end_time - start_time) * 1000  # 转换为毫秒
                    latencies.append(latency)
                    print(f"  测试 {i+1}: {latency:.1f}ms")
                else:
                    print(f"  测试 {i+1}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  测试 {i+1}: 失败 - {e}")
            
            time.sleep(1)
        
        if latencies:
            return {
                'avg': statistics.mean(latencies),
                'min': min(latencies),
                'max': max(latencies),
                'count': len(latencies)
            }
        return None
    
    def analyze_pop(self, pop_code):
        """分析POP节点"""
        pop_analysis = {
            # 亚太地区 - 理想节点
            'HKG': {'location': '🇭🇰 香港', 'rating': '⭐⭐⭐⭐⭐', 'status': '✅ 优秀'},
            'NRT': {'location': '🇯🇵 东京', 'rating': '⭐⭐⭐⭐', 'status': '✅ 良好'},
            'ICN': {'location': '🇰🇷 首尔', 'rating': '⭐⭐⭐⭐', 'status': '✅ 良好'},
            'SIN': {'location': '🇸🇬 新加坡', 'rating': '⭐⭐⭐', 'status': '⚠️ 一般'},
            
            # 美国西海岸 - 当前问题节点
            'SFO': {'location': '🇺🇸 旧金山', 'rating': '⭐⭐', 'status': '❌ 较慢'},
            'LAX': {'location': '🇺🇸 洛杉矶', 'rating': '⭐⭐', 'status': '❌ 较慢'},
            'SEA': {'location': '🇺🇸 西雅图', 'rating': '⭐⭐', 'status': '❌ 较慢'},
            
            # 美国其他地区 - 更慢
            'ORD': {'location': '🇺🇸 芝加哥', 'rating': '⭐', 'status': '❌ 很慢'},
            'IAD': {'location': '🇺🇸 弗吉尼亚', 'rating': '⭐', 'status': '❌ 很慢'},
        }
        
        # 提取POP前缀 (如 SFO53-P2 -> SFO)
        pop_prefix = pop_code[:3] if len(pop_code) >= 3 else pop_code
        
        return pop_analysis.get(pop_prefix, {
            'location': f'🌍 {pop_code}', 
            'rating': '❓ 未知', 
            'status': '❓ 需要分析'
        })
    
    def run_comprehensive_test(self):
        """运行综合测试"""
        print("🚀 CloudFront 路由综合测试")
        print("=" * 50)
        
        # 1. 获取节点信息
        print("📍 步骤1: 获取节点信息")
        cf_info = self.get_cloudfront_info()
        
        if 'error' in cf_info:
            print(f"❌ 获取信息失败: {cf_info['error']}")
            return
        
        pop_code = cf_info['pop']
        pop_analysis = self.analyze_pop(pop_code)
        
        print(f"   节点代码: {pop_code}")
        print(f"   节点位置: {pop_analysis['location']}")
        print(f"   速度评级: {pop_analysis['rating']}")
        print(f"   状态: {pop_analysis['status']}")
        
        # 2. 延迟测试
        print(f"\n⚡ 步骤2: 延迟测试")
        latency_result = self.test_latency()
        
        if latency_result:
            avg_latency = latency_result['avg']
            print(f"   平均延迟: {avg_latency:.1f}ms")
            print(f"   最快延迟: {latency_result['min']:.1f}ms")
            print(f"   最慢延迟: {latency_result['max']:.1f}ms")
            
            # 性能评估
            if avg_latency < 50:
                performance = "🚀 优秀"
            elif avg_latency < 100:
                performance = "✅ 良好"
            elif avg_latency < 200:
                performance = "⚠️ 一般"
            else:
                performance = "❌ 较差"
            
            print(f"   性能评估: {performance}")
        
        # 3. 优化建议
        print(f"\n💡 步骤3: 优化建议")
        
        if pop_code.startswith('SFO') or pop_code.startswith('LAX') or pop_code.startswith('SEA'):
            print("   ❌ 当前路由到美国西海岸，建议优化：")
            print("   1. 修改 Price Class 为 'Use All Edge Locations'")
            print("   2. 等待 15-20 分钟部署完成")
            print("   3. 预期路由到香港(HKG)或东京(NRT)节点")
            print("   4. 延迟预计从 200ms 降低到 40ms")
            
        elif pop_code.startswith('HKG') or pop_code.startswith('NRT') or pop_code.startswith('ICN'):
            print("   ✅ 当前路由正常，已优化到亚太节点")
            print("   如需进一步提升，建议考虑 AWS 中国区域")
            
        else:
            print(f"   ❓ 当前节点 {pop_code} 需要进一步分析")
        
        # 4. 其他信息
        print(f"\n📊 步骤4: 其他信息")
        print(f"   缓存状态: {cf_info['cache_status']}")
        print(f"   缓存年龄: {cf_info['age']}秒")
        print(f"   服务器: {cf_info['server']}")
        
        return {
            'pop_code': pop_code,
            'pop_analysis': pop_analysis,
            'latency': latency_result,
            'cf_info': cf_info
        }

def main():
    import sys
    
    if len(sys.argv) != 2:
        print("用法: python test_cloudfront_routing.py <domain>")
        print("示例: python test_cloudfront_routing.py example.com")
        sys.exit(1)
    
    domain = sys.argv[1]
    tester = CloudFrontTester(domain)
    result = tester.run_comprehensive_test()
    
    if result:
        print(f"\n🎯 测试完成")
        print(f"建议: 如果看到SFO/LAX节点，请执行优化脚本")

if __name__ == "__main__":
    main() 