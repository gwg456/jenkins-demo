#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSH/SFTP 多中转机连接脚本
通过api4-api7中转机循环尝试连接目标机
Python 3.8+
"""

import paramiko
import socket
import time
import logging
from typing import Optional, Tuple, List

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SSHSFTPProxy:
    def __init__(self, proxy_config: dict, target_config: dict):
        """
        初始化SSH/SFTP代理连接器
        
        Args:
            proxy_config: 中转机配置
            target_config: 目标机配置
        """
        self.proxy_config = proxy_config
        self.target_config = target_config
        self.ssh_proxy = None
        self.ssh_target = None
        self.sftp_client = None
        
    def _get_proxy_hosts(self) -> List[str]:
        """
        生成中转机主机列表 (api4, api5, api6, api7)
        
        Returns:
            List[str]: 中转机主机名列表
        """
        prefix = self.proxy_config.get('host_prefix', 'api')
        start_num = self.proxy_config.get('start_num', 4)
        end_num = self.proxy_config.get('end_num', 7)
        
        return [f"{prefix}{i}" for i in range(start_num, end_num + 1)]
    
    def _create_ssh_client(self) -> paramiko.SSHClient:
        """
        创建SSH客户端
        
        Returns:
            paramiko.SSHClient: 配置好的SSH客户端
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddHostKey())
        return client
    
    def _connect_proxy(self, proxy_host: str) -> Tuple[bool, Optional[paramiko.SSHClient]]:
        """
        连接中转机
        
        Args:
            proxy_host: 中转机主机名
            
        Returns:
            Tuple[bool, Optional[paramiko.SSHClient]]: (连接成功标志, SSH客户端)
        """
        try:
            ssh_client = self._create_ssh_client()
            
            # 连接配置
            connect_kwargs = {
                'hostname': proxy_host,
                'port': self.proxy_config.get('port', 22),
                'username': self.proxy_config['username'],
                'timeout': self.proxy_config.get('timeout', 30),
                'banner_timeout': 30,
                'auth_timeout': 30
            }
            
            # 认证方式：密钥或密码
            if 'private_key_path' in self.proxy_config:
                try:
                    private_key = paramiko.RSAKey.from_private_key_file(
                        self.proxy_config['private_key_path'],
                        password=self.proxy_config.get('private_key_password')
                    )
                    connect_kwargs['pkey'] = private_key
                except Exception as e:
                    logger.warning(f"加载私钥失败，尝试密码认证: {e}")
                    if 'password' in self.proxy_config:
                        connect_kwargs['password'] = self.proxy_config['password']
            elif 'password' in self.proxy_config:
                connect_kwargs['password'] = self.proxy_config['password']
            else:
                raise ValueError("必须提供密码或私钥路径")
            
            logger.info(f"正在连接中转机: {proxy_host}:{connect_kwargs['port']}")
            ssh_client.connect(**connect_kwargs)
            
            logger.info(f"成功连接中转机: {proxy_host}")
            return True, ssh_client
            
        except Exception as e:
            logger.error(f"连接中转机 {proxy_host} 失败: {e}")
            try:
                ssh_client.close()
            except:
                pass
            return False, None
    
    def _connect_target_via_proxy(self, ssh_proxy: paramiko.SSHClient) -> Tuple[bool, Optional[paramiko.SSHClient]]:
        """
        通过中转机连接目标机
        
        Args:
            ssh_proxy: 已连接的中转机SSH客户端
            
        Returns:
            Tuple[bool, Optional[paramiko.SSHClient]]: (连接成功标志, 目标机SSH客户端)
        """
        try:
            # 创建通道到目标机
            transport = ssh_proxy.get_transport()
            dest_addr = (self.target_config['host'], self.target_config.get('port', 22))
            local_addr = ('127.0.0.1', 0)  # 本地地址，端口自动分配
            
            logger.info(f"创建SSH隧道到目标机: {dest_addr[0]}:{dest_addr[1]}")
            channel = transport.open_channel("direct-tcpip", dest_addr, local_addr)
            
            # 通过隧道连接目标机
            ssh_target = self._create_ssh_client()
            
            connect_kwargs = {
                'username': self.target_config['username'],
                'timeout': self.target_config.get('timeout', 30),
                'sock': channel,
                'banner_timeout': 30,
                'auth_timeout': 30
            }
            
            # 目标机认证
            if 'private_key_path' in self.target_config:
                try:
                    private_key = paramiko.RSAKey.from_private_key_file(
                        self.target_config['private_key_path'],
                        password=self.target_config.get('private_key_password')
                    )
                    connect_kwargs['pkey'] = private_key
                except Exception as e:
                    logger.warning(f"加载目标机私钥失败，尝试密码认证: {e}")
                    if 'password' in self.target_config:
                        connect_kwargs['password'] = self.target_config['password']
            elif 'password' in self.target_config:
                connect_kwargs['password'] = self.target_config['password']
            else:
                raise ValueError("目标机必须提供密码或私钥路径")
            
            ssh_target.connect(**connect_kwargs)
            
            logger.info(f"成功通过中转机连接到目标机: {self.target_config['host']}")
            return True, ssh_target
            
        except Exception as e:
            logger.error(f"连接目标机失败: {e}")
            try:
                ssh_target.close()
            except:
                pass
            return False, None
    
    def connect(self) -> bool:
        """
        循环尝试通过中转机连接目标机
        
        Returns:
            bool: 连接成功标志
        """
        proxy_hosts = self._get_proxy_hosts()
        logger.info(f"开始尝试连接中转机列表: {proxy_hosts}")
        
        for proxy_host in proxy_hosts:
            try:
                # 连接中转机
                success, ssh_proxy = self._connect_proxy(proxy_host)
                if not success:
                    continue
                
                self.ssh_proxy = ssh_proxy
                
                # 通过中转机连接目标机
                success, ssh_target = self._connect_target_via_proxy(ssh_proxy)
                if success:
                    self.ssh_target = ssh_target
                    logger.info(f"成功建立完整连接链路: 本机 -> {proxy_host} -> {self.target_config['host']}")
                    return True
                else:
                    # 目标机连接失败，关闭中转机连接，尝试下一台中转机
                    ssh_proxy.close()
                    self.ssh_proxy = None
                    
            except Exception as e:
                logger.error(f"连接过程异常: {e}")
                continue
        
        logger.error("所有中转机连接尝试均失败")
        return False
    
    def create_sftp(self) -> Optional[paramiko.SFTPClient]:
        """
        创建SFTP客户端
        
        Returns:
            Optional[paramiko.SFTPClient]: SFTP客户端或None
        """
        if not self.ssh_target:
            logger.error("目标机SSH连接未建立，无法创建SFTP")
            return None
        
        try:
            self.sftp_client = self.ssh_target.open_sftp()
            logger.info("SFTP客户端创建成功")
            return self.sftp_client
        except Exception as e:
            logger.error(f"创建SFTP客户端失败: {e}")
            return None
    
    def execute_command(self, command: str) -> Tuple[int, str, str]:
        """
        在目标机执行命令
        
        Args:
            command: 要执行的命令
            
        Returns:
            Tuple[int, str, str]: (退出码, 标准输出, 标准错误)
        """
        if not self.ssh_target:
            logger.error("目标机SSH连接未建立")
            return -1, "", "SSH连接未建立"
        
        try:
            stdin, stdout, stderr = self.ssh_target.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            stdout_data = stdout.read().decode('utf-8')
            stderr_data = stderr.read().decode('utf-8')
            
            logger.info(f"命令执行完成: {command} (退出码: {exit_code})")
            return exit_code, stdout_data, stderr_data
            
        except Exception as e:
            logger.error(f"执行命令失败: {e}")
            return -1, "", str(e)
    
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        上传文件到目标机
        
        Args:
            local_path: 本地文件路径
            remote_path: 远程文件路径
            
        Returns:
            bool: 上传成功标志
        """
        if not self.sftp_client:
            logger.error("SFTP客户端未创建")
            return False
        
        try:
            self.sftp_client.put(local_path, remote_path)
            logger.info(f"文件上传成功: {local_path} -> {remote_path}")
            return True
        except Exception as e:
            logger.error(f"文件上传失败: {e}")
            return False
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        从目标机下载文件
        
        Args:
            remote_path: 远程文件路径
            local_path: 本地文件路径
            
        Returns:
            bool: 下载成功标志
        """
        if not self.sftp_client:
            logger.error("SFTP客户端未创建")
            return False
        
        try:
            self.sftp_client.get(remote_path, local_path)
            logger.info(f"文件下载成功: {remote_path} -> {local_path}")
            return True
        except Exception as e:
            logger.error(f"文件下载失败: {e}")
            return False
    
    def list_directory(self, remote_path: str = '.') -> Optional[List[str]]:
        """
        列出目标机目录内容
        
        Args:
            remote_path: 远程目录路径
            
        Returns:
            Optional[List[str]]: 文件列表或None
        """
        if not self.sftp_client:
            logger.error("SFTP客户端未创建")
            return None
        
        try:
            files = self.sftp_client.listdir(remote_path)
            logger.info(f"目录列表获取成功: {remote_path}")
            return files
        except Exception as e:
            logger.error(f"获取目录列表失败: {e}")
            return None
    
    def close(self):
        """
        关闭所有连接
        """
        try:
            if self.sftp_client:
                self.sftp_client.close()
                logger.info("SFTP连接已关闭")
            
            if self.ssh_target:
                self.ssh_target.close()
                logger.info("目标机SSH连接已关闭")
            
            if self.ssh_proxy:
                self.ssh_proxy.close()
                logger.info("中转机SSH连接已关闭")
                
        except Exception as e:
            logger.warning(f"关闭连接时出现异常: {e}")


