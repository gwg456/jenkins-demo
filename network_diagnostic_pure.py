#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
网络诊断工具 - 纯Python库版本
需要安装: pip install ping3 icmplib
"""

import datetime
import platform
import socket
import sys

try:
    from ping3 import ping, verbose_ping
    PING3_AVAILABLE = True
except ImportError:
    PING3_AVAILABLE = False

try:
    from icmplib import ping as icmp_ping, traceroute
    ICMPLIB_AVAILABLE = True
except ImportError:
    ICMPLIB_AVAILABLE = False

class PurePythonNetworkDiagnostic:
    def __init__(self, target_host='2.2.3.2'):
        self.target_host = target_host
        self.system = platform.system()
        self.report_file = f"python_network_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
    def check_dependencies(self):
        """检查依赖库"""
        missing = []
        if not PING3_AVAILABLE:
            missing.append('ping3')
        if not ICMPLIB_AVAILABLE:
            missing.append('icmplib')
        
        if missing:
            print("❌ 缺少依赖库，请安装:")
            print(f"pip install {' '.join(missing)}")
            return False
        return True
    
    def ping3_test(self, count=10):
        """使用 ping3 库进行测试"""
        print("🏓 正在使用 ping3 库测试...")
        
        results = []
        success_count = 0
        total_time = 0
        
        for i in range(count):
            try:
                response_time = ping(self.target_host, timeout=3)
                if response_time is not None:
                    success_count += 1
                    total_time += response_time
                    results.append(f"Reply from {self.target_host}: time={response_time*1000:.1f}ms")
                else:
                    results.append(f"Request timeout for icmp_seq {i+1}")
            except Exception as e:
                results.append(f"Error: {str(e)}")
        
        # 统计
        loss_rate = (count - success_count) / count * 100
        avg_time = (total_time / success_count * 1000) if success_count > 0 else 0
        
        summary = [
            f"--- {self.target_host} ping statistics ---",
            f"{count} packets transmitted, {success_count} received, {loss_rate:.1f}% packet loss",
            f"round-trip min/avg/max = -/{avg_time:.1f}/- ms"
        ]
        
        return {
            'success': success_count > 0,
            'results': results,
            'summary': summary,
            'stats': {
                'sent': count,
                'received': success_count,
                'loss_rate': loss_rate,
                'avg_time': avg_time
            }
        }
    
    def icmplib_ping_test(self, count=10):
        """使用 icmplib 库进行 ping 测试"""
        print("🏓 正在使用 icmplib 库测试...")
        
        try:
            host = icmp_ping(self.target_host, count=count, timeout=3)
            
            results = []
            for i, rtt in enumerate(host.rtts):
                if rtt > 0:
                    results.append(f"Reply from {self.target_host}: icmp_seq={i+1} time={rtt:.1f}ms")
                else:
                    results.append(f"Request timeout for icmp_seq {i+1}")
            
            summary = [
                f"--- {self.target_host} ping statistics ---",
                f"{host.packets_sent} packets transmitted, {host.packets_received} received, "
                f"{host.packet_loss*100:.1f}% packet loss",
                f"round-trip min/avg/max = {host.min_rtt:.1f}/{host.avg_rtt:.1f}/{host.max_rtt:.1f} ms"
            ]
            
            return {
                'success': host.is_alive,
                'results': results,
                'summary': summary,
                'stats': {
                    'sent': host.packets_sent,
                    'received': host.packets_received,
                    'loss_rate': host.packet_loss * 100,
                    'avg_time': host.avg_rtt,
                    'min_time': host.min_rtt,
                    'max_time': host.max_rtt
                }
            }
        except Exception as e:
            return {
                'success': False,
                'results': [f"Ping failed: {str(e)}"],
                'summary': [f"Error: {str(e)}"],
                'stats': {}
            }
    
    def traceroute_test(self):
        """使用 icmplib 进行路由追踪（类似MTR）"""
        print("🚀 正在执行路由追踪测试...")
        
        try:
            hops = traceroute(self.target_host, timeout=3, count=3)
            
            results = [
                "Start: traceroute to " + self.target_host,
                "HOST: " + socket.gethostname().ljust(30) + "Loss%   Snt   Last   Avg  Best  Wrst StDev"
            ]
            
            for hop in hops:
                if hop.avg_rtt > 0:
                    loss = (hop.count - len([r for r in hop.rtts if r > 0])) / hop.count * 100
                    results.append(
                        f"{hop.distance:2d}.|-- {hop.address.ljust(20)} "
                        f"{loss:4.1f}%   {hop.count:3d}   {hop.avg_rtt:6.1f} {hop.avg_rtt:6.1f} "
                        f"{hop.min_rtt:6.1f} {hop.max_rtt:6.1f}   0.0"
                    )
                else:
                    results.append(f"{hop.distance:2d}.|-- {'???'.ljust(20)} 100.0%   {hop.count:3d}      -      -      -      -     -")
            
            return {
                'success': len(hops) > 0,
                'results': results,
                'hops': len(hops)
            }
        except Exception as e:
            return {
                'success': False,
                'results': [f"Traceroute failed: {str(e)}"],
                'hops': 0
            }
    
    def get_system_info(self):
        """获取系统信息"""
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
        except:
            hostname = "Unknown"
            local_ip = "Unknown"
        
        return {
            'hostname': hostname,
            'local_ip': local_ip,
            'system': f"{platform.system()} {platform.release()}",
            'python_version': platform.python_version(),
            'timestamp': datetime.datetime.now().isoformat()
        }
    
    def generate_report(self, ping_result, traceroute_result):
        """生成综合报告"""
        system_info = self.get_system_info()
        
        report_content = []
        report_content.append("=" * 60)
        report_content.append("     网络诊断综合报告 (纯Python库版)")
        report_content.append("=" * 60)
        report_content.append(f"目标主机: {self.target_host}")
        report_content.append(f"测试时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_content.append(f"本机主机名: {system_info['hostname']}")
        report_content.append(f"本机IP: {system_info['local_ip']}")
        report_content.append(f"操作系统: {system_info['system']}")
        report_content.append(f"Python版本: {system_info['python_version']}")
        report_content.append("=" * 60)
        report_content.append("")
        
        # Ping 结果
        report_content.append("🏓 PING 测试结果 (使用Python库):")
        report_content.append("-" * 40)
        if ping_result['success']:
            report_content.extend(ping_result['results'])
            report_content.append("")
            report_content.extend(ping_result['summary'])
        else:
            report_content.append("❌ Ping 测试失败")
            report_content.extend(ping_result['results'])
        report_content.append("")
        
        # Traceroute 结果
        report_content.append("🚀 路由追踪结果 (使用Python库):")
        report_content.append("-" * 40)
        if traceroute_result['success']:
            report_content.extend(traceroute_result['results'])
        else:
            report_content.append("❌ 路由追踪失败")
            report_content.extend(traceroute_result['results'])
        report_content.append("")
        
        report_content.append("📊 使用的Python库:")
        report_content.append("-" * 20)
        report_content.append("- ping3: Ping 测试")
        report_content.append("- icmplib: 路由追踪和高级网络诊断")
        report_content.append("")
        
        report_content.append("=" * 60)
        report_content.append("报告结束")
        report_content.append("=" * 60)
        
        # 保存报告
        with open(self.report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_content))
        
        return '\n'.join(report_content)
    
    def run_diagnostic(self):
        """运行完整的网络诊断"""
        print("🌐 纯Python网络诊断工具")
        print(f"目标主机: {self.target_host}")
        print("=" * 50)
        
        # 检查依赖
        if not self.check_dependencies():
            return None
        
        # 执行测试
        ping_result = self.icmplib_ping_test() if ICMPLIB_AVAILABLE else self.ping3_test()
        traceroute_result = self.traceroute_test() if ICMPLIB_AVAILABLE else {
            'success': False, 
            'results': ['需要 icmplib 库支持路由追踪功能'],
            'hops': 0
        }
        
        # 生成报告
        report = self.generate_report(ping_result, traceroute_result)
        
        # 显示结果
        print("\n📋 诊断结果:")
        print("=" * 50)
        print(report)
        
        print(f"\n✅ 诊断完成!")
        print(f"📄 详细报告已保存到: {self.report_file}")
        
        return {
            'ping': ping_result,
            'traceroute': traceroute_result,
            'report_file': self.report_file
        }

def main():
    """主函数"""
    # 获取目标主机
    target = sys.argv[1] if len(sys.argv) > 1 else '2.2.3.2'
    
    # 创建诊断实例并运行
    diagnostic = PurePythonNetworkDiagnostic(target)
    diagnostic.run_diagnostic()

if __name__ == '__main__':
    main() 