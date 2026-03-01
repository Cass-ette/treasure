import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

# 测试的易方达系列基金代码
fund_codes = [
    '017232',  # 易方达国证信息技术创新主题联接C
    '006328',  # 易方达中证海外互联网50ETF联接(QDII)
]

# 从基金代码获取基金名称和类型
def get_fund_info(fund_code):
    # 这里简化处理，实际应用中应从API或页面获取
    if fund_code == '017232':
        return '易方达国证信息技术创新主题联接C', '普通基金'
    elif fund_code == '006328':
        return '易方达中证海外互联网50ETF联接', 'QDII基金'
    return f'基金{fund_code}', '未知'

# 模拟主代码中的净值提取逻辑
def extract_nav(fund_code):
    url = f'http://fund.eastmoney.com/{fund_code}.html'
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    fund_name, fund_type = get_fund_info(fund_code)
    nav_value = None
    nav_date = None
    
    # 复制主代码中的净值提取逻辑
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
    
    # 如果方式0失败，使用模式4的QDII特殊处理逻辑
    if not nav_value:
        # 检查是否为QDII基金
        if 'QDII' in fund_type or '海外' in fund_name or '净值估算' in str(soup):
            print("检测到QDII/海外基金，应用特殊处理逻辑")
            
            # 方式1: 查找特定的净值数据容器
            nav_data_container = soup.find('div', id='jjjz_gsjz')
            if nav_data_container:
                # 在容器中查找所有表格
                tables = nav_data_container.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    if rows and len(rows) > 1:
                        # 通常第一行是最新数据
                        first_row = rows[1]
                        cells = first_row.find_all('td')
                        if cells and len(cells) > 1:
                            # 假设第一个数值单元格是单位净值
                            nav_value_str = cells[1].get_text(strip=True)
                            try:
                                nav_value = float(nav_value_str)
                                print(f"从专用容器获取QDII基金净值: {nav_value}")
                                # QDII基金日期通常在表格的第一个单元格
                                if cells[0]:
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
            
            # 方式2: 如果方式1失败，尝试查找所有表格
            if not nav_value:
                all_tables = soup.find_all('table')
                for table in all_tables:
                    # 查找包含'日期'和'单位净值'表头的表格
                    headers = table.find_all('th')
                    if headers and any('日期' in header.text for header in headers) and any('单位净值' in header.text for header in headers):
                        rows = table.find_all('tr')
                        if rows and len(rows) > 1:
                            # 通常第一行是最新数据
                            first_row = rows[1]
                            cells = first_row.find_all('td')
                            if cells and len(cells) > 1:
                                # 假设第一个数值单元格是单位净值
                                nav_value_str = cells[1].get_text(strip=True)
                                try:
                                    nav_value = float(nav_value_str)
                                    print(f"从所有表格中筛选获取QDII基金净值: {nav_value}")
                                    # QDII基金日期通常在表格的第一个单元格
                                    if cells[0]:
                                        date_text = cells[0].get_text(strip=True)
                                        if re.match(r'\d{4}-\d{2}-\d{2}', date_text):
                                            nav_date = date_text
                                            print(f"从所有表格中筛选获取QDII基金日期: {nav_date}")
                                except ValueError:
                                    continue
                        if nav_value:
                            break
    
    # 如果日期仍然未找到，使用当前日期减1天作为替代
    if not nav_date:
        today = datetime.now()
        nav_date = today.strftime('%Y-%m-%d')
        print(f"未找到日期，使用当前日期: {nav_date}")
    
    return nav_value, nav_date

# 测试所有基金
print("开始验证易方达系列基金净值爬取修复效果...")
print("="*60)

success_count = 0
for fund_code in fund_codes:
    print(f"\n测试基金代码: {fund_code}")
    print("-"*40)
    
    try:
        nav_value, nav_date = extract_nav(fund_code)
        fund_name, _ = get_fund_info(fund_code)
        
        if nav_value:
            print(f"✅ 成功爬取 {fund_name}({fund_code}) 的净值: {nav_value}，日期: {nav_date}")
            success_count += 1
        else:
            print(f"❌ 未能爬取 {fund_name}({fund_code}) 的净值")
    except Exception as e:
        print(f"❌ 爬取 {fund_code} 时发生错误: {str(e)}")

print("="*60)
print(f"测试完成，共{len(fund_codes)}只基金，成功{success_count}只")
if success_count == len(fund_codes):
    print("🎉 所有易方达系列基金净值爬取修复成功！")
else:
    print("⚠️ 部分易方达系列基金净值爬取仍有问题，请进一步检查。")