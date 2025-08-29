#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
高级子域名发现工具 - 避免API限制
仅用于合法授权的安全测试！
"""

import requests
import socket
import threading
import time
import json
import re
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
import ssl
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AdvancedSubdomainFinder:
    def __init__(self, domain, threads=20, timeout=10):
        self.domain = domain
        self.threads = threads
        self.timeout = timeout
        self.found_subdomains = set()
        self.session = requests.Session()
        self.setup_session()
        
    def setup_session(self):
        """设置会话和请求头"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
        self.session.headers.update({
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def get_comprehensive_wordlist(self):
        """获取综合子域名字典"""
        basic_list = [
            # 常用服务
            'www', 'mail', 'email', 'webmail', 'secure', 'docs', 'support', 'help',
            'api', 'app', 'mobile', 'm', 'admin', 'administrator', 'login', 'portal',
            
            # 开发相关
            'dev', 'development', 'test', 'testing', 'stage', 'staging', 'demo',
            'beta', 'alpha', 'preview', 'sandbox', 'lab', 'labs', 'experimental',
            
            # 基础设施
            'ftp', 'sftp', 'ssh', 'vpn', 'proxy', 'gateway', 'firewall', 'router',
            'switch', 'wifi', 'wireless', 'remote', 'access', 'terminal',
            
            # 服务器相关
            'server', 'host', 'node', 'cluster', 'cloud', 'cdn', 'cache', 'static',
            'assets', 'resources', 'files', 'download', 'upload', 'backup',
            
            # 数据库
            'db', 'database', 'mysql', 'postgres', 'mongodb', 'redis', 'elastic',
            'kibana', 'grafana', 'prometheus', 'influx', 'cassandra',
            
            # 监控和日志
            'monitor', 'monitoring', 'status', 'health', 'metrics', 'stats',
            'analytics', 'log', 'logs', 'syslog', 'audit', 'trace',
            
            # CI/CD
            'ci', 'cd', 'build', 'deploy', 'jenkins', 'gitlab', 'github', 'git',
            'svn', 'repo', 'repository', 'code', 'source', 'maven', 'nexus',
            
            # 网络服务
            'ns', 'ns1', 'ns2', 'ns3', 'dns', 'mx', 'mx1', 'mx2', 'pop', 'pop3',
            'imap', 'smtp', 'webdisk', 'cpanel', 'whm', 'plesk',
            
            # 内容管理
            'cms', 'blog', 'news', 'forum', 'wiki', 'kb', 'faq', 'community',
            'social', 'chat', 'message', 'feedback', 'contact', 'about',
            
            # 电商和业务
            'shop', 'store', 'cart', 'checkout', 'payment', 'pay', 'billing',
            'invoice', 'order', 'product', 'catalog', 'inventory',
            
            # 多媒体
            'img', 'image', 'photo', 'gallery', 'video', 'media', 'stream',
            'live', 'broadcast', 'radio', 'tv', 'podcast',
            
            # 地理位置
            'us', 'eu', 'asia', 'cn', 'jp', 'uk', 'de', 'fr', 'au', 'ca',
            'east', 'west', 'north', 'south', 'central',
            
            # 环境标识
            'prod', 'production', 'live', 'staging', 'qa', 'uat', 'sit',
            'internal', 'intranet', 'extranet', 'public', 'private',
            
            # 安全相关
            'ssl', 'tls', 'cert', 'auth', 'oauth', 'sso', 'ldap', 'ad',
            'security', 'firewall', 'ids', 'ips', 'siem', 'waf'
        ]
        
        # 添加数字组合
        numbered_subdomains = []
        for base in ['app', 'api', 'web', 'mail', 'db', 'server']:
            for i in range(1, 11):
                numbered_subdomains.append(f"{base}{i}")
                numbered_subdomains.append(f"{base}-{i}")
        
        return basic_list + numbered_subdomains
    
    def dns_lookup(self, subdomain):
        """DNS解析检查"""
        full_domain = f"{subdomain}.{self.domain}"
        
        try:
            # 获取A记录
            ip_address = socket.gethostbyname(full_domain)
            return {
                'domain': full_domain,
                'ip': ip_address,
                'type': 'A'
            }
        except socket.gaierror:
            return None
        except Exception as e:
            return None
    
    def http_probe(self, subdomain_info):
        """HTTP/HTTPS 探测"""
        if not subdomain_info:
            return None
            
        domain = subdomain_info['domain']
        results = []
        
        # 测试 HTTPS 和 HTTP
        for scheme in ['https', 'http']:
            try:
                url = f"{scheme}://{domain}"
                response = self.session.get(
                    url, 
                    timeout=self.timeout, 
                    verify=False,
                    allow_redirects=True,
                    stream=True
                )
                
                # 只读取前1KB来提取标题
                content = response.raw.read(1024).decode('utf-8', errors='ignore')
                
                result = {
                    'url': url,
                    'status_code': response.status_code,
                    'title': self.extract_title(content),
                    'server': response.headers.get('Server', 'Unknown'),
                    'content_type': response.headers.get('Content-Type', 'Unknown'),
                    'response_time': response.elapsed.total_seconds()
                }
                
                if response.status_code < 400:
                    results.append(result)
                    break  # 如果HTTPS成功，就不测试HTTP了
                    
            except requests.exceptions.RequestException:
                continue
            except Exception as e:
                continue
        
        return results[0] if results else None
    
    def extract_title(self, html_content):
        """提取HTML标题"""
        try:
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
            if title_match:
                title = title_match.group(1).strip()
                # 清理标题
                title = re.sub(r'\s+', ' ', title)
                return title[:100] if len(title) > 100 else title
        except:
            pass
        return "No Title"
    
    def check_subdomain(self, subdomain):
        """检查单个子域名"""
        try:
            # DNS检查
            dns_result = self.dns_lookup(subdomain)
            if dns_result:
                # HTTP检查
                http_result = self.http_probe(dns_result)
                
                result = {
                    'subdomain': subdomain,
                    'domain': dns_result['domain'],
                    'ip': dns_result['ip'],
                    'http_info': http_result
                }
                
                self.found_subdomains.add(dns_result['domain'])
                return result
                
        except Exception as e:
            pass
        
        return None
    
    def certificate_transparency_search(self):
        """通过证书透明度日志搜索子域名"""
        print("🔍 搜索证书透明度日志...")
        
        try:
            url = f"https://crt.sh/?q=%.{self.domain}&output=json"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                certificates = response.json()
                ct_subdomains = set()
                
                for cert in certificates:
                    name_value = cert.get('name_value', '')
                    for domain in name_value.split('\n'):
                        domain = domain.strip()
                        if domain.endswith(f".{self.domain}"):
                            subdomain = domain.replace(f".{self.domain}", "")
                            if subdomain and '*' not in subdomain:
                                ct_subdomains.add(subdomain)
                
                print(f"📋 从CT日志发现 {len(ct_subdomains)} 个潜在子域名")
                return list(ct_subdomains)
                
        except Exception as e:
            print(f"⚠️ CT日志搜索失败: {e}")
        
        return []
    
    def run_bruteforce(self):
        """执行暴力破解"""
        print(f"🎯 开始暴力破解 {self.domain}")
        
        wordlist = self.get_comprehensive_wordlist()
        print(f"📚 使用字典: {len(wordlist)} 个子域名")
        print(f"🧵 线程数: {self.threads}")
        print("=" * 60)
        
        start_time = time.time()
        results = []
        checked = 0
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            future_to_subdomain = {
                executor.submit(self.check_subdomain, subdomain): subdomain 
                for subdomain in wordlist
            }
            
            for future in as_completed(future_to_subdomain):
                subdomain = future_to_subdomain[future]
                checked += 1
                
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        self.print_result(result)
                    
                    # 显示进度
                    if checked % 50 == 0:
                        progress = (checked / len(wordlist)) * 100
                        elapsed = time.time() - start_time
                        rate = checked / elapsed if elapsed > 0 else 0
                        print(f"📊 进度: {progress:.1f}% ({checked}/{len(wordlist)}) - {rate:.1f} req/s")
                        
                except Exception as e:
                    continue
        
        return results
    
    def print_result(self, result):
        """打印发现的子域名"""
        domain = result['domain']
        ip = result['ip']
        http_info = result['http_info']
        
        print(f"✅ {domain}")
        print(f"   📍 IP: {ip}")
        
        if http_info:
            print(f"   🌐 URL: {http_info['url']} [{http_info['status_code']}]")
            print(f"   📄 Title: {http_info['title']}")
            print(f"   ⚡ Response: {http_info['response_time']:.2f}s")
        
        print("-" * 60)
    
    def run(self):
        """完整运行流程"""
        print(f"🚀 高级子域名发现 - {self.domain}")
        print("=" * 60)
        
        all_results = []
        
        # 1. 证书透明度搜索
        ct_subdomains = self.certificate_transparency_search()
        
        # 2. 暴力破解
        bf_results = self.run_bruteforce()
        all_results.extend(bf_results)
        
        # 3. 检查CT日志中的子域名
        if ct_subdomains:
            print(f"\n🔍 验证CT日志中的子域名...")
            ct_verified = []
            
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                future_to_subdomain = {
                    executor.submit(self.check_subdomain, sub): sub 
                    for sub in ct_subdomains[:100]  # 限制数量避免过多请求
                }
                
                for future in as_completed(future_to_subdomain):
                    try:
                        result = future.result()
                        if result and result not in all_results:
                            ct_verified.append(result)
                            self.print_result(result)
                    except:
                        continue
            
            all_results.extend(ct_verified)
        
        # 4. 生成报告
        self.generate_report(all_results)
        
        return all_results
    
    def generate_report(self, results):
        """生成扫描报告"""
        print("\n" + "=" * 60)
        print("📊 扫描报告")
        print("=" * 60)
        
        print(f"🎯 目标域名: {self.domain}")
        print(f"✅ 发现子域名: {len(results)}")
        print(f"🌐 HTTP可访问: {sum(1 for r in results if r['http_info'])}")
        
        if results:
            print("\n📋 子域名列表:")
            for i, result in enumerate(results, 1):
                domain = result['domain']
                ip = result['ip']
                http_status = f"[{result['http_info']['status_code']}]" if result['http_info'] else "[DNS Only]"
                print(f"{i:2d}. {domain} -> {ip} {http_status}")
        
        # 保存到文件
        filename = f"subdomain_scan_{self.domain}_{int(time.time())}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"子域名扫描结果 - {self.domain}\n")
            f.write(f"扫描时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for result in results:
                f.write(f"域名: {result['domain']}\n")
                f.write(f"IP: {result['ip']}\n")
                if result['http_info']:
                    f.write(f"URL: {result['http_info']['url']}\n")
                    f.write(f"状态: {result['http_info']['status_code']}\n")
                    f.write(f"标题: {result['http_info']['title']}\n")
                f.write("-" * 40 + "\n")
        
        print(f"\n💾 详细结果已保存到: {filename}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="高级Python子域名发现工具")
    parser.add_argument("-d", "--domain", required=True, help="目标域名")
    parser.add_argument("-t", "--threads", type=int, default=20, help="线程数 (默认: 20)")
    parser.add_argument("--timeout", type=int, default=10, help="超时时间 (默认: 10秒)")
    
    args = parser.parse_args()
    
    print("⚠️  仅用于合法授权的安全测试！")
    print("=" * 60)
    
    finder = AdvancedSubdomainFinder(
        domain=args.domain,
        threads=args.threads,
        timeout=args.timeout
    )
    
    try:
        results = finder.run()
        print(f"\n🎉 扫描完成！共发现 {len(results)} 个子域名")
    except KeyboardInterrupt:
        print("\n❌ 用户中断扫描")
    except Exception as e:
        print(f"\n❌ 扫描出错: {e}")

if __name__ == "__main__":
    main() 