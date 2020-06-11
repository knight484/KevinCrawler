import logging
import logging
import random
import time
from urllib.parse import unquote

import bs4
import demjson
import pymongo
from bs4 import BeautifulSoup
from pymongo.errors import WriteError
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, \
    TimeoutException

from Base import *

logging.captureWarnings(True)


class MedSci:

    def __init__(self, headers, cookies):
        self.header = {headers.split(': ')[0]: headers.split(': ')[1]}
        self.cookie = {}
        for i in cookies.split("; "):
            self.cookie[i.split('=')[0]] = i.split('=')[1]
        mongo = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = mongo['梅斯医学']
        self.proxy = get_proxies()

    def get_news_info(self, keyword):
        table = self.db['咨询概览']
        table.create_index('uid')

        cur_pg = 1
        max_pg = 1
        start = time.time()
        e = 0
        while cur_pg <= max_pg:
            url = f'http://www.medsci.cn/search?page={cur_pg}&q={keyword}'
            r = req_get(url, header=self.header, proxy=self.proxy)
            if not r:
                time.sleep(5)
                continue
            soup = BeautifulSoup(r.text, 'lxml')
            max_pg = int(re.search(r'页码: \d+/(\d+)页', soup.find('span', class_='page-info-right').text).group(1))
            items = soup.find('div', id="medsciSiteSearch").find_all('div', class_='item')
            for item in items:
                news = dict()
                news['title'] = item.h2.text
                news['url'] = 'http://www.medsci.cn' + item.a['href']
                news['uid'] = re.search(r'id=(.+)', item.a['href']).group(1)
                news['abstract'] = item.find('p', class_='text-justify').text.strip()
                infos = [i.strip() for i in
                         item.find('p', style="color:rgba(117,117,117,.5); margin-top: 8px;").contents if
                         i is not None and '<span>' not in str(i)]
                if len(infos) == 3:
                    cols = ['source', 'keywords', 'date']
                elif len(infos) == 2:
                    cols = ['source', 'date']
                for col, info in zip(cols, infos):
                    news[col] = info

                table.update_one({"uid": news["uid"]}, {"$set": news}, True)
                e += 1
                end = time.time()
                spend = end - start
                unit_spend = spend / e
                remain = (max_pg * 15 - e) * unit_spend
                print(f"\r进度正在爬取第({cur_pg}/{max_pg})页的数据, 进度({e}/{max_pg * 15})页信息数据, "
                      f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                      f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')
            cur_pg += 1
        return None


if __name__ == "__main__":
    h = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'
    c = '_ga=GA1.2.1313902437.1587914675; _gid=GA1.2.1053623808.1591528765; UM_distinctid=1728e81b92945d-0c6a300523d25b-f7d123e-1fa400-1728e81b92a333; CNZZDATA1278894273=1572490412-1591526719-https%253A%252F%252Fwww.google.com%252F%7C1591526719'
    ms = MedSci(headers=h, cookies=c)
    ms.get_news_info('肾移植')
