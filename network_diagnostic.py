#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
网络诊断工具 - Python版本
支持 Ping 和 MTR 功能
"""

import subprocess
import datetime
import platform
import socket
import time
import json
import os

class NetworkDiagnostic:
    def __init__(self, target_host='2.2.3.2'):
        self.target_host = target_host
        self.system = platform.system()
        self.report_file = f"network_diagnostic_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
    def ping_test(self, count=10):
        """执行 Ping 测试"""
        print("🏓 正在执行 Ping 测试...")
        
        if self.system == 'Windows':
            cmd = ['ping', '-n', str(count), self.target_host]
        else:
            cmd = ['ping', '-c', str(count), self.target_host]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.stderr else None
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'error': 'Ping 测试超时'
            }
    
    def mtr_test(self, count=10):
        """执行 MTR 测试"""
        print("🚀 正在执行 MTR 测试...")
        
        # 检查 mtr 是否可用
        if not self._check_mtr_available():
            return {
                'success': False,
                'output': '',
                'error': 'MTR 工具未安装'
            }
        
        cmd = ['mtr', '-4', '-r', '-c', str(count), '--report-wide', self.target_host]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.stderr else None
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'error': 'MTR 测试超时'
            }
    
    def _check_mtr_available(self):
        """检查 MTR 是否可用"""
        try:
            subprocess.run(['mtr', '--version'], capture_output=True, timeout=5)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
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
    
    def generate_report(self, ping_result, mtr_result):
        """生成综合报告"""
        system_info = self.get_system_info()
        
        report_content = []
        report_content.append("=" * 60)
        report_content.append("        网络诊断综合报告 (Python版)")
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
        report_content.append("🏓 PING 测试结果:")
        report_content.append("-" * 40)
        if ping_result['success']:
            report_content.append(ping_result['output'])
        else:
            report_content.append(f"❌ Ping 失败: {ping_result['error']}")
        report_content.append("")
        
        # MTR 结果
        report_content.append("🚀 MTR 测试结果:")
        report_content.append("-" * 40)
        if mtr_result['success']:
            report_content.append(mtr_result['output'])
        else:
            report_content.append(f"❌ MTR 失败: {mtr_result['error']}")
            report_content.append("建议安装 MTR: ")
            if self.system == 'Windows':
                report_content.append("  - 下载 WinMTR: https://sourceforge.net/projects/winmtr/")
                report_content.append("  - 或使用: choco install winmtr")
            else:
                report_content.append("  - Ubuntu/Debian: sudo apt-get install mtr-tiny")
                report_content.append("  - CentOS/RHEL: sudo yum install mtr")
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
        print("🌐 网络诊断工具 - Python版")
        print(f"目标主机: {self.target_host}")
        print("=" * 50)
        
        # 执行测试
        ping_result = self.ping_test()
        mtr_result = self.mtr_test()
        
        # 生成报告
        report = self.generate_report(ping_result, mtr_result)
        
        # 显示结果
        print("\n📋 诊断结果:")
        print("=" * 50)
        print(report)
        
        print(f"\n✅ 诊断完成!")
        print(f"📄 详细报告已保存到: {self.report_file}")
        
        return {
            'ping': ping_result,
            'mtr': mtr_result,
            'report_file': self.report_file
        }

def main():
    """主函数"""
    import sys
    
    # 获取目标主机
    target = sys.argv[1] if len(sys.argv) > 1 else '2.2.3.2'
    
    # 创建诊断实例并运行
    diagnostic = NetworkDiagnostic(target)
    diagnostic.run_diagnostic()

if __name__ == '__main__':
    main() 