# -*- coding: utf-8 -*-

"""测试前三十日平均净值API接口"""

import sys
import os
import requests
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 定义测试函数
def test_average_nav_api():
    # 应用运行在本地5000端口
    base_url = 'http://localhost:5000'
    
    try:
        # 首先尝试登录获取session
        print("尝试登录系统...")
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        # 创建一个会话对象来保持登录状态
        session = requests.Session()
        
        # 发送登录请求
        login_response = session.post(f'{base_url}/login', data=login_data)
        
        if login_response.status_code == 200:
            print("登录成功！")
            
            # 获取所有基金ID（这里简化处理，假设我们知道一些基金ID）
            # 实际应用中，应该先调用获取基金列表的API
            fund_ids = [1, 2, 3, 4, 5]  # 假设有这些基金ID
            
            print("\n===== 测试前三十日平均净值API =====")
            
            for fund_id in fund_ids:
                # 调用获取前三十日平均净值的API
                try:
                    response = session.get(f'{base_url}/get_fund_30_day_average?fund_id={fund_id}')
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"基金ID {fund_id}:")
                        print(f"  状态: {'成功' if data.get('success') else '失败'}")
                        if data.get('success'):
                            print(f"  前三十日平均净值: {data.get('average_nav'):.4f}")
                            print(f"  实际使用交易日数量: {data.get('trading_days_count')}")
                            print(f"  消息: {data.get('message')}")
                        else:
                            print(f"  错误信息: {data.get('message')}")
                    else:
                        print(f"基金ID {fund_id}: 请求失败，状态码: {response.status_code}")
                except Exception as e:
                    print(f"基金ID {fund_id}: 调用API时出错: {str(e)}")
            
            # 登出系统
            session.get(f'{base_url}/logout')
        else:
            print(f"登录失败，状态码: {login_response.status_code}")
            print("请确保应用正在运行，并且管理员账户信息正确")
            
    except requests.exceptions.ConnectionError:
        print("连接错误: 无法连接到应用服务器")
        print("请确保应用正在运行，然后再运行此测试脚本")
    except Exception as e:
        print(f"发生错误: {str(e)}")

# 提供使用说明
def print_usage():
    print("===== 前三十日平均净值API测试工具 =====")
    print("使用说明:")
    print("1. 请确保应用服务器正在运行 (python simple_app.py)")
    print("2. 确保管理员账户(admin/admin123)存在")
    print("3. 运行此脚本进行测试")
    print("\n注意: 如果应用运行在不同的端口，请修改脚本中的base_url")

if __name__ == "__main__":
    print_usage()
    print("\n开始测试...")
    test_average_nav_api()