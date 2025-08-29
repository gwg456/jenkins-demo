#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CDN节点测试和优化工具
用于测试CloudFront不同节点的访问速度
"""

import requests
import time
import socket
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

class CDNOptimizer:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def test_cdn_speed(self, url, test_count=3):
        """测试CDN节点速度"""
        speeds = []
        
        for i in range(test_count):
            try:
                start_time = time.time()
                response = self.session.get(url, timeout=10, stream=True)
                
                # 下载前1KB数据测试速度
                chunk_size = 1024
                downloaded = 0
                for chunk in response.iter_content(chunk_size=chunk_size):
                    downloaded += len(chunk)
                    if downloaded >= chunk_size:
                        break
                
                end_time = time.time()
                response.close()
                
                if response.status_code == 200:
                    latency = (end_time - start_time) * 1000  # 转换为毫秒
                    speeds.append(latency)
                    print(f"  测试 {i+1}: {latency:.2f}ms")
                else:
                    print(f"  测试 {i+1}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  测试 {i+1}: 失败 - {e}")
                
            time.sleep(1)  # 避免请求过于频繁
        
        if speeds:
            avg_speed = statistics.mean(speeds)
            min_speed = min(speeds)
            max_speed = max(speeds)
            return {
                'avg': avg_speed,
                'min': min_speed,
                'max': max_speed,
                'count': len(speeds)
            }
        return None
    
    def get_cdn_info(self, url):
        """获取CDN节点信息"""
        try:
            response = self.session.head(url, timeout=5)
            
            info = {
                'server': response.headers.get('Server', 'Unknown'),
                'cache_status': response.headers.get('X-Cache', 'Unknown'),
                'pop': response.headers.get('X-Amz-Cf-Pop', 'Unknown'),
                'age': response.headers.get('Age', 'Unknown'),
                'via': response.headers.get('Via', 'Unknown')
            }
            
            return info
        except Exception as e:
            return {'error': str(e)}
    
    def ping_test(self, hostname):
        """Ping测试"""
        try:
            # 解析域名到IP
            ip = socket.gethostbyname(hostname)
            
            # Ping测试 (Windows/Linux兼容)
            import platform
            if platform.system().lower() == "windows":
                cmd = f"ping -n 4 {ip}"
            else:
                cmd = f"ping -c 4 {ip}"
            
            result = subprocess.run(cmd.split(), capture_output=True, text=True)
            
            if result.returncode == 0:
                # 解析ping结果
                output = result.stdout
                if "平均" in output or "avg" in output:
                    # 提取平均延迟
                    import re
                    pattern = r'(\d+\.?\d*)ms'
                    matches = re.findall(pattern, output)
                    if matches:
                        avg_ping = float(matches[-1])  # 通常最后一个是平均值
                        return {'ip': ip, 'avg_ping': avg_ping}
            
            return {'ip': ip, 'avg_ping': None}
            
        except Exception as e:
            return {'error': str(e)}
    
    def test_cloudfront_distribution(self, distribution_url):
        """测试CloudFront分发"""
        hostname = distribution_url.replace('https://', '').replace('http://', '').split('/')[0]
        
        print(f"🔍 测试 CloudFront 分发: {hostname}")
        print("=" * 50)
        
        # 1. Ping测试
        print("📡 Ping测试:")
        ping_result = self.ping_test(hostname)
        if 'error' not in ping_result:
            print(f"  IP地址: {ping_result['ip']}")
            if ping_result['avg_ping']:
                print(f"  平均延迟: {ping_result['avg_ping']}ms")
        else:
            print(f"  Ping失败: {ping_result['error']}")
        
        # 2. CDN信息
        print("\n🌐 CDN节点信息:")
        cdn_info = self.get_cdn_info(distribution_url)
        for key, value in cdn_info.items():
            print(f"  {key}: {value}")
        
        # 3. 速度测试
        print(f"\n⚡ 速度测试:")
        speed_result = self.test_cdn_speed(distribution_url)
        if speed_result:
            print(f"  平均响应: {speed_result['avg']:.2f}ms")
            print(f"  最快响应: {speed_result['min']:.2f}ms")
            print(f"  最慢响应: {speed_result['max']:.2f}ms")
            print(f"  成功测试: {speed_result['count']} 次")
        else:
            print("  速度测试失败")
        
        print("-" * 50)
        
        return {
            'hostname': hostname,
            'ping': ping_result,
            'cdn_info': cdn_info,
            'speed': speed_result
        }
    
    def compare_cdns(self, urls):
        """比较多个CDN性能"""
        print("🚀 CDN性能对比测试")
        print("=" * 60)
        
        results = []
        
        for i, url in enumerate(urls, 1):
            print(f"\n测试 {i}/{len(urls)}: {url}")
            result = self.test_cloudfront_distribution(url)
            results.append(result)
            time.sleep(2)  # 避免请求过快
        
        # 生成对比报告
        self.generate_comparison_report(results)
        
        return results
    
    def generate_comparison_report(self, results):
        """生成对比报告"""
        print("\n" + "=" * 60)
        print("📊 CDN性能对比报告")
        print("=" * 60)
        
        # 排序结果 (按平均速度)
        valid_results = [r for r in results if r.get('speed')]
        valid_results.sort(key=lambda x: x['speed']['avg'])
        
        print(f"{'排名':<4} {'域名':<30} {'节点':<15} {'平均延迟':<10} {'Ping':<10}")
        print("-" * 70)
        
        for i, result in enumerate(valid_results, 1):
            hostname = result['hostname'][:28]
            pop = result['cdn_info'].get('pop', 'Unknown')[:13]
            avg_speed = f"{result['speed']['avg']:.1f}ms"
            ping = f"{result['ping'].get('avg_ping', 'N/A')}"
            if ping != 'N/A':
                ping = f"{float(ping):.1f}ms"
            
            print(f"{i:<4} {hostname:<30} {pop:<15} {avg_speed:<10} {ping:<10}")
        
        # 推荐建议
        if valid_results:
            best = valid_results[0]
            print(f"\n🏆 推荐使用: {best['hostname']}")
            print(f"   节点位置: {best['cdn_info'].get('pop', 'Unknown')}")
            print(f"   平均延迟: {best['speed']['avg']:.1f}ms")
    
    def suggest_optimizations(self, results):
        """建议优化方案"""
        print("\n💡 优化建议:")
        
        # 分析结果
        cn_nodes = []
        us_nodes = []
        
        for result in results:
            pop = result['cdn_info'].get('pop', '').upper()
            if any(x in pop for x in ['HKG', 'NRT', 'ICN', 'SIN']):  # 亚太节点
                cn_nodes.append(result)
            elif any(x in pop for x in ['LAX', 'SFO', 'ORD', 'IAD']):  # 美国节点
                us_nodes.append(result)
        
        if us_nodes and not cn_nodes:
            print("1. 🇨🇳 考虑使用AWS中国区域的CloudFront")
            print("2. 🌏 调整Price Class为PriceClass_All包含更多亚太节点")
            print("3. 🔄 使用混合CDN策略，针对中国用户使用本土CDN")
        
        if cn_nodes:
            best_cn = min(cn_nodes, key=lambda x: x['speed']['avg'])
            print(f"4. ✅ 当前最佳亚太节点: {best_cn['cdn_info'].get('pop', 'Unknown')}")

def main():
    optimizer = CDNOptimizer()
    
    # 示例URLs - 替换为您的CloudFront分发
    test_urls = [
        "https://your-distribution.cloudfront.net",
        # 可以添加多个分发进行对比
    ]
    
    print("⚠️ 请将示例URL替换为您实际的CloudFront分发地址")
    print("示例: python cdn_optimization_script.py")
    
    # 如果需要测试，请取消注释以下行并提供实际URL
    # results = optimizer.compare_cdns(test_urls)
    # optimizer.suggest_optimizations(results)

if __name__ == "__main__":
    main() 