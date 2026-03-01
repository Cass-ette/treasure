# 测试修复后的基金净值爬取功能（仅净值提取逻辑）
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import time

# 用户提到的易方达系列基金
funds_to_test = {
    '017232': '易方达国证信息技术创新主题联接C',
    '006328': '易方达中证海外互联网50ETF联接'
}

# 之前测试的基金作为对照
control_funds = {
    '001167': '金鹰科技创新股票A',
    '018957': '中航机遇领航混合C',
    '018994': '中欧数字经济混合C',
    '007519': '东方阿尔法优选混合C'
}

# 合并所有要测试的基金
all_funds = {**funds_to_test, **control_funds}

# 模拟simple_app.py中修复后的净值提取逻辑
def extract_nav(fund_code, fund_name):
    """仅测试净值提取逻辑，不涉及数据库操作"""
    try:
        print(f"\n======= 测试基金: {fund_name} ({fund_code}) =======")
        
        # 使用天天基金网作为数据源
        url = f"http://fund.eastmoney.com/{fund_code}.html"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        print(f"尝试爬取基金 {fund_code} 的净值数据，URL: {url}")
        response = requests.get(url, headers=headers, timeout=20)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试获取基金名称
            fund_name_elem = soup.find('div', class_='fundDetail-tit') or soup.find('h1')
            if fund_name_elem:
                fund_name_text = fund_name_elem.get_text(strip=True)
                print(f"页面显示基金名称: {fund_name_text}")
            
            # 重新设计查找策略，不使用颜色作为判断标准
            latest_nav_elem = None
            
            # 方式0: 优先查找特定的单位净值元素 - 最可靠的方式
            unit_nav_elem = soup.find('dl', class_='dataItem01')
            if unit_nav_elem:
                latest_nav_elem = unit_nav_elem
                print("方式0: 直接找到单位净值元素(dataItem01)")
            
            # 方式1: 查找特定的净值展示区域
            if not latest_nav_elem:
                # 查找净值信息卡片
                nav_info_card = soup.find('div', class_='fundInfoItem')
                if nav_info_card:
                    # 在卡片内查找所有包含数字的元素
                    number_elements = nav_info_card.find_all(text=re.compile(r'[0-9.]+'))
                    if number_elements:
                        # 寻找包含'单位净值'的元素
                        for num_text in number_elements:
                            if num_text.parent:
                                # 检查元素文本是否包含'单位净值'
                                if '单位净值' in num_text.parent.text:
                                    latest_nav_elem = num_text.parent
                                    print("方式1: 在净值卡片中找到包含单位净值的元素")
                                    break
            
            # 方式2: 查找特定的类名组合
            if not latest_nav_elem:
                nav_data_section = soup.find('div', class_='dataOfFund')
                if nav_data_section:
                    latest_nav_elem = nav_data_section
                    print("方式2: 找到数据区域元素")
            
            # 方式3: 查找包含单位净值的表格
            if not latest_nav_elem:
                nav_table = soup.find('table', class_='w782')
                if nav_table:
                    rows = nav_table.find_all('tr')
                    if rows and len(rows) > 1:
                        # 通常第一行是最新数据
                        first_row = rows[1]
                        cells = first_row.find_all('td')
                        if cells and len(cells) > 1:
                            # 假设第一个数值单元格是单位净值
                            latest_nav_elem = cells[1]  # 单元格包含单位净值
                            print("方式3: 从历史净值表格中获取最新单位净值")
            
            # 方式4: 查找特定的价格标签 - 不限制颜色
            if not latest_nav_elem:
                price_elem = soup.find('span', class_='ui-font-large')
                if price_elem:
                    latest_nav_elem = price_elem
                    # 获取颜色类信息用于调试
                    color_classes = [cls for cls in price_elem.get('class', []) if cls.startswith('ui-color-')]
                    color_text = color_classes[0] if color_classes else '无颜色类'
                    print(f"方式4: 找到价格标签元素(大字体, {color_text})")
            
            # 方式5: 查找顶部悬浮栏中的单位净值
            if not latest_nav_elem:
                fixed_nav_elem = soup.find('span', class_='fix_dwjz')
                if fixed_nav_elem:
                    latest_nav_elem = fixed_nav_elem
                    print("方式5: 找到顶部悬浮栏中的单位净值")
            
            if latest_nav_elem:
                # 提取净值文本
                nav_text = latest_nav_elem.get_text(strip=True)
                print(f"找到净值元素，文本内容: {nav_text}")
                
                # 使用正则表达式提取数字，尝试多种模式
                
                # 模式1: 优先匹配带空格的'单位净值：数值'格式
                nav_match = re.search(r'单位净值[：:]\s*([0-9.]+)', nav_text)
                date_match = re.search(r'更新时间[：:]\s*([0-9-]+)', nav_text)
                
                # 模式2: 改进的'单位净值(日期)数值'格式匹配，处理净值和涨跌幅连在一起的情况
                if not nav_match:
                    # 匹配格式: 单位净值(2025-08-29)1.9952或单位净值(2025-08-29)1.9952-0.31%
                    nav_match = re.search(r'单位净值\((\d{4}-\d{2}-\d{2})\)([0-9.]+)', nav_text)
                    if nav_match:
                        print("匹配到'单位净值(日期)数值'格式")
                        # 提取净值部分，确保只获取到有效的净值数值
                        latest_nav_value = nav_match.group(2)
                        # 检查净值部分是否包含额外的数字（涨跌幅与净值连在一起的情况）
                        if len(latest_nav_value) > 8:  # 净值通常不会超过8个字符(如9.9999)
                            # 查找第一个完整的小数
                            dot_pos = latest_nav_value.find('.')
                            if dot_pos > 0 and dot_pos + 5 <= len(latest_nav_value):
                                # 提取小数点前的数字和小数点后4位
                                latest_nav_value = latest_nav_value[:dot_pos + 5]
                                print(f"处理连在一起的涨跌幅，提取净值: {latest_nav_value}")
                        nav_match = type('obj', (object,), {'group': lambda s, x=1: latest_nav_value})
                
                if not date_match:
                    date_match = re.search(r'更新日期：([0-9-]+)', nav_text)
                    print("尝试使用'更新日期'查找日期")
                    # 检查是否包含日期格式的文本
                    if not date_match:
                        date_match = re.search(r'单位净值\((\d{4}-\d{2}-\d{2})\)', nav_text)
                        if date_match:
                            print("从单位净值格式中提取日期")
                
                # 模式3: 适配新的网页结构格式 - 单位净值(YYYY-MM-DD)XXXX
                if not nav_match and not date_match:
                    # 使用更精确的正则表达式提取日期和净值
                    date_match = re.search(r'单位净值\(([0-9-]+)\)', nav_text)
                    if date_match:
                        print("匹配到新格式: 单位净值(YYYY-MM-DD)XXXX")
                        # 提取日期后的第一个有效净值数值
                        nav_part = nav_text.split(date_match.group(0))[1] if date_match else nav_text
                        # 只提取第一个有效的浮点数
                        nav_match = re.search(r'(\d+\.\d{3,4})', nav_part)  # 假设净值通常有3-4位小数
                        if nav_match:
                            print(f"提取到净值: {nav_match.group(1)}")
                
                # 模式4: 避免使用累计净值，确保获取正确的单位净值
                if not nav_match:
                    # 首先检查文本中是否有'累计净值'字样
                    if '累计净值' in nav_text:
                        # 分割文本，只保留'单位净值'相关部分
                        parts = nav_text.split('累计净值')
                        nav_text = parts[0]  # 假设单位净值在累计净值前面
                        print("发现累计净值，尝试只使用单位净值部分的文本")
                    
                    # 检查是否为QDII基金
                    if 'QDII' in fund_name.upper() or '海外' in fund_name or '净值估算' in nav_text:
                        print("检测到QDII/海外基金，应用特殊处理逻辑")
                        # QDII基金可能在非交易时段不显示实时净值，尝试多种方式查找
                        
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
                                        nav_value = cells[1].get_text(strip=True)
                                        try:
                                            float_num = float(nav_value)
                                            nav_match = type('obj', (object,), {'group': lambda s, x=1: float_num})
                                            print(f"从专用容器获取QDII基金净值: {float_num}")
                                            # QDII基金日期通常在表格的第一个单元格
                                            if cells[0]:
                                                date_text = cells[0].get_text(strip=True)
                                                try:
                                                    # 尝试解析日期格式
                                                    if re.match(r'\d{4}-\d{2}-\d{2}', date_text):
                                                        nav_date = datetime.strptime(date_text, '%Y-%m-%d')
                                                        date_match = type('obj', (object,), {'group': lambda s, x=1: date_text})
                                                        print(f"从专用容器获取QDII基金日期: {nav_date}")
                                                        break  # 找到日期后退出循环
                                                except:
                                                    pass
                                        except ValueError:
                                            continue
                                    if nav_match and date_match:
                                        break
                                if nav_match and date_match:
                                    break
                        
                        # 方式2: 如果方式1失败，尝试查找所有表格
                        if not nav_match:
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
                                            nav_value = cells[1].get_text(strip=True)
                                            try:
                                                float_num = float(nav_value)
                                                nav_match = type('obj', (object,), {'group': lambda s, x=1: float_num})
                                                print(f"从所有表格中筛选获取QDII基金净值: {float_num}")
                                                # QDII基金日期通常在表格的第一个单元格
                                                if cells[0]:
                                                    date_text = cells[0].get_text(strip=True)
                                                    try:
                                                        # 尝试解析日期格式
                                                        if re.match(r'\d{4}-\d{2}-\d{2}', date_text):
                                                            nav_date = datetime.strptime(date_text, '%Y-%m-%d')
                                                            date_match = type('obj', (object,), {'group': lambda s, x=1: date_text})
                                                            print(f"从所有表格中筛选获取QDII基金日期: {nav_date}")
                                                            break  # 找到日期后退出循环
                                                    except:
                                                        pass
                                            except ValueError:
                                                continue
                                    if nav_match and date_match:
                                        break
                        
                        # 方式3: 对于QDII基金，如果找不到日期，使用当前日期作为替代
                        if nav_match and not date_match:
                            # 设置为当前日期减去1天（通常是最近的交易日）
                            nav_date = datetime.now() - timedelta(days=1)
                            date_text = nav_date.strftime('%Y-%m-%d')
                            date_match = type('obj', (object,), {'group': lambda s, x=1: date_text})
                            print(f"QDII基金未找到日期，使用最近交易日: {nav_date}")
                    
                    # 如果QDII特殊处理失败，尝试直接提取所有数字序列
                    if not nav_match:
                        # 优先匹配3-4位小数的数值
                        all_numbers = re.findall(r'\b[0-9]+\.[0-9]{3,4}\b', nav_text) 
                        if not all_numbers:
                            # 如果没有匹配到，尝试更宽松的匹配
                            all_numbers = re.findall(r'[0-9.]+', nav_text)
                        
                        # 寻找看起来像净值的数字（通常在0.1-10之间的数值）
                        for num in all_numbers:
                            try:
                                float_num = float(num)
                                # 更严格的净值范围判断，避免误判累计净值
                                if 0.1 <= float_num <= 10:
                                    nav_match = type('obj', (object,), {'group': lambda s, x=1: float_num})
                                    print(f"通过数值范围匹配到可能的净值: {float_num}")
                                    break
                            except ValueError:
                                continue
                
                if nav_match and date_match:
                    latest_nav = float(nav_match.group(1))
                    try:
                        nav_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                    except:
                        nav_date = datetime.now()
                    print(f"成功提取净值: {latest_nav}, 日期: {nav_date}")
                    print("✅ 净值提取成功！")
                    return True
                else:
                    print("❌ 未能从文本中提取有效的净值和日期")
                    return False
            else:
                print("❌ 未能找到包含净值信息的元素")
                return False
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试过程中出错: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始测试修复后的基金净值爬取功能...")
    print("注意：本测试仅验证净值提取逻辑，不涉及数据库操作\n")
    
    success_count = 0
    for code, name in all_funds.items():
        result = extract_nav(code, name)
        if result:
            success_count += 1
        
        # 为了避免请求过于频繁，暂停2秒
        time.sleep(2)
    
    print(f"\n测试完成: 共测试 {len(all_funds)} 只基金，成功 {success_count} 只")
    print("\n结论：")
    if success_count == len(all_funds):
        print("✅ 所有基金净值爬取成功！移除颜色限制的修复生效。")
    else:
        print(f"❌ 仍有 {len(all_funds) - success_count} 只基金爬取失败，需要进一步修复。")