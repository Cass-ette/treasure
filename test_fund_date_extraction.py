import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta

# 要测试的基金代码
fund_codes = ['020404', '006328', '270042']

# 模拟基金类型判断
def get_fund_info(fund_code):
    # 基金类型和名称信息（实际应用中应从页面获取）
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
    
    # 2025年节假日（这里只列部分作为示例）
    holidays = [
        datetime(2025, 1, 1).date(),  # 元旦
        datetime(2025, 1, 29).date(), datetime(2025, 1, 30).date(), 
        datetime(2025, 1, 31).date(), datetime(2025, 2, 1).date(), 
        datetime(2025, 2, 2).date(),  # 春节
        # 其他节假日略
    ]
    
    return date not in holidays

# 提取基金净值和日期
def extract_fund_info(fund_code):
    url = f'http://fund.eastmoney.com/{fund_code}.html'
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    fund_info = get_fund_info(fund_code)
    fund_name = fund_info['name']
    fund_type = fund_info['type']
    
    nav_value = None
    nav_date = None
    date_match = None
    
    print(f"\n测试基金: {fund_name}({fund_code})")
    print("-"*60)
    print(f"URL: {url}")
    
    # 方式0: 查找 class 为 'dataItem01' 的 dl 元素
    nav_element = soup.find('dl', class_='dataItem01')
    if nav_element:
        nav_text = nav_element.get_text(strip=True)
        print(f"方式0找到数据: {nav_text}")
        
        # 尝试直接匹配单位净值
        nav_match = re.search(r'单位净值[:：]?\s*([0-9.]+)', nav_text)
        if nav_match:
            nav_value = float(nav_match.group(1))
            print(f"从方式0提取净值: {nav_value}")
            
            # 尝试匹配日期
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', nav_text)
            if date_match:
                nav_date = date_match.group(1)
                print(f"从方式0提取日期: {nav_date}")
    
    # 模式2: 改进的'单位净值(日期)数值'格式匹配
    if not nav_value:
        # 匹配格式: 单位净值(2025-08-29)1.9952或单位净值(2025-08-29)1.9952-0.31%
        if nav_element:
            nav_text = nav_element.get_text(strip=True)
            nav_match = re.search(r'单位净值\((\d{4}-\d{2}-\d{2})\)([0-9.]+)', nav_text)
            if nav_match:
                print("匹配到'单位净值(日期)数值'格式")
                # 提取净值部分
                latest_nav_value = nav_match.group(2)
                # 处理净值和涨跌幅连在一起的情况
                if len(latest_nav_value) > 8:
                    dot_pos = latest_nav_value.find('.')
                    if dot_pos > 0 and dot_pos + 5 <= len(latest_nav_value):
                        latest_nav_value = latest_nav_value[:dot_pos + 5]
                        print(f"处理连在一起的涨跌幅，提取净值: {latest_nav_value}")
                nav_value = float(latest_nav_value)
                
                # 提取日期
                if not nav_date:
                    nav_date = nav_match.group(1)
                    print(f"从单位净值格式提取日期: {nav_date}")
    
    # 检查是否为QDII基金
    if not nav_value and ('QDII' in fund_type.upper() or '海外' in fund_name or '净值估算' in str(soup)):
        print("检测到QDII/海外基金，应用特殊处理逻辑")
        
        # 方式1: 查找特定的净值数据容器
        nav_data_container = soup.find('div', id='jjjz_gsjz')
        if nav_data_container:
            print("找到净值数据容器")
            tables = nav_data_container.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                if rows and len(rows) > 1:
                    first_row = rows[1]
                    cells = first_row.find_all('td')
                    if cells and len(cells) > 1:
                        nav_value_str = cells[1].get_text(strip=True)
                        try:
                            nav_value = float(nav_value_str)
                            print(f"从专用容器获取QDII基金净值: {nav_value}")
                            # 尝试提取日期
                            if cells[0] and not nav_date:
                                date_text = cells[0].get_text(strip=True)
                                if re.match(r'\d{4}-\d{2}-\d{2}', date_text):
                                    nav_date = date_text
                                    print(f"从专用容器获取QDII基金日期: {nav_date}")
                        except ValueError:
                            continue
                    if nav_value:
                        break
                if nav_value:
                    break
        
        # 方式2: 查找所有表格
        if not nav_value:
            all_tables = soup.find_all('table')
            for table in all_tables:
                # 查找包含'日期'和'单位净值'表头的表格
                headers = table.find_all('th')
                if headers and any('日期' in header.text for header in headers) and any('单位净值' in header.text for header in headers):
                    print("找到包含净值信息的表格")
                    rows = table.find_all('tr')
                    if rows and len(rows) > 1:
                        first_row = rows[1]
                        cells = first_row.find_all('td')
                        if cells and len(cells) > 1:
                            nav_value_str = cells[1].get_text(strip=True)
                            try:
                                nav_value = float(nav_value_str)
                                print(f"从表格中获取净值: {nav_value}")
                                # 尝试提取日期
                                if cells[0] and not nav_date:
                                    date_text = cells[0].get_text(strip=True)
                                    if re.match(r'\d{4}-\d{2}-\d{2}', date_text):
                                        nav_date = date_text
                                        print(f"从表格中获取日期: {nav_date}")
                            except ValueError:
                                continue
                    if nav_value:
                        break
    
    # 如果仍然无法提取净值，尝试直接从页面中查找所有数字序列
    if not nav_value:
        all_text = soup.get_text(strip=True)
        # 优先匹配3-4位小数的数值
        all_numbers = re.findall(r'\b[0-9]+\.[0-9]{3,4}\b', all_text) 
        if all_numbers:
            # 寻找看起来像净值的数字（通常在0.1-10之间的数值）
            for num in all_numbers:
                try:
                    float_num = float(num)
                    if 0.1 <= float_num <= 10:
                        nav_value = float_num
                        print(f"通过数值范围匹配到可能的净值: {nav_value}")
                        break
                except ValueError:
                    continue
    
    # 专门针对日期的提取逻辑
    if not nav_date:
        # 从页面中搜索所有日期格式
        all_text = soup.get_text(strip=True)
        date_matches = re.findall(r'\d{4}-\d{2}-\d{2}', all_text)
        if date_matches:
            # 选择最近的日期
            sorted_dates = sorted([datetime.strptime(d, '%Y-%m-%d') for d in date_matches], reverse=True)
            nav_date = sorted_dates[0].strftime('%Y-%m-%d')
            print(f"从页面中提取到最新日期: {nav_date}")
    
    # 如果日期仍然未找到，使用最近的交易日作为后备
    if not nav_date:
        print("未能从页面提取日期，使用最近的交易日作为后备")
        today = datetime.now().date()
        nav_date_str = today.strftime('%Y-%m-%d')
        
        # 如果今天不是交易日，查找最近的交易日
        if not is_market_day(today):
            # 向前查找最近的交易日
            for i in range(1, 8):
                check_date = today - timedelta(days=i)
                if is_market_day(check_date):
                    nav_date_str = check_date.strftime('%Y-%m-%d')
                    break
        
        nav_date = nav_date_str
        print(f"使用后备日期: {nav_date}")
    
    return nav_value, nav_date

# 测试所有基金
def test_all_funds():
    print("开始测试基金净值和日期提取...")
    print("="*80)
    
    results = {}
    for fund_code in fund_codes:
        nav_value, nav_date = extract_fund_info(fund_code)
        results[fund_code] = {'nav': nav_value, 'date': nav_date}
        
        print(f"\n测试结果:")
        print(f"净值: {'成功' if nav_value else '失败'}")
        print(f"日期: {'成功 (从页面提取)' if nav_date and not nav_date.startswith(str(datetime.now().year)) else '使用后备日期' if nav_date else '失败'}")
        print(f"最终净值: {nav_value}")
        print(f"最终日期: {nav_date}")
        print(f"是否为今天日期: {'是' if nav_date == datetime.now().strftime('%Y-%m-%d') else '否'}")
        print("="*80)
    
    return results

if __name__ == '__main__':
    test_all_funds()