import requests
from bs4 import BeautifulSoup
from datetime import datetime
import akshare as ak
import requests

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