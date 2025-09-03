#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSH/SFTP 多中转机连接使用示例
"""

from ssh_sftp_proxy import SSHSFTPProxy

# 示例1: 基本密码认证
def example_password_auth():
    """使用密码认证的示例"""
    
    # 中转机配置 (api4, api5, api6, api7)
    proxy_config = {
        'host_prefix': 'api',
        'start_num': 4,
        'end_num': 7,
        'port': 22,
        'username': 'admin',
        'password': 'your_proxy_password',
        'timeout': 30
    }
    
    # 目标机配置
    target_config = {
        'host': '192.168.1.100',
        'port': 22,
        'username': 'root',
        'password': 'your_target_password',
        'timeout': 30
    }
    
    proxy = SSHSFTPProxy(proxy_config, target_config)
    
    try:
        if proxy.connect():
            print("连接成功！")
            
            # 创建SFTP
            sftp = proxy.create_sftp()
            if sftp:
                # 文件操作示例
                proxy.upload_file('/local/file.txt', '/remote/file.txt')
                files = proxy.list_directory('/tmp')
                print(f"目标机/tmp目录文件: {files}")
                
                # 执行命令
                exit_code, stdout, stderr = proxy.execute_command('df -h')
                print(f"磁盘使用情况:\n{stdout}")
        
    finally:
        proxy.close()


# 示例2: 私钥认证
def example_key_auth():
    """使用私钥认证的示例"""
    
    # 中转机配置（使用私钥）
    proxy_config = {
        'host_prefix': 'api',
        'start_num': 4,
        'end_num': 7,
        'port': 22,
        'username': 'ubuntu',
        'private_key_path': '~/.ssh/id_rsa',
        # 'private_key_password': 'key_password',  # 如果私钥有密码
        'timeout': 30
    }
    
    # 目标机配置（使用私钥）
    target_config = {
        'host': 'prod.server.com',
        'port': 2222,  # 非标准SSH端口
        'username': 'deploy',
        'private_key_path': '~/.ssh/deploy_key',
        'timeout': 30
    }
    
    proxy = SSHSFTPProxy(proxy_config, target_config)
    
    try:
        if proxy.connect():
            print("私钥认证连接成功！")
            
            # 执行批量命令
            commands = [
                'uptime',
                'free -h',
                'ps aux | head -5'
            ]
            
            for cmd in commands:
                exit_code, stdout, stderr = proxy.execute_command(cmd)
                print(f"\n命令: {cmd}")
                print(f"输出: {stdout.strip()}")
                if stderr:
                    print(f"错误: {stderr.strip()}")
        
    finally:
        proxy.close()


# 示例3: 文件批量操作
def example_batch_operations():
    """批量文件操作示例"""
    
    proxy_config = {
        'host_prefix': 'api',
        'start_num': 4,
        'end_num': 7,
        'port': 22,
        'username': 'ops',
        'password': 'ops_password'
    }
    
    target_config = {
        'host': '10.0.0.50',
        'username': 'app',
        'password': 'app_password'
    }
    
    proxy = SSHSFTPProxy(proxy_config, target_config)
    
    try:
        if proxy.connect():
            sftp = proxy.create_sftp()
            if sftp:
                # 批量上传文件
                files_to_upload = [
                    ('/local/config.yaml', '/etc/app/config.yaml'),
                    ('/local/script.sh', '/tmp/deploy.sh'),
                    ('/local/data.json', '/var/app/data.json')
                ]
                
                for local, remote in files_to_upload:
                    success = proxy.upload_file(local, remote)
                    print(f"上传 {local} -> {remote}: {'成功' if success else '失败'}")
                
                # 执行部署脚本
                proxy.execute_command('chmod +x /tmp/deploy.sh')
                exit_code, stdout, stderr = proxy.execute_command('/tmp/deploy.sh')
                print(f"部署脚本执行结果: {exit_code}")
                
    finally:
        proxy.close()


if __name__ == "__main__":
    print("选择运行示例:")
    print("1. 密码认证示例")
    print("2. 私钥认证示例") 
    print("3. 批量操作示例")
    
    choice = input("请输入选项 (1-3): ").strip()
    
    if choice == '1':
        example_password_auth()
    elif choice == '2':
        example_key_auth()
    elif choice == '3':
        example_batch_operations()
    else:
        print("无效选项，运行默认示例")
        example_password_auth()