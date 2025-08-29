#!/usr/bin/env python3
"""
简单子域名发现工具
仅用于合法授权的安全测试！
"""

import requests
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor

class SimpleSubdomainFinder:
    def __init__(self, domain, threads=20):
        self.domain = domain
        self.threads = threads
        self.found = []
        
    def common_subdomains(self):
        """常用子域名列表"""
        return [
            'www', 'mail', 'ftp', 'admin', 'test', 'dev', 'staging', 'api',
            'app', 'blog', 'cdn', 'static', 'img', 'assets', 'support',
            'help', 'docs', 'portal', 'secure', 'vpn', 'git', 'jenkins',
            'ci', 'cd', 'monitor', 'status', 'health', 'metrics', 'log'
        ]
    
    def check_subdomain(self, sub):
        """检查子域名是否存在"""
        full_domain = f"{sub}.{self.domain}"
        
        try:
            # DNS解析检查
            socket.gethostbyname(full_domain)
            
            # HTTP检查
            for protocol in ['https', 'http']:
                try:
                    url = f"{protocol}://{full_domain}"
                    response = requests.get(url, timeout=5, verify=False)
                    if response.status_code < 400:
                        result = {
                            'domain': full_domain,
                            'url': url,
                            'status': response.status_code
                        }
                        self.found.append(result)
                        print(f"✅ 发现: {full_domain} [{response.status_code}]")
                        return result
                except:
                    continue
                    
        except socket.gaierror:
            pass
        except Exception as e:
            pass
        
        return None
    
    def run(self):
        """执行扫描"""
        print(f"🎯 扫描目标: {self.domain}")
        print("=" * 40)
        
        subdomains = self.common_subdomains()
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            executor.map(self.check_subdomain, subdomains)
        
        print("\n📋 扫描结果:")
        print(f"发现 {len(self.found)} 个子域名:")
        for item in self.found:
            print(f"  {item['domain']} -> {item['url']}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("用法: python simple_subdomain_finder.py <domain>")
        print("示例: python simple_subdomain_finder.py example.com")
        sys.exit(1)
    
    domain = sys.argv[1]
    finder = SimpleSubdomainFinder(domain)
    finder.run() 