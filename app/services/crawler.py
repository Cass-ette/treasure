"""
爬虫服务：从天天基金网爬取基金净值
提取自 simple_app.py 的 update_fund_nav() 函数
"""
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta


def update_fund_nav(fund_code, _db=None, _Fund=None, _FundNavHistory=None):
    """
    爬取并更新基金净值（写入数据库）。
    _db / _Fund / _FundNavHistory 仅供测试注入，正常调用无需传递。
    """
    if _db is None:
        from app.extensions import db as _db
    if _Fund is None:
        from app.models import Fund as _Fund
    if _FundNavHistory is None:
        from app.models import FundNavHistory as _FundNavHistory

    from app.services.calculation import calculate_returns

    try:
        url = f"http://fund.eastmoney.com/{fund_code}.html"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/91.0.4472.124 Safari/537.36'
        }

        print(f"尝试爬取基金 {fund_code} 的净值数据，URL: {url}")
        response = requests.get(url, headers=headers, timeout=20)
        response.encoding = 'utf-8'
        print(f"服务器响应状态码: {response.status_code}")

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # ---- 获取基金名称 ----
            fund_name = None
            fund_name_elem = soup.find('div', class_='fundDetail-tit') or soup.find('h1')
            if fund_name_elem:
                fund_name_text = fund_name_elem.get_text(strip=True)
                name_match = re.search(r'([^\(]+)', fund_name_text)
                if name_match:
                    fund_name = name_match.group(1).strip()
                    print(f"提取到基金名称: {fund_name}")
            if not fund_name:
                meta = soup.find('meta', attrs={'name': 'keywords'})
                if meta and meta.get('content'):
                    kws = meta['content'].split(',')
                    if kws and len(kws) > 1:
                        fund_name = kws[0].strip()

            # ---- 获取基金类型 ----
            fund_type = None
            type_keywords = {
                '股票': '股票型', '混合': '混合型', '债券': '债券型',
                '货币': '货币型', '指数': '指数型',
                'QDII': 'QDII', 'ETF': 'ETF', 'LOF': 'LOF',
            }
            ft_elem = soup.find('div', class_='fundInfoItem', text=re.compile(r'基金类型'))
            if ft_elem:
                m = re.search(r'基金类型[:：]\s*(\S+)', ft_elem.get_text(strip=True))
                if m:
                    fund_type = m.group(1).strip()
            if not fund_type and fund_name:
                for kw, tn in type_keywords.items():
                    if kw in fund_name:
                        fund_type = tn
                        break
            if not fund_type:
                desc_meta = soup.find('meta', attrs={'name': 'description'})
                if desc_meta and desc_meta.get('content'):
                    for kw, tn in type_keywords.items():
                        if kw in desc_meta['content']:
                            fund_type = tn
                            break

            # ---- 查找净值元素（5种方式） ----
            nav_elem = None
            if not nav_elem:
                e = soup.find('dl', class_='dataItem01')
                if e:
                    nav_elem = e
            if not nav_elem:
                card = soup.find('div', class_='fundInfoItem')
                if card:
                    for t in card.find_all(text=re.compile(r'[0-9.]+')):
                        if t.parent and '单位净值' in t.parent.text:
                            nav_elem = t.parent
                            break
            if not nav_elem:
                e = soup.find('div', class_='dataOfFund')
                if e:
                    nav_elem = e
            if not nav_elem:
                tbl = soup.find('table', class_='w782')
                if tbl:
                    rows = tbl.find_all('tr')
                    if len(rows) > 1:
                        cells = rows[1].find_all('td')
                        if len(cells) > 1:
                            nav_elem = cells[1]
            if not nav_elem:
                e = soup.find('span', class_='ui-font-large')
                if e:
                    nav_elem = e
            if not nav_elem:
                e = soup.find('span', class_='fix_dwjz')
                if e:
                    nav_elem = e

            if nav_elem:
                nav_text = nav_elem.get_text(strip=True)
                print(f"找到净值元素，文本内容: {nav_text}")

                nav_match = re.search(r'单位净值[：:]\s*([0-9.]+)', nav_text)
                date_match = re.search(r'更新时间[：:]\s*([0-9-]+)', nav_text)

                if not nav_match:
                    m2 = re.search(r'单位净值\((\d{4}-\d{2}-\d{2})\)([0-9.]+)', nav_text)
                    if m2:
                        val = m2.group(2)
                        if len(val) > 8:
                            dp = val.find('.')
                            if dp > 0 and dp + 5 <= len(val):
                                val = val[:dp + 5]
                        nav_match = type('_', (), {'group': lambda s, x=1: val})()

                if not date_match:
                    date_match = re.search(r'更新日期：([0-9-]+)', nav_text) or \
                                 re.search(r'单位净值\((\d{4}-\d{2}-\d{2})\)', nav_text)

                if not nav_match and not date_match:
                    dm = re.search(r'单位净值\(([0-9-]+)\)', nav_text)
                    if dm:
                        date_match = dm
                        part = nav_text.split(dm.group(0))[1]
                        nm = re.search(r'(\d+\.\d{3,4})', part)
                        if nm:
                            nav_match = nm

                if not nav_match:
                    if '累计净值' in nav_text:
                        nav_text = nav_text.split('累计净值')[0]

                    fn_upper = (fund_name or '').upper()
                    if 'QDII' in fn_upper or '海外' in (fund_name or '') or '净值估算' in nav_text:
                        # QDII 特殊容器
                        container = soup.find('div', id='jjjz_gsjz')
                        if container:
                            for tbl in container.find_all('table'):
                                rows = tbl.find_all('tr')
                                if len(rows) > 1:
                                    cells = rows[1].find_all('td')
                                    if len(cells) > 1:
                                        try:
                                            fv = float(cells[1].get_text(strip=True))
                                            nav_match = type('_', (), {'group': lambda s, x=1: fv})()
                                            if cells[0] and not date_match:
                                                dt = cells[0].get_text(strip=True)
                                                if re.match(r'\d{4}-\d{2}-\d{2}', dt):
                                                    date_match = type('_', (), {'group': lambda s, x=1: dt})()
                                        except ValueError:
                                            pass
                                if nav_match:
                                    break
                        if not nav_match:
                            for tbl in soup.find_all('table'):
                                ths = tbl.find_all('th')
                                if ths and any('日期' in h.text for h in ths) and any('单位净值' in h.text for h in ths):
                                    rows = tbl.find_all('tr')
                                    if len(rows) > 1:
                                        cells = rows[1].find_all('td')
                                        if len(cells) > 1:
                                            try:
                                                fv = float(cells[1].get_text(strip=True))
                                                nav_match = type('_', (), {'group': lambda s, x=1: fv})()
                                                if cells[0] and not date_match:
                                                    dt = cells[0].get_text(strip=True)
                                                    if re.match(r'\d{4}-\d{2}-\d{2}', dt):
                                                        date_match = type('_', (), {'group': lambda s, x=1: dt})()
                                            except ValueError:
                                                pass
                                    if nav_match:
                                        break

                    if not nav_match:
                        nums = re.findall(r'\b[0-9]+\.[0-9]{3,4}\b', nav_text) or re.findall(r'[0-9.]+', nav_text)
                        for n in nums:
                            try:
                                fv = float(n)
                                if 0.1 <= fv <= 10:
                                    nav_match = type('_', (), {'group': lambda s, x=1: fv})()
                                    break
                            except ValueError:
                                continue

                # 从全页提取日期兜底
                if not date_match:
                    all_dates = re.findall(r'\d{4}-\d{2}-\d{2}', soup.get_text(strip=True))
                    if all_dates:
                        latest = sorted([datetime.strptime(d, '%Y-%m-%d') for d in all_dates], reverse=True)[0]
                        dt_str = latest.strftime('%Y-%m-%d')
                        date_match = type('_', (), {'group': lambda s, x=1: dt_str})()

                if not date_match:
                    from app.services.fund_service import FundService
                    today = datetime.now().date()
                    dt_str = today.strftime('%Y-%m-%d')
                    if not FundService.is_market_day(today):
                        for i in range(1, 8):
                            cd = today - timedelta(days=i)
                            if FundService.is_market_day(cd):
                                dt_str = cd.strftime('%Y-%m-%d')
                                break
                    date_match = type('_', (), {'group': lambda s, x=1: dt_str})()

                if nav_match and date_match:
                    latest_nav = float(nav_match.group(1))
                    nav_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                    print(f"成功提取净值: {latest_nav}, 日期: {nav_date}")

                    fund = _Fund.query.filter_by(code=fund_code).first()
                    if fund:
                        old_nav = fund.latest_nav
                        fund.latest_nav = latest_nav
                        fund.nav_date = nav_date
                        if fund_name and not fund.name:
                            fund.name = fund_name
                        if fund_type and (not fund.fund_type or fund.fund_type == '未知'):
                            fund.fund_type = fund_type
                        _db.session.commit()

                        if not _FundNavHistory.query.filter_by(fund_id=fund.id, date=nav_date).first():
                            _db.session.add(_FundNavHistory(fund_id=fund.id, nav=latest_nav, date=nav_date))
                            _db.session.commit()

                        if old_nav and old_nav != latest_nav:
                            calculate_returns(fund.id, old_nav, latest_nav, _db=_db)
                        return True
                    else:
                        new_fund = _Fund(
                            code=fund_code,
                            name=fund_name or f"基金{fund_code}",
                            fund_type=fund_type or '未知',
                            latest_nav=latest_nav,
                            nav_date=nav_date
                        )
                        _db.session.add(new_fund)
                        _db.session.commit()
                        print(f"成功创建新基金记录: {new_fund.name} ({new_fund.code})")
                        return True
                else:
                    print("未能从文本中提取有效的净值和日期")
            else:
                print("未能找到包含净值信息的元素")

        # ---- 备用数据源：新浪财经 ----
        try:
            print(f"尝试使用备用数据源爬取基金 {fund_code}")
            sina_url = f"http://finance.sina.com.cn/fund/quotes/{fund_code}/nav.shtml"
            sr = requests.get(sina_url, headers=headers, timeout=10)
            sr.encoding = 'utf-8'
            if sr.status_code == 200:
                ssoup = BeautifulSoup(sr.text, 'html.parser')
                ne = ssoup.find('div', class_='fundDetail-tit')
                if ne:
                    m = re.search(r'([0-9.]+)', ne.get_text(strip=True))
                    if m:
                        latest_nav = float(m.group(1))
                        from app.services.fund_service import FundService
                        today = datetime.now().date()
                        nav_date = datetime.now()
                        if not FundService.is_market_day(today):
                            for i in range(1, 8):
                                cd = today - timedelta(days=i)
                                if FundService.is_market_day(cd):
                                    nav_date = datetime.combine(cd, datetime.min.time())
                                    break

                        fund = _Fund.query.filter_by(code=fund_code).first()
                        if fund:
                            old_nav = fund.latest_nav
                            fund.latest_nav = latest_nav
                            fund.nav_date = nav_date
                            _db.session.commit()

                            if not _FundNavHistory.query.filter_by(fund_id=fund.id, date=nav_date).first():
                                _db.session.add(_FundNavHistory(fund_id=fund.id, nav=latest_nav, date=nav_date))
                                _db.session.commit()

                            if old_nav and old_nav != latest_nav:
                                calculate_returns(fund.id, old_nav, latest_nav, _db=_db)
                            print(f"从新浪财经成功获取净值: {latest_nav}")
                            return True
        except Exception as e:
            print(f"备用数据源爬取失败: {str(e)}")

        return False

    except Exception as e:
        print(f"爬取基金 {fund_code} 净值时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
