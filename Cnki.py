import logging
import random
import re
import time
from urllib.parse import unquote

import pymongo
from bs4 import BeautifulSoup
from pymongo.errors import WriteError
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, \
    TimeoutException

from Base import *
import logging
import random
import re
import time
from urllib.parse import unquote

import pymongo
from bs4 import BeautifulSoup
from pymongo.errors import WriteError
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, \
    TimeoutException

from Base import *

logging.captureWarnings(True)


class Cnki:

    def __init__(self, headers, cookies):
        self.header = {headers.split(': ')[0]: headers.split(': ')[1]}
        self.cookie = {}
        for i in cookies.split("; "):
            self.cookie[i.split('=')[0]] = i.split('=')[1]
        mongo = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = mongo['知网']
        self.proxy = get_proxies()

    def get_essay(self, keyword, ctl_code):

        table = self.db['文献信息']
        table.create_index('uid')

        params = dict()
        params['RecordsPerPage'] = 50
        params['QueryID'] = random.randint(1, 10)
        params['ID'] = ''
        params['turnpage'] = 1
        params['tpagemode'] = 'L'
        params['dbPrefix'] = 'SCDB'
        params['Fields'] = ''
        params['DisplayMode'] = 'listmode'
        params['PageName'] = 'ASP.brief_default_result_aspx'
        params['ctl'] = ctl_code
        params['Param'] = f"NVSM关键词 = '{keyword}'"
        params['isinEn'] = 1

        cur_pg = 1
        max_pg = 1
        start = time.time()
        while cur_pg <= max_pg:

            # 生成初始页链接并获取页面
            params['curpage'] = cur_pg
            url = 'https://kns.cnki.net/kns/brief/brief.aspx?'
            for p in params:
                url += f"&{p}={params[p]}"
            r = req_get(url, header=self.header, proxy=self.proxy, cookie=self.cookie)
            soup = BeautifulSoup(r.text, 'lxml')
            try:
                max_pg = int(soup.find('span', class_='countPageMark').text.split('/')[-1])
            except AttributeError:
                pass

            # 主循环
            items = soup.find('table', class_='GridTableContent').find_all('tr')[1:]
            for e, item in enumerate(items):

                # 获取数据
                essay = dict()
                try:
                    essay['title'] = item.find('a', class_='fz14').text
                except AttributeError:
                    continue
                essay['authors'] = item.find('td', class_='author_flag').text.strip().split(';')
                essay['journal'] = item.find('td', class_='author_flag').find_next_sibling().text.strip()
                essay['type'] = item.find_all('td', align='center')[1].text.strip()
                essay['cite'] = item.find('td', align='right').text.strip()
                essay['uid'] = essay['title']
                try:
                    essay['publication'] = item.find('td', align='center').text.strip()
                except AttributeError:
                    pass
                try:
                    essay['download'] = item.find('span', class_='downloadCount').text.strip()
                except AttributeError:
                    essay['download'] = ''
                if '' in essay['authors']:
                    essay['authors'].remove('')

                # 根据链接参数生成文献链接
                try:
                    essay[
                        'url'] = f"https://kns.cnki.net/KCMS/detail/{re.search(r'&URLID=(.+)&', item.find('a', class_='fz14')['href']).group(1)}.html"
                except AttributeError:
                    dbcode = re.search(r'DbCode=(.+?)&', item.find('a', class_='fz14')['href']).group(1)
                    dbname = re.search(r'DbName=(.+?)&', item.find('a', class_='fz14')['href']).group(1)
                    filename = re.search(r'FileName=(.+?)&', item.find('a', class_='fz14')['href']).group(1)
                    essay[
                        'url'] = f'https://kns.cnki.net/KCMS/detail/detail.aspx?dbcode={dbcode}&dbname={dbname}&filename={filename}'

                # 通过生成并跳转链接的方式, 获取作者链接及所在机构名
                essay['author_link'] = list()
                essay['affiliate'] = list()
                for u in item.find_all('a', class_='KnowledgeNetLink'):
                    if 'href' not in u.attrs:
                        continue
                    dbcode = re.search(r'sdb=(.+?)&', u['href']).group(1)
                    skey = re.search(r'skey=(.+?)&', u['href']).group(1)
                    code = re.search(r'code=(.+?)&', u['href']).group(1)
                    author_url = f'https://kns.cnki.net/kcms/detail/knetsearch.aspx?dbcode={dbcode}&sfield=au&skey={skey}&code={code}'
                    essay['author_link'].append(author_url)
                    author_r = req_get(author_url, header=self.header, proxy=self.proxy)
                    author_s = BeautifulSoup(author_r.text, 'lxml')
                    if author_s.find('p', class_='orgn'):
                        essay['affiliate'].append(author_s.find('p', class_='orgn').text)
                essay['author_link'] = list(set(essay['author_link']))
                essay['affiliate'] = list(set(essay['affiliate']))

                # 通过获取的参数, 生成期刊链接
                journal = item.find('td', class_='author_flag').find_next_sibling().find('a')
                if journal.name == 'a':
                    pcode = re.search(r'&DBCode=(.+?)&', journal['href']).group(1)
                    pykm = re.search(r'&BaseID=(.+?)&', journal['href']).group(1)
                    essay['journal_link'] = f'http://navi.cnki.net/KNavi/JournalDetail?pcode={pcode}&pykm={pykm}'

                # 保存数据
                table.update_one({"uid": essay["uid"]}, {"$set": essay}, True)
                end = time.time()
                spend = end - start
                unit_spend = spend / ((cur_pg - 1) * 50 + e + 1)
                remain = ((max_pg - cur_pg) * 50 + (len(items) - e)) * unit_spend
                print(
                    f"进度({cur_pg}/{max_pg})页({e}/{len(items)})条文献信息数据, "
                    f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                    f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.")
            cur_pg += 1


if __name__ == "__main__":
    h = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36'
    c = 'Ecp_ClientId=1200412222403053972; cnkiUserKey=88e5f366-e905-f1e7-17fa-e3240e67f653; Ecp_IpLoginFail=200522117.140.138.55; ASP.NET_SessionId=csboxgpludvgeolzt4zdpytf; SID_kns=123118; SID_klogin=125144; SID_crrs=125131; KNS_SortType=; _pk_ref=%5B%22%22%2C%22%22%2C1590131081%2C%22https%3A%2F%2Fwww.cnki.net%2F%22%5D; _pk_ses=*; SID_krsnew=125133; SID_kns_new=123113; SID_kcms=124105; RsPerPage=50'

    cnk = Cnki(headers=h, cookies=c)
    cnk.get_essay('肺动脉高压', '8ae6b600-3ac6-4534-b876-33412b9c6462')
