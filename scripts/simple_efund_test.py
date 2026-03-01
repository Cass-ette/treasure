# 简单测试易方达系列基金
import requests
from bs4 import BeautifulSoup
import re
import time

# 用户提到的易方达系列基金
funds = {
    '017232': '易方达国证信息技术创新主题联接C',
    '006328': '易方达中证海外互联网50ETF联接'
}

print("开始简单测试易方达系列基金...")

for code, name in funds.items():
    print(f"\n======= 测试基金: {name} ({code}) =======")
    
    try:
        url = f"http://fund.eastmoney.com/{code}.html"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        print(f"请求URL: {url}")
        response = requests.get(url, headers=headers, timeout=20)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            print(f"请求成功，状态码: {response.status_code}")
            
            # 直接查找所有包含'单位净值'的文本
            soup = BeautifulSoup(response.text, 'html.parser')
            unit_nav_texts = soup.find_all(text=re.compile(r'单位净值'))
            
            print(f"找到{len(unit_nav_texts)}个包含'单位净值'的文本元素")
            for i, text in enumerate(unit_nav_texts):
                # 获取包含此文本的元素
                parent = text.find_parent()
                if parent:
                    print(f"元素{i+1}: {parent.text.strip()[:100]}...")
                    # 查找其中的数值
                    numbers = re.findall(r'[0-9.]+', parent.text)
                    if numbers:
                        print(f"  提取到的数字: {numbers}")
                        
                    # 查看是否有颜色类
                    color_classes = []
                    if hasattr(parent, 'attrs') and 'class' in parent.attrs:
                        color_classes = [cls for cls in parent.attrs['class'] if cls.startswith('ui-color-')]
                    if color_classes:
                        print(f"  颜色类: {color_classes}")
            
            # 尝试查找大字体元素
            large_font_elements = soup.find_all(class_='ui-font-large')
            print(f"\n找到{len(large_font_elements)}个大字体元素")
            for i, elem in enumerate(large_font_elements):
                text = elem.text.strip()
                print(f"大字体元素{i+1}: '{text}'")
                # 查看是否有颜色类
                color_classes = []
                if hasattr(elem, 'attrs') and 'class' in elem.attrs:
                    color_classes = [cls for cls in elem.attrs['class'] if cls.startswith('ui-color-')]
                if color_classes:
                    print(f"  颜色类: {color_classes}")
        else:
            print(f"请求失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")
    
    time.sleep(2)

print("\n测试完成")