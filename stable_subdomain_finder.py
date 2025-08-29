#!/usr/bin/env python3
"""
稳定的子域名发现工具 - 避免API限制
"""

import requests
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor

class StableSubdomainFinder:
    def __init__(self, domain, threads=10):
        self.domain = domain
        self.threads = threads
        self.found = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_wordlist(self):
        """获取子域名字典"""
        common = [
            'www', 'mail', 'ftp', 'admin', 'test', 'dev', 'staging', 'api',
            'app', 'blog', 'cdn', 'static', 'img', 'assets', 'support',
            'help', 'docs', 'portal', 'secure', 'vpn', 'git', 'jenkins',
            'ci', 'cd', 'monitor', 'status', 'health', 'metrics', 'log',
            'db', 'database', 'mysql', 'redis', 'elastic', 'kibana',
            'grafana', 'prometheus', 'influx', 'backup', 'archive'
        ]
        
        # 添加数字组合
        for base in ['api', 'app', 'web', 'mail', 'server']:
            for i in range(1, 6):
                common.append(f"{base}{i}")
        
        return common
    
    def check_subdomain(self, subdomain):
        """检查子域名"""
        full_domain = f"{subdomain}.{self.domain}"
        
        try:
            # DNS检查
            ip = socket.gethostbyname(full_domain)
            
            # HTTP检查
            result = {'domain': full_domain, 'ip': ip, 'http': None}
            
            for scheme in ['https', 'http']:
                try:
                    url = f"{scheme}://{full_domain}"
                    resp = self.session.get(url, timeout=8, verify=False)
                    if resp.status_code < 400:
                        result['http'] = {
                            'url': url,
                            'status': resp.status_code,
                            'server': resp.headers.get('Server', 'Unknown')
                        }
                        break
                except:
                    continue
            
            self.found.append(result)
            status = f"[{result['http']['status']}]" if result['http'] else "[DNS]"
            print(f"✅ {full_domain} -> {ip} {status}")
            return result
            
        except socket.gaierror:
            return None
        except Exception:
            return None
    
    def certificate_search(self):
        """证书透明度搜索"""
        print("🔍 搜索证书透明度日志...")
        try:
            url = f"https://crt.sh/?q=%.{self.domain}&output=json"
            resp = self.session.get(url, timeout=15)
            
            if resp.status_code == 200:
                certs = resp.json()
                subdomains = set()
                
                for cert in certs[:50]:  # 限制数量
                    names = cert.get('name_value', '').split('\n')
                    for name in names:
                        name = name.strip()
                        if name.endswith(f".{self.domain}") and '*' not in name:
                            sub = name.replace(f".{self.domain}", "")
                            if sub:
                                subdomains.add(sub)
                
                print(f"📋 从证书日志发现 {len(subdomains)} 个子域名")
                return list(subdomains)[:20]  # 限制验证数量
                
        except Exception as e:
            print(f"⚠️ 证书搜索失败: {e}")
        
        return []
    
    def run(self):
        """执行扫描"""
        print(f"🎯 目标: {self.domain}")
        print("=" * 40)
        
        # 获取字典
        wordlist = self.get_wordlist()
        
        # 证书透明度搜索
        ct_subs = self.certificate_search()
        
        # 合并去重
        all_subs = list(set(wordlist + ct_subs))
        print(f"📚 总共测试 {len(all_subs)} 个子域名")
        
        # 多线程检查
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            list(executor.map(self.check_subdomain, all_subs))
        
        # 结果统计
        print(f"\n📊 发现 {len(self.found)} 个子域名:")
        for item in self.found:
            http_info = f" -> {item['http']['url']}" if item['http'] else ""
            print(f"  {item['domain']} ({item['ip']}){http_info}")
        
        # 保存结果
        filename = f"subdomains_{self.domain}.txt"
        with open(filename, 'w') as f:
            for item in self.found:
                f.write(f"{item['domain']}\n")
        print(f"\n💾 结果保存到: {filename}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("用法: python stable_subdomain_finder.py <domain>")
        print("示例: python stable_subdomain_finder.py example.com")
        sys.exit(1)
    
    print("⚠️ 仅用于合法授权的安全测试！")
    
    domain = sys.argv[1]
    finder = StableSubdomainFinder(domain)
    finder.run() 