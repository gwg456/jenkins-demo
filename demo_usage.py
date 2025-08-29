#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Jenkins Demo 使用示例
演示如何与Web应用进行交互
"""

import requests
import json
import time

def test_web_app(base_url="http://localhost:8080"):
    """测试Web应用的各个端点"""
    
    print("🚀 Jenkins Demo Web应用测试")
    print(f"📍 目标URL: {base_url}")
    print("-" * 50)
    
    # 测试主页端点
    print("1️⃣ 测试主页端点 (/)")
    try:
        response = requests.get(f"{base_url}/")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        print("✅ 主页测试通过\n")
    except Exception as e:
        print(f"❌ 主页测试失败: {e}\n")
    
    # 测试健康检查端点
    print("2️⃣ 测试健康检查端点 (/health)")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        print("✅ 健康检查通过\n")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}\n")
    
    # 测试API信息端点
    print("3️⃣ 测试API信息端点 (/api/info)")
    try:
        response = requests.get(f"{base_url}/api/info")
        print(f"状态码: {response.status_code}")
        data = response.json()
        print("📊 API信息:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("✅ API信息测试通过\n")
    except Exception as e:
        print(f"❌ API信息测试失败: {e}\n")

def load_test(base_url="http://localhost:8080", requests_count=10):
    """简单的负载测试"""
    
    print("⚡ 负载测试")
    print(f"📍 目标URL: {base_url}")
    print(f"🔢 请求次数: {requests_count}")
    print("-" * 50)
    
    success_count = 0
    total_time = 0
    
    for i in range(requests_count):
        start_time = time.time()
        try:
            response = requests.get(f"{base_url}/health")
            end_time = time.time()
            response_time = end_time - start_time
            total_time += response_time
            
            if response.status_code == 200:
                success_count += 1
                print(f"请求 {i+1}: ✅ ({response_time:.3f}s)")
            else:
                print(f"请求 {i+1}: ❌ 状态码 {response.status_code}")
        except Exception as e:
            print(f"请求 {i+1}: ❌ 错误 {e}")
    
    success_rate = (success_count / requests_count) * 100
    avg_response_time = total_time / requests_count if requests_count > 0 else 0
    
    print("-" * 50)
    print(f"📈 测试结果:")
    print(f"   成功率: {success_rate:.1f}% ({success_count}/{requests_count})")
    print(f"   平均响应时间: {avg_response_time:.3f}s")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Jenkins Demo 使用示例")
    parser.add_argument("--url", default="http://localhost:8080", 
                       help="Web应用的URL (默认: http://localhost:8080)")
    parser.add_argument("--load-test", action="store_true", 
                       help="执行负载测试")
    parser.add_argument("--requests", type=int, default=10, 
                       help="负载测试的请求次数 (默认: 10)")
    
    args = parser.parse_args()
    
    # 基本功能测试
    test_web_app(args.url)
    
    # 负载测试 (如果指定)
    if args.load_test:
        load_test(args.url, args.requests)
    
    print("🎉 测试完成！") 