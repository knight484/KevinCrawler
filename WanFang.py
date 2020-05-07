import re
import time

import pymongo
from bs4 import BeautifulSoup

from Base import *


class WanFang:
    def __init__(self, headers, cookies):
        self.header = {headers.split(': ')[0]: headers.split(': ')[1]}
        self.cookie = {}
        for i in cookies.split("; "):
            self.cookie[i.split('=')[0]] = i.split('=')[1]
        mongo = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = mongo['万方']
        self.proxy = get_proxies()

    def get_paper_id(self, keyword=None):
        table = self.db['期刊论文']
        for p in range(100):
            url = f'http://www.wanfangdata.com.cn/search/searchList.do?searchType=perio&showType=detail&pageSize=50&searchWord={keyword}&isTriggerTag=&page={p + 1}'
            r = requests.get(url, headers=self.header, cookies=self.cookie)
            soup = BeautifulSoup(r.text, 'lxml')
            documents = soup.find_all('div', class_='ResultList')
            for d in documents:
                doc = dict()
                doc['名称'] = d.find('div', class_='title').find('a').text
                doc['重定位网址'] = 'http://www.wanfangdata.com.cn/' + d.find('div', class_='title').find('a')['href']
                doc['类型'] = d.find('span', class_='resultResouceType').text.strip('[]')
                doc['作者'] = re.sub(r'\[.+\]', '', d.find('div', class_='author').text).strip().replace('\n', ',')
                doc['刊名'] = d.find('div', class_='Source').text.strip()
                doc['核心'] = d.find('div', class_='Label periodical_label').text.strip().replace('\n', ',')
                doc['刊期'] = d.find('div', class_='Volume').text.strip()
                if d.find('div', class_='summary'):
                    doc['摘要'] = d.find('div', class_='summary').text.replace('摘要：', '')
                if d.find('div', class_='Keyword'):
                    doc['关键词'] = d.find('div', class_='Keyword').text.strip().replace('\n', ',')
                result = d.find('div', class_='result_new_operaRight').find_all('li')
                for res in result:
                    try:
                        txt = res.find('a').text.strip()
                    except AttributeError:
                        continue
                    doc[txt.split('：')[0]] = txt.split('：')[1]

                table.update_one({"重定位网址": doc['重定位网址']}, {"$set": doc}, True)
            print(f'\r进度:{p}%...', end='')
            if p > int(soup.find('span', class_='searchPageWrap_all').text):
                break

    def get_paper_info(self, url_list):
        table = self.db['论文信息']
        table.create_index('uid')

        start = time.time()
        for e, url in enumerate(url_list):
            r = req_get(url, header=self.header, proxy=self.proxy)
            if not r:
                print(f"\r进度({e}/{len(url_list)})", end='')
                continue
            soup = BeautifulSoup(r.text, 'lxml')

            paper = dict()
            try:
                paper['标题'] = soup.find('title').text
            except AttributeError:
                print(f"\r进度({e}/{len(url_list)})", end='')
                continue
            paper['url'] = url
            paper['uid'] = url
            if 'old' not in url:
                try:
                    paper['摘要'] = soup.find('div', class_="abstract").find('div').text.strip('摘要： ')
                except AttributeError:
                    pass
                try:
                    items = soup.find('ul', class_="info").find_all('li')
                except AttributeError:
                    print(f"\r进度({e}/{len(url_list)})", end='')
                    continue
                for i in items:
                    col = i.find('div', class_="info_left").text.strip().strip(':：').replace(' ', '')
                    value = re.sub(r'\s+', ',', i.find('div', class_="info_right").text.strip())
                    paper[col] = value
            else:
                try:
                    paper['摘要'] = soup.find('div', class_="abstract").find('div', class_="text").text.strip('摘要： ')
                except AttributeError:
                    pass
                try:
                    items = soup.find('div', class_='fixed-width baseinfo-feild').find_all('div', class_="row")
                except AttributeError:
                    print(f"\r进度({e}/{len(url_list)})", end='')
                    continue
                for i in items:
                    col = i.find('span', class_="pre").text.strip().strip(':：').replace(' ', '')
                    value = re.sub(r'\s+', ',', i.find('span', class_="text").text.strip())
                    paper[col] = value
            table.update_one({"uid": paper['uid']}, {"$set": paper}, True)
            end = time.time()
            spend = end - start
            unit_spend = spend / (e + 1)
            remain = (len(url_list) - e) * unit_spend
            print(f"\r进度({e}/{len(url_list)}), "
                  f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                  f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')
        return None


if __name__ == '__main__':
    db = pymongo.MongoClient("mongodb://localhost:27017")
    table = db['百度学术']['论文信息']
    urls = table.distinct('万方')
    got = db['万方']['论文信息'].distinct('url')
    urls = [u for u in urls if u not in got]

    header = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'
    cookie = 'zh_choose=n; Hm_lvt_838fbc4154ad87515435bf1e10023fab=1587457098,1587984078,1587992753,1588151893; firstvisit_backurl=http%3A//www.wanfangdata.com.cn; SEARCHHISTORY_0=UEsDBBQACAgIAEyKnVAAAAAAAAAAAAAAAAABAAAAMO2baW8bRRjHv4ulrUAKyRw7x0aKkDeOncNO%0AnMRuEyOENt61vY5jO%2BvbqFKLSluCClTQQ7SCqhItCFEq%2BoIWCv0wxE7yLRg7rUrc7ESgJF2yfZXZ%0A0%2Fv%2FzfXMf56892GgaqwUrFljzQqMFmuFwlDANgOjgWRIT%2BZBKIM4DQwFahXLmTJf3FCxDCedS7TK%0A4hEoLjoF8UCuWi2Pjow0Go3hhlHMGMWsaVSN4XRpbThdHNl95PmfqF2pDpuld1%2B%2BZ8woFE5VcqVG%0A%2F%2BBU2chai3bbGkPg1O5NZ0qOOaZMEEUHij6uTFAlGFY0VZnQFB0pHJ6yKwnHzmYtJ2Fkx8QXW82y%0AY1Uqdqkovq3z8Gn35692fjkvLlT7nx3o3v62c3njr3PnOz%2Fd2%2FzjiihsPv16%2B8GDXuHxl53LP4jC%0A1v2r3Y1z3Y3vOlc3Xh5e%2FqL7zW1x2L1zqXPpYq%2Fw6Nr2%2FQu9V91%2B2L3%2BpPPshihv37%2B4c%2Fdq7%2BSt%0APzef3BM%2FXKythUu1oqCoUq4NBdKOZVSthN0DDwmnDEDEiOB9dsitUjhv5ccXwYyqQWmloBeV8hz4%0AglWpFaojWasaNOtGMW2Zi%2F3zvUro8RhrZMq1lYJdyb1Tthy79IHhVO20Iaqk6ohvzLbGNh%2F%2FvnP3%0A5uhb2x%2F91tn4fvvCJzs%2F3ux89unbg6Ql9%2B0Bv4cHZEL8K0CIxoCmQaHVHYgxzVNqOp4gKvEJEK4K%0Are5ASCKk102TEwz8AgQJre5AFsKGNg1QWMPIJ0AYF1rdgQSb4ZiTis1xVfMLECy0ugNJraD66mo5%0Ag7BfBlUGhVZ3IE2d1UutSgwRvwChVGh1B7I23yZOmc5pUB4LnSAgUGh1BzIZM2rRSuQ08gsPMcUg%0ACQ84E8HotB1l3C9hiIqFVncg6zOhcG02gZCKfQIEq0KrO5DGFNQj0WCVUr%2FEZVCMqpK4rJjJxvNm%0AZY5Qv3QZwIVWdyDzKl1lpfF5n0RlXKMASKIyWk%2B3krlpACk7Dv%2BhD2c%2FB4IMOBBc4UjRgz0rggeV%0AIO%2BfURWu9ayIoK5ovH9pQuG63JMY4HggRrQ%2FRowEIXeMeK0VjZFanYFjsXEGMJpW1bAL%2F4CJoIbJ%0AXqBM0bGi0RfeTrh3RmMKJ3vx9V8yBgEY5Lj16Hrn4bOtGx9LCe7%2B8r4ImYYEHclclgzG1u14ijD1%0AJCCkhw6QcCjYSFyrVGVKXW6nIeceAKiC%2FwTv0KmpFAsg7tT0YGWpgJttAt9Qe0kNi1kUSqg5JBUC%0AyUwEHmAIHhI108o6luWObdC%2FPjxsu7b1gK0Mwau%2Bco8awgzKXMPFWajX8gYnx2P2%2F0%2BoASiGNsnE%0AkB%2FPxaz8dBzJncXj6aCDzDwVp1ANaypAElcyzHPNlYXxMpavF49it8krJF%2FPXhTClO8XoVMVQAiw%0AZEk7bdjrZi2%2FhoHcJjzaHcI3dSXqCjOsiWpwr6uyEddy1MpBTywDvD1WqQAgKFsQWHPzswBXZtTj%0Ab%2FdeIemx9q8iLgJqSfufncJ6srhaYPx1zNXHEdn8mzCa9iZjgcKdF7LNDIC4RlQvLD68QU0EhAgI%0AIO7UzCYwYzOoiIgXnAKvUEMqFEAki4%2Fptpmu0Sg5wBr32UJXJUTmn6%2BjdpStL7OD8ho870odvrGi%0AEWkChB3W9HQ8UvVEczsER%2FQI%2FDwOZE0vhxM2ihgJEXOeDIJHYCpzoAo8kt2edqpYjVoponlhqvD6%0AJocKBSdJQA7C0eBsLEWZXzZXgSouSTZXQ9WmvcQtiPyy%2FQ6x0CrxKgr17Ew%2BN0WwvLudHCCICa3u%0AQCIQZBdaobxK%2FZLjhZnQ6g5kaqmIx%2BeXyyrzS06Tqgmt7kBiaRqGIi7nzCcZCSJsFFolSV6zk8kz%0A2RbnvukylHBZl9GT7YXJHG0T6Jdpl3KhVZIWmSguNRfLeeabFsIwk7WQ1UijvByuU%2BqbMYT1tLoD%0AKcXSicJq6AzBcl%2Ft5ADhUGh1BzIxpcfTZJIw3%2BRFcsRki2s9JoJ3mKYY%2ByUO4URolSQCmo0MdIqL%0AmPsldNeQ0CrZKm%2FH4%2FPJ0jxTjzoz8rkboCmaruisZ6LwsBIE%2FbV%2FSNFI798weVDR2CCRnVu%2Fbn1%2B%0Ap3PlWnfjhje2jiBB9BXaYmyCGiAC5Nn3%2FwZQSwcI9w%2F7GTcGAAAJOwAA%0A; Hm_lpvt_838fbc4154ad87515435bf1e10023fab=1588151905'
    cr = WanFang(headers=header, cookies=cookie)
    cr.get_paper_info(url_list=urls)