def main():
    """
    主函数 - 演示用法
    """
    # 中转机配置
    proxy_config = {
        'host_prefix': 'api',  # 中转机主机名前缀
        'start_num': 4,        # 开始数字
        'end_num': 7,          # 结束数字
        'port': 22,            # SSH端口
        'username': 'your_proxy_username',  # 中转机用户名
        'password': 'your_proxy_password',  # 中转机密码（或使用私钥）
        # 'private_key_path': '/path/to/private/key',  # 私钥路径（可选）
        # 'private_key_password': 'key_password',      # 私钥密码（可选）
        'timeout': 30          # 连接超时时间
    }
    
    # 目标机配置
    target_config = {
        'host': 'target.server.com',           # 目标机主机名或IP
        'port': 22,                            # 目标机SSH端口
        'username': 'your_target_username',    # 目标机用户名
        'password': 'your_target_password',    # 目标机密码（或使用私钥）
        # 'private_key_path': '/path/to/target/key',   # 目标机私钥路径（可选）
        # 'private_key_password': 'target_key_password', # 目标机私钥密码（可选）
        'timeout': 30                          # 连接超时时间
    }
    
    # 创建连接器
    proxy = SSHSFTPProxy(proxy_config, target_config)
    
    try:
        # 尝试连接
        if proxy.connect():
            logger.info("SSH连接建立成功")
            
            # 创建SFTP客户端
            sftp = proxy.create_sftp()
            if sftp:
                logger.info("SFTP客户端创建成功")
                
                # 示例操作
                print("\n=== 连接成功，可以进行以下操作 ===")
                
                # 1. 列出目标机当前目录
                files = proxy.list_directory('.')
                if files:
                    print(f"目标机当前目录文件列表: {files[:10]}...")  # 只显示前10个
                
                # 2. 执行简单命令
                exit_code, stdout, stderr = proxy.execute_command('pwd && whoami')
                print(f"命令执行结果:")
                print(f"  当前路径和用户: {stdout.strip()}")
                
                # 3. 示例文件操作（取消注释以启用）
                # proxy.upload_file('/local/path/file.txt', '/remote/path/file.txt')
                # proxy.download_file('/remote/path/file.txt', '/local/download/file.txt')
                
                print("\n=== 连接测试完成 ===")
            else:
                logger.error("SFTP客户端创建失败")
        else:
            logger.error("无法建立SSH连接")
            
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"程序执行异常: {e}")
    finally:
        # 清理连接
        proxy.close()


