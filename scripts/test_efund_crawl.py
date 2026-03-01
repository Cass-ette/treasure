# 测试易方达系列基金净值爬取
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

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

print("开始测试易方达系列基金净值爬取...")
print("注意：此测试仅显示爬取过程和结果，不涉及数据库操作\n")

success_count = 0
for code, name in all_funds.items():
    print(f"\n======= 测试基金: {name} ({code}) =======")
    
    try:
        # 使用天天基金网作为数据源
        url = f"http://fund.eastmoney.com/{code}.html"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        print(f"尝试爬取基金 {code} 的净值数据，URL: {url}")
        response = requests.get(url, headers=headers, timeout=20)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试获取基金名称
            fund_name_elem = soup.find('div', class_='fundDetail-tit') or soup.find('h1')
            if fund_name_elem:
                fund_name_text = fund_name_elem.get_text(strip=True)
                print(f"页面显示基金名称: {fund_name_text}")
            
            # 保存网页内容以便分析
            with open(f'fund_debug_{code}.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"网页内容已保存到 fund_debug_{code}.html")
            
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
            
            # 方式4: 查找特定的价格标签，但不使用颜色作为判断标准
            if not latest_nav_elem:
                # 查找大字体的价格标签，不限制颜色
                price_elem = soup.find('span', class_='ui-font-large')
                if price_elem:
                    latest_nav_elem = price_elem
                    # 检查元素是否有颜色类
                    color_classes = [cls for cls in price_elem.get('class', []) if cls.startswith('ui-color-')]
                    color_text = color_classes[0] if color_classes else '无颜色类'
                    print(f"方式4: 找到价格标签元素(大字体, {color_text})")
            
            # 方式5: 查找顶部悬浮栏中的单位净值
            if not latest_nav_elem:
                fixed_nav_elem = soup.find('span', class_='fix_dwjz')
                if fixed_nav_elem:
                    latest_nav_elem = fixed_nav_elem
                    print("方式5: 找到顶部悬浮栏中的单位净值")
            
            # 显示所有可能包含单位净值的元素
            print("\n检查页面上所有包含'单位净值'的元素:")
            unit_nav_elements = soup.find_all(text=re.compile(r'单位净值'))
            for i, elem in enumerate(unit_nav_elements):
                if elem.parent:
                    print(f"元素{i+1}: {elem.parent.text.strip()}")
                    print(f"  元素HTML: {elem.parent}")
            
            if latest_nav_elem:
                # 提取净值文本
                nav_text = latest_nav_elem.get_text(strip=True)
                print(f"\n找到净值元素，文本内容: {nav_text}")
                print(f"元素HTML: {latest_nav_elem}")
                
                # 使用正则表达式提取数字，尝试多种模式
                
                # 模式1: 优先匹配带空格的'单位净值：数值'格式
                nav_match = re.search(r'单位净值[：:]\s*([0-9.]+)', nav_text)
                date_match = re.search(r'更新时间[：:]\s*([0-9-]+)', nav_text)
                
                # 模式2: 改进的'单位净值(日期)数值'格式匹配
                if not nav_match:
                    nav_match = re.search(r'单位净值\((\d{4}-\d{2}-\d{2})\)([0-9.]+)', nav_text)
                    if nav_match:
                        print("匹配到'单位净值(日期)数值'格式")
                        latest_nav_value = nav_match.group(2)
                        if len(latest_nav_value) > 8:
                            dot_pos = latest_nav_value.find('.')
                            if dot_pos > 0 and dot_pos + 5 <= len(latest_nav_value):
                                latest_nav_value = latest_nav_value[:dot_pos + 5]
                                print(f"处理连在一起的涨跌幅，提取净值: {latest_nav_value}")
                        nav_match = type('obj', (object,), {'group': lambda s, x=1: latest_nav_value})
                
                if not date_match:
                    date_match = re.search(r'更新日期：([0-9-]+)', nav_text)
                    if not date_match:
                        date_match = re.search(r'单位净值\((\d{4}-\d{2}-\d{2})\)', nav_text)
                
                # 模式3: 适配新的网页结构格式
                if not nav_match and not date_match:
                    date_match = re.search(r'单位净值\(([0-9-]+)\)', nav_text)
                    if date_match:
                        nav_part = nav_text.split(date_match.group(0))[1] if date_match else nav_text
                        nav_match = re.search(r'(\d+\.\d{3,4})', nav_part)
                
                # 模式4: 避免使用累计净值
                if not nav_match:
                    if '累计净值' in nav_text:
                        parts = nav_text.split('累计净值')
                        nav_text = parts[0]
                        print("发现累计净值，尝试只使用单位净值部分的文本")
                    
                    all_numbers = re.findall(r'\b[0-9]+\.[0-9]{3,4}\b', nav_text)  # 优先匹配3-4位小数的数值
                    if not all_numbers:
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
                
                if nav_match and date_match:
                    latest_nav = float(nav_match.group(1))
                    try:
                        nav_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                    except:
                        nav_date = datetime.now()
                    print(f"成功提取净值: {latest_nav}, 日期: {nav_date}")
                    print("✅ 净值提取成功！")
                    success_count += 1
                else:
                    print("❌ 未能从文本中提取有效的净值和日期")
                    print("尝试使用更直接的方式提取...")
                    # 直接搜索页面上所有包含单位净值的元素
                    for elem in unit_nav_elements:
                        if elem.parent:
                            parent_text = elem.parent.text.strip()
                            nav_match = re.search(r'([0-9.]+)', parent_text)
                            if nav_match:
                                try:
                                    float_nav = float(nav_match.group(1))
                                    if 0.1 <= float_nav <= 10:
                                        print(f"直接从包含'单位净值'的元素提取: {float_nav}")
                                        break
                                except:
                                    continue
            else:
                print("❌ 未能找到包含净值信息的元素")
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 测试过程中出错: {str(e)}")
    
    # 为了避免请求过于频繁，暂停2秒
    import time
    time.sleep(2)

print(f"\n测试完成: 共测试 {len(all_funds)} 只基金，成功 {success_count} 只")