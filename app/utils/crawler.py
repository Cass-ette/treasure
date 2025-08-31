import requests
from bs4 import BeautifulSoup
from datetime import datetime
import akshare as ak
import requests
import pandas as pd

class FundCrawler:
    @staticmethod
    def get_fund_nav(fund_code):
        """获取基金最新净值"""
        try:
            # 尝试使用akshare库获取数据
            try:
                fund_resp = ak.fund_open_fund_info(fund_code=fund_code, indicator='单位净值走势')
                if not fund_resp.empty:
                    latest_data = fund_resp.iloc[-1]
                    return {
                        'nav': float(latest_data['单位净值']),
                        'date': datetime.strptime(str(latest_data['净值日期']), '%Y%m%d')
                    }
            except:
                pass
            
            # 备用方案：从天天基金网爬取数据
            url = f'http://fund.eastmoney.com/{fund_code}.html'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找最新净值和日期
            nav_element = soup.find('span', class_='ui-font-large ui-color-red')
            date_element = soup.find('span', class_='ui-date')
            
            if nav_element and date_element:
                nav = float(nav_element.text)
                date_str = date_element.text.strip('()')
                date = datetime.strptime(date_str, '%Y-%m-%d')
                
                return {
                    'nav': nav,
                    'date': date
                }
            
            return None
        except Exception as e:
            print(f'获取基金 {fund_code} 净值失败: {e}')
            return None
    
    @staticmethod
    def get_fund_historical_navs(fund_code, days=30):
        """获取基金历史净值数据（最近N个交易日）"""
        try:
            # 尝试使用akshare库获取历史数据
            try:
                fund_resp = ak.fund_open_fund_info(fund_code=fund_code, indicator='单位净值走势')
                if not fund_resp.empty:
                    # 获取最近N个交易日的数据
                    # 由于akshare返回的可能包含非交易日数据，需要确保只返回有净值的日期
                    result = []
                    for _, row in fund_resp.tail(days*2).iterrows():
                        try:
                            date = datetime.strptime(str(row['净值日期']), '%Y%m%d')
                            nav = float(row['单位净值'])
                            result.append({'nav': nav, 'date': date})
                        except:
                            continue
                    
                    # 按日期升序排序并返回最近N个
                    result.sort(key=lambda x: x['date'])
                    return result[-days:] if len(result) >= days else result
            except Exception as e:
                print(f'使用akshare获取历史净值失败: {e}')
                
            # 备用方案：从天天基金网爬取历史数据
            url = f'http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code={fund_code}&page=1&per=100'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找净值表格
            table = soup.find('table', class_='w782')
            if not table:
                return []
            
            result = []
            rows = table.find_all('tr')[1:]  # 跳过表头
            
            # 解析表格数据
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:
                    try:
                        date_str = cells[0].text.strip()
                        nav_str = cells[1].text.strip()
                        
                        if date_str and nav_str:
                            date = datetime.strptime(date_str, '%Y-%m-%d')
                            nav = float(nav_str)
                            result.append({'nav': nav, 'date': date})
                    except Exception as e:
                        print(f'解析历史净值数据失败: {e}')
                        continue
                
                # 达到所需的天数则停止
                if len(result) >= days:
                    break
            
            return result
        except Exception as e:
            print(f'获取基金 {fund_code} 历史净值失败: {e}')
            return []