class InteractiveSSHSFTP:
    """
    交互式SSH/SFTP工具类
    """
    
    @staticmethod
    def prompt_config():
        """
        交互式配置生成器
        """
        print("=== SSH/SFTP 多中转机连接配置 ===\n")
        
        # 中转机配置
        print("中转机配置:")
        proxy_prefix = input("中转机主机名前缀 (默认: api): ").strip() or 'api'
        proxy_start = int(input("起始数字 (默认: 4): ").strip() or '4')
        proxy_end = int(input("结束数字 (默认: 7): ").strip() or '7')
        proxy_port = int(input("中转机SSH端口 (默认: 22): ").strip() or '22')
        proxy_username = input("中转机用户名: ").strip()
        
        print("中转机认证方式:")
        print("1. 密码认证")
        print("2. 私钥认证")
        auth_type = input("选择认证方式 (1/2): ").strip()
        
        proxy_config = {
            'host_prefix': proxy_prefix,
            'start_num': proxy_start,
            'end_num': proxy_end,
            'port': proxy_port,
            'username': proxy_username,
            'timeout': 30
        }
        
        if auth_type == '1':
            proxy_config['password'] = input("中转机密码: ").strip()
        else:
            proxy_config['private_key_path'] = input("私钥文件路径: ").strip()
            key_password = input("私钥密码 (可选，直接回车跳过): ").strip()
            if key_password:
                proxy_config['private_key_password'] = key_password
        
        # 目标机配置
        print("\n目标机配置:")
        target_host = input("目标机主机名或IP: ").strip()
        target_port = int(input("目标机SSH端口 (默认: 22): ").strip() or '22')
        target_username = input("目标机用户名: ").strip()
        
        print("目标机认证方式:")
        print("1. 密码认证")
        print("2. 私钥认证")
        target_auth_type = input("选择认证方式 (1/2): ").strip()
        
        target_config = {
            'host': target_host,
            'port': target_port,
            'username': target_username,
            'timeout': 30
        }
        
        if target_auth_type == '1':
            target_config['password'] = input("目标机密码: ").strip()
        else:
            target_config['private_key_path'] = input("目标机私钥文件路径: ").strip()
            target_key_password = input("目标机私钥密码 (可选，直接回车跳过): ").strip()
            if target_key_password:
                target_config['private_key_password'] = target_key_password
        
        return proxy_config, target_config
    
    @staticmethod
    def interactive_session():
        """
        交互式会话
        """
        try:
            print("欢迎使用 SSH/SFTP 多中转机连接工具!\n")
            
            # 获取配置
            proxy_config, target_config = InteractiveSSHSFTP.prompt_config()
            
            # 建立连接
            proxy = SSHSFTPProxy(proxy_config, target_config)
            
            if not proxy.connect():
                print("连接失败，程序退出")
                return
            
            # 创建SFTP
            sftp = proxy.create_sftp()
            if not sftp:
                print("SFTP创建失败")
                proxy.close()
                return
            
            print("\n=== 连接成功！进入交互模式 ===")
            print("可用命令:")
            print("  cmd <command>     - 执行shell命令")
            print("  upload <local> <remote> - 上传文件")
            print("  download <remote> <local> - 下载文件")
            print("  ls [path]         - 列出目录")
            print("  pwd               - 显示当前路径")
            print("  exit              - 退出程序")
            
            while True:
                try:
                    user_input = input("\n> ").strip()
                    if not user_input:
                        continue
                    
                    parts = user_input.split()
                    command = parts[0].lower()
                    
                    if command == 'exit':
                        break
                    elif command == 'cmd' and len(parts) > 1:
                        cmd = ' '.join(parts[1:])
                        exit_code, stdout, stderr = proxy.execute_command(cmd)
                        print(f"退出码: {exit_code}")
                        if stdout:
                            print(f"输出:\n{stdout}")
                        if stderr:
                            print(f"错误:\n{stderr}")
                    elif command == 'upload' and len(parts) >= 3:
                        local_path = parts[1]
                        remote_path = parts[2]
                        success = proxy.upload_file(local_path, remote_path)
                        print(f"上传{'成功' if success else '失败'}")
                    elif command == 'download' and len(parts) >= 3:
                        remote_path = parts[1]
                        local_path = parts[2]
                        success = proxy.download_file(remote_path, local_path)
                        print(f"下载{'成功' if success else '失败'}")
                    elif command == 'ls':
                        path = parts[1] if len(parts) > 1 else '.'
                        files = proxy.list_directory(path)
                        if files:
                            print(f"目录内容 ({path}):")
                            for f in files:
                                print(f"  {f}")
                        else:
                            print("获取目录列表失败")
                    elif command == 'pwd':
                        exit_code, stdout, stderr = proxy.execute_command('pwd')
                        if exit_code == 0:
                            print(f"当前路径: {stdout.strip()}")
                        else:
                            print(f"获取路径失败: {stderr}")
                    else:
                        print("未知命令或参数错误")
                        
                except KeyboardInterrupt:
                    print("\n程序被中断")
                    break
                except Exception as e:
                    print(f"操作异常: {e}")
            
        except Exception as e:
            logger.error(f"交互会话异常: {e}")
        finally:
            proxy.close()
            print("连接已关闭，再见!")


if __name__ == "__main__":
    import sys
    
    # 检查是否安装paramiko
    try:
        import paramiko
    except ImportError:
        print("错误: 需要安装 paramiko 库")
        print("安装命令: pip install paramiko")
        sys.exit(1)
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        # 交互式模式
        InteractiveSSHSFTP.interactive_session()
    else:
        # 演示模式
        print("演示模式运行...")
        print("要启用交互式模式，请使用: python ssh_sftp_proxy.py --interactive")
        print("或修改main()函数中的配置参数")
        main()