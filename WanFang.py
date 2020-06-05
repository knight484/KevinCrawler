import re
import time

import pymongo
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

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
        driver = webdriver.Chrome()
        driver.implicitly_wait(5)

        start = time.time()
        for e, url in enumerate(url_list):
            r = req_get(url, header=self.header, proxy=self.proxy)
            if not r:
                print(f"\r进度({e}/{len(url_list)})", end='')
                continue
            r.encoding = r.apparent_encoding
            soup = BeautifulSoup(r.text, 'lxml')

            paper = dict()
            try:
                paper['标题'] = soup.find('title').text
            except AttributeError:
                print(f"\r进度({e}/{len(url_list)})", end='')
                continue
            paper['url'] = url
            paper['uid'] = url
            if 'old' in url:
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
            elif 'med' in url:
                try:
                    paper['摘要'] = soup.find('div', class_="abstracts").text.strip('\n摘要： 更多')
                except AttributeError:
                    pass
                try:
                    items = soup.find('div', class_="table").find_all('div', class_='table-tr')
                except AttributeError:
                    print(f"\r进度({e}/{len(url_list)})", end='')
                    continue
                for i in items:
                    col = i.text.split('：')[0].strip().replace(' ', '')
                    value = re.sub(r'\s+', ',', i.text.split('：')[1].strip())
                    value = re.sub(r'\[\d+\]', '', value)
                    value = re.sub(r',+', ',', value)
                    paper[col] = value
            elif "?" in url:
                paper['摘要'] = soup.find('div', class_="abstract").text.strip('\n摘要： 更多')
                items = soup.find('ul', class_='info').find_all('li')
                for i in items:
                    key = i.text.split('：')[0].strip().replace(' ', '')
                    value = re.sub(r'\s+', ',', i.text.split('：')[1].strip())
                    value = re.sub(r'\[\d+\]', '', value)
                    value = re.sub(r',+', ',', value)
                    paper[key] = value
            elif soup.find('title').text == '万方数据知识服务平台':
                driver.get(url)
                try:
                    paper['标题'] = driver.find_element_by_class_name('detailTitleCN').text.strip()
                except NoSuchElementException:
                    continue
                items = driver.find_elements_by_css_selector('.detailList > div')
                for i in items:
                    key = i.text.split('：')[0].strip().replace(' ', '')
                    value = i.text.split('：')[1].strip()
                    paper[key] = value

            table.update_one({"uid": paper['uid']}, {"$set": paper}, True)
            end = time.time()
            spend = end - start
            unit_spend = spend / (e + 1)
            remain = (len(url_list) - e) * unit_spend
            print(f"\r进度({e}/{len(url_list)}), "
                  f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                  f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')

        driver.close()
        return None


if __name__ == '__main__':
    mongo = pymongo.MongoClient("mongodb://localhost:27017")
    db = mongo['万方']
    table = db['论文信息']