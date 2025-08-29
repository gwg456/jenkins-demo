#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单的子域名爆破工具
警告: 仅用于合法授权的安全测试！
"""

import requests
import socket
import threading
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import dns.resolver
from urllib3.packages.urllib3.contrib.socks import _socks_options
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SubdomainBruteforcer:
    def __init__(self, domain, wordlist=None, threads=50, timeout=5):
        self.domain = domain
        self.wordlist = wordlist or self.get_default_wordlist()
        self.threads = threads
        self.timeout = timeout
        self.found_subdomains = set()
        self.total_checked = 0
        
    def get_default_wordlist(self):
        """默认的子域名字典"""
        return [
            'www', 'mail', 'ftp', 'localhost', 'webmail', 'smtp', 'pop', 'ns1', 'webdisk',
            'ns2', 'cpanel', 'whm', 'autodiscover', 'autoconfig', 'test', 'dev', 'staging',
            'beta', 'demo', 'api', 'app', 'admin', 'blog', 'shop', 'forum', 'help', 'support',
            'secure', 'ssl', 'vpn', 'cdn', 'static', 'img', 'image', 'assets', 'js', 'css',
            'media', 'upload', 'download', 'files', 'backup', 'old', 'new', 'mobile', 'm',
            'wap', 'portal', 'news', 'wiki', 'docs', 'doc', 'download', 'git', 'svn',
            'ftp2', 'email', 'imap', 'pop3', 'mx', 'mx1', 'mx2', 'ns', 'ns3', 'dns',
            'search', 'chat', 'video', 'radio', 'tv', 'stream', 'live', 'store', 'payment',
            'pay', 'account', 'accounts', 'user', 'users', 'member', 'members', 'client',
            'clients', 'guest', 'guests', 'internal', 'intranet', 'extranet', 'private',
            'public', 'server', 'host', 'remote', 'vpn2', 'gateway', 'proxy', 'cache',
            'db', 'database', 'mysql', 'oracle', 'mssql', 'postgres', 'mongo', 'redis',
            'elastic', 'kibana', 'grafana', 'monitor', 'status', 'health', 'metrics',
            'stats', 'analytics', 'log', 'logs', 'syslog', 'backup2', 'archive', 'repo',
            'repository', 'code', 'build', 'ci', 'cd', 'jenkins', 'travis', 'github',
            'gitlab', 'bitbucket', 'jira', 'confluence', 'sharepoint', 'teams', 'slack'
        ]
    
    def load_wordlist_from_file(self, filename):
        """从文件加载字典"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"❌ 字典文件 {filename} 不存在")
            return self.get_default_wordlist()
    
    def dns_lookup(self, subdomain):
        """DNS查询方法"""
        full_domain = f"{subdomain}.{self.domain}"
        try:
            # 尝试A记录查询
            result = dns.resolver.resolve(full_domain, 'A')
            ips = [str(ip) for ip in result]
            return full_domain, ips, 'A'
        except dns.resolver.NXDOMAIN:
            return None
        except dns.resolver.NoAnswer:
            try:
                # 尝试CNAME记录查询
                result = dns.resolver.resolve(full_domain, 'CNAME')
                cnames = [str(cname) for cname in result]
                return full_domain, cnames, 'CNAME'
            except:
                return None
        except Exception:
            return None
    
    def http_check(self, subdomain):
        """HTTP检查方法"""
        full_domain = f"{subdomain}.{self.domain}"
        
        for protocol in ['https', 'http']:
            try:
                url = f"{protocol}://{full_domain}"
                response = requests.get(
                    url, 
                    timeout=self.timeout, 
                    verify=False,
                    allow_redirects=True,
                    headers={'User-Agent': 'Mozilla/5.0 (compatible; SubdomainScanner)'}
                )
                
                if response.status_code in [200, 301, 302, 403, 401]:
                    return {
                        'domain': full_domain,
                        'url': url,
                        'status_code': response.status_code,
                        'title': self.extract_title(response.text),
                        'server': response.headers.get('Server', 'Unknown')
                    }
            except requests.exceptions.RequestException:
                continue
        
        return None
    
    def extract_title(self, html):
        """提取HTML标题"""
        try:
            import re
            title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
            if title_match:
                return title_match.group(1).strip()[:100]
        except:
            pass
        return "Unknown"
    
    def check_subdomain(self, subdomain):
        """检查单个子域名"""
        self.total_checked += 1
        
        # DNS查询
        dns_result = self.dns_lookup(subdomain)
        if dns_result:
            domain, records, record_type = dns_result
            
            # HTTP检查
            http_result = self.http_check(subdomain)
            
            result = {
                'domain': domain,
                'dns_records': records,
                'record_type': record_type,
                'http_info': http_result
            }
            
            self.found_subdomains.add(domain)
            return result
        
        return None
    
    def run(self):
        """执行爆破"""
        print(f"🎯 开始对 {self.domain} 进行子域名爆破")
        print(f"📚 字典大小: {len(self.wordlist)}")
        print(f"🧵 线程数: {self.threads}")
        print(f"⏱️  超时时间: {self.timeout}s")
        print("=" * 60)
        
        start_time = time.time()
        results = []
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            # 提交所有任务
            future_to_subdomain = {
                executor.submit(self.check_subdomain, subdomain): subdomain 
                for subdomain in self.wordlist
            }
            
            # 处理结果
            for future in as_completed(future_to_subdomain):
                subdomain = future_to_subdomain[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        self.print_result(result)
                        
                    # 显示进度
                    if self.total_checked % 100 == 0:
                        progress = (self.total_checked / len(self.wordlist)) * 100
                        print(f"📊 进度: {progress:.1f}% ({self.total_checked}/{len(self.wordlist)})")
                        
                except Exception as e:
                    print(f"❌ 检查 {subdomain} 时出错: {e}")
        
        end_time = time.time()
        self.print_summary(results, end_time - start_time)
        return results
    
    def print_result(self, result):
        """打印单个结果"""
        domain = result['domain']
        records = result['dns_records']
        record_type = result['record_type']
        http_info = result['http_info']
        
        print(f"✅ {domain}")
        print(f"   📍 {record_type}: {', '.join(records)}")
        
        if http_info:
            print(f"   🌐 HTTP: {http_info['url']} [{http_info['status_code']}]")
            print(f"   📄 Title: {http_info['title']}")
            print(f"   🖥️  Server: {http_info['server']}")
        
        print("-" * 60)
    
    def print_summary(self, results, elapsed_time):
        """打印总结"""
        print("\n" + "=" * 60)
        print(f"🎉 扫描完成!")
        print(f"⏰ 耗时: {elapsed_time:.2f} 秒")
        print(f"📊 总检查: {self.total_checked}")
        print(f"✅ 发现子域名: {len(results)}")
        print(f"💨 平均速度: {self.total_checked/elapsed_time:.2f} 请求/秒")
        
        if results:
            print("\n📋 发现的子域名列表:")
            for i, result in enumerate(results, 1):
                domain = result['domain']
                http_info = result['http_info']
                status = f" [{http_info['status_code']}]" if http_info else ""
                print(f"{i:2d}. {domain}{status}")
    
    def save_results(self, results, filename):
        """保存结果到文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"子域名扫描结果 - {self.domain}\n")
            f.write(f"扫描时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            
            for result in results:
                domain = result['domain']
                records = result['dns_records']
                record_type = result['record_type']
                http_info = result['http_info']
                
                f.write(f"域名: {domain}\n")
                f.write(f"DNS记录 ({record_type}): {', '.join(records)}\n")
                
                if http_info:
                    f.write(f"HTTP状态: {http_info['status_code']}\n")
                    f.write(f"URL: {http_info['url']}\n")
                    f.write(f"标题: {http_info['title']}\n")
                    f.write(f"服务器: {http_info['server']}\n")
                
                f.write("-" * 40 + "\n")
        
        print(f"💾 结果已保存到: {filename}")

def main():
    parser = argparse.ArgumentParser(description="Python子域名爆破工具")
    parser.add_argument("-d", "--domain", required=True, help="目标域名")
    parser.add_argument("-w", "--wordlist", help="字典文件路径")
    parser.add_argument("-t", "--threads", type=int, default=50, help="线程数 (默认: 50)")
    parser.add_argument("--timeout", type=int, default=5, help="超时时间 (默认: 5秒)")
    parser.add_argument("-o", "--output", help="输出文件名")
    
    args = parser.parse_args()
    
    # 创建爆破器实例
    bruteforcer = SubdomainBruteforcer(
        domain=args.domain,
        threads=args.threads,
        timeout=args.timeout
    )
    
    # 加载字典
    if args.wordlist:
        bruteforcer.wordlist = bruteforcer.load_wordlist_from_file(args.wordlist)
    
    # 执行扫描
    results = bruteforcer.run()
    
    # 保存结果
    if args.output and results:
        bruteforcer.save_results(results, args.output)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 用户中断扫描")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}") 