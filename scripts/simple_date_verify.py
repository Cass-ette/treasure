import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta

# 要测试的基金代码
fund_codes = ['020404', '006328', '270042']

# 模拟基金类型判断
def get_fund_info(fund_code):
    fund_info = {
        '020404': {'name': '易方达新常态灵活配置混合', 'type': '普通基金'},
        '006328': {'name': '易方达中证海外互联网50ETF联接', 'type': 'QDII基金'},
        '270042': {'name': '广发纳斯达克100ETF联接', 'type': 'QDII基金'}
    }
    return fund_info.get(fund_code, {'name': f'基金{fund_code}', 'type': '未知'})

# 模拟交易日判断
def is_market_day(date):
    # 简化版交易日判断：排除周末
    if date.weekday() >= 5:
        return False
    
    # 2025年节假日（部分）
    holidays = [
        datetime(2025, 1, 1).date(),  # 元旦
        datetime(2025, 1, 29).date(), datetime(2025, 1, 30).date(), 
        datetime(2025, 1, 31).date(), datetime(2025, 2, 1).date(), 
        datetime(2025, 2, 2).date(),  # 春节
    ]
    
    return date not in holidays

# 提取基金净值和日期（简化版）
def extract_fund_info(fund_code):
    url = f'http://fund.eastmoney.com/{fund_code}.html'
    print(f"\n正在访问: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        fund_info = get_fund_info(fund_code)
        fund_name = fund_info['name']
        fund_type = fund_info['type']
        
        nav_value = None
        nav_date = None
        
        print(f"基金名称: {fund_name}")
        print(f"基金类型: {fund_type}")
        
        # 1. 首先尝试全局日期搜索
        all_text = soup.get_text(strip=True)
        date_matches = re.findall(r'\d{4}-\d{2}-\d{2}', all_text)
        
        if date_matches:
            # 选择最近的日期
            sorted_dates = sorted([datetime.strptime(d, '%Y-%m-%d') for d in date_matches], reverse=True)
            nav_date = sorted_dates[0].strftime('%Y-%m-%d')
            print(f"从页面提取到日期: {nav_date}")
        else:
            print("未能从页面提取日期")
        
        # 2. 尝试方式0: 查找 class 为 'dataItem01' 的 dl 元素
        nav_element = soup.find('dl', class_='dataItem01')
        if nav_element:
            nav_text = nav_element.get_text(strip=True)
            print(f"方式0数据: {nav_text[:100]}...")
            
            # 尝试匹配单位净值
            nav_match = re.search(r'单位净值[:：]?\s*([0-9.]+)', nav_text)
            if nav_match:
                nav_value = float(nav_match.group(1))
                print(f"提取净值: {nav_value}")
                
                # 再次尝试匹配日期
                if not nav_date:
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', nav_text)
                    if date_match:
                        nav_date = date_match.group(1)
                        print(f"从方式0提取日期: {nav_date}")
        
        # 3. 特殊处理QDII基金
        if ('QDII' in fund_type.upper() or '海外' in fund_name):
            print("应用QDII特殊处理")
            
            # 查找特定的净值数据容器
            nav_data_container = soup.find('div', id='jjjz_gsjz')
            if nav_data_container:
                tables = nav_data_container.find_all('table')
                for table in tables:
                    headers = table.find_all('th')
                    if headers and any('日期' in header.text for header in headers):
                        rows = table.find_all('tr')
                        if rows and len(rows) > 1:
                            first_row = rows[1]
                            cells = first_row.find_all('td')
                            if cells and len(cells) > 0:
                                # 尝试获取日期
                                if not nav_date:
                                    date_text = cells[0].get_text(strip=True)
                                    if re.match(r'\d{4}-\d{2}-\d{2}', date_text):
                                        nav_date = date_text
                                        print(f"从QDII专用表格提取日期: {nav_date}")
                                break
        
        # 4. 如果日期仍然未找到，使用最近的交易日作为后备
        if not nav_date:
            print("使用最近的交易日作为后备日期")
            today = datetime.now().date()
            nav_date_str = today.strftime('%Y-%m-%d')
            
            # 如果今天不是交易日，查找最近的交易日
            if not is_market_day(today):
                for i in range(1, 8):
                    check_date = today - timedelta(days=i)
                    if is_market_day(check_date):
                        nav_date_str = check_date.strftime('%Y-%m-%d')
                        break
            
            nav_date = nav_date_str
            print(f"后备日期: {nav_date}")
        
        return nav_value, nav_date
        
    except Exception as e:
        print(f"获取数据时出错: {str(e)}")
        return None, None

def main():
    print("验证基金净值日期提取逻辑")
    print("="*80)
    print(f"当前日期: {datetime.now().strftime('%Y-%m-%d')}")
    print("="*80)
    
    for fund_code in fund_codes:
        nav_value, nav_date = extract_fund_info(fund_code)
        
        print("\n结果总结:")
        print(f"基金代码: {fund_code}")
        print(f"提取净值: {'成功' if nav_value else '失败'}")
        print(f"提取日期: {nav_date}")
        print(f"是否使用今天日期: {'是' if nav_date and nav_date == datetime.now().strftime('%Y-%m-%d') else '否'}")
        print("="*80)

if __name__ == '__main__':
    main()