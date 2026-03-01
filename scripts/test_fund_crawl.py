import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

# 要测试的基金列表
fund_codes = ['001167', '018957', '018994', '007519']
fund_names = {
    '001167': '金鹰科技创新股票A',
    '018957': '中航机遇领航混合C',
    '018994': '中欧数字经济混合C',
    '007519': '东方阿尔法优选混合C'
}

def test_fund_crawl(fund_code, fund_name):
    """测试单个基金的爬取情况"""
    try:
        print(f"\n测试基金: {fund_name} ({fund_code})")
        
        # 使用天天基金网作为数据源
        url = f"http://fund.eastmoney.com/{fund_code}.html"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        response = requests.get(url, headers=headers, timeout=20)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 保存网页内容到临时文件以便分析
        with open(f"fund_{fund_code}.html", "w", encoding="utf-8") as f:
            f.write(soup.prettify())
        print(f"网页内容已保存到 fund_{fund_code}.html")
        
        # 尝试多种方式查找最新净值
        latest_nav_elem = None
        
        # 1. 尝试原始的方式 - 查找dataItem02
        latest_nav_elem = soup.find('dl', class_='dataItem02')
        if latest_nav_elem:
            print("找到 dataItem02 元素")
        else:
            # 2. 查找fundInfoItem
            latest_nav_elem = soup.find('div', class_='fundInfoItem')
            if latest_nav_elem:
                print("找到 fundInfoItem 元素")
            else:
                # 3. 查找包含'单位净值'的文本
                nav_text_elem = soup.find(text=re.compile(r'单位净值'))
                if nav_text_elem:
                    latest_nav_elem = nav_text_elem.parent
                    print("找到包含'单位净值'的文本元素")
                else:
                    # 4. 查找价格标签
                    price_elem = soup.find('span', class_='ui-font-large ui-color-red')
                    if price_elem:
                        latest_nav_elem = price_elem
                        print("找到价格标签元素")
        
        if latest_nav_elem:
            nav_text = latest_nav_elem.get_text(strip=True)
            print(f"找到净值元素，文本内容: {nav_text}")
            
            # 尝试提取净值
            # 模式1: 原始模式
            nav_match = re.search(r'单位净值：([0-9.]+)', nav_text)
            date_match = re.search(r'更新时间：([0-9-]+)', nav_text)
            
            # 模式2: 无空格格式
            if not nav_match:
                nav_match = re.search(r'单位净值:([0-9.]+)', nav_text)
                print("尝试使用无空格格式查找单位净值")
            
            # 模式3: 单位净值(日期)数值格式
            if not nav_match:
                nav_match = re.search(r'单位净值\((\d{4}-\d{2}-\d{2})\)([0-9.]+)', nav_text)
                if nav_match:
                    print("匹配到'单位净值(日期)数值'格式")
                    # 提取净值部分
                    latest_nav_value = nav_match.group(2)
                    nav_match = type('obj', (object,), {'group': lambda s, x=1: latest_nav_value})
            
            # 模式4: 提取所有数字
            if not nav_match:
                all_numbers = re.findall(r'[0-9.]+', nav_text)
                for num in all_numbers:
                    try:
                        float_num = float(num)
                        if 0.1 <= float_num <= 10:
                            nav_match = type('obj', (object,), {'group': lambda s, x=1: float_num})
                            print(f"通过数值范围匹配到可能的净值: {float_num}")
                            break
                    except ValueError:
                        continue
            
            if nav_match:
                latest_nav = float(nav_match.group(1))
                print(f"成功提取净值: {latest_nav}")
            else:
                print("未能提取净值")
        else:
            print("未能找到包含净值信息的元素")
            
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")

if __name__ == "__main__":
    print("开始测试基金净值爬取功能...")
    for code in fund_codes:
        test_fund_crawl(code, fund_names[code])
    print("\n测试完成")