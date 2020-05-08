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


class BaiduScholar:

    def __init__(self, headers, cookies):
        self.header = {headers.split(': ')[0]: headers.split(': ')[1]}
        self.cookie = {}
        for i in cookies.split("; "):
            self.cookie[i.split('=')[0]] = i.split('=')[1]
        mongo = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = mongo['百度学术']
        self.proxy = get_proxies()
        self.driver = webdriver.Chrome()

    def get_scholar_link(self, name_list, affl_keyword=None):
        table = self.db['学者网址']
        table.create_index('uid')

        self.driver.implicitly_wait(10)
        start = time.time()

        for e, name in enumerate(name_list):
            url = f'http://xueshu.baidu.com/usercenter/data/authorchannel?cmd=inject_page&author={name}&affiliate={affl_keyword}'
            self.driver.get(url)
            time.sleep(random.random() * 3)
            scholar_list = self.driver.find_elements_by_class_name("searchResultItem")
            for s in scholar_list:
                scholar = dict()
                scholar['作者姓名'] = s.find_element_by_class_name("personName").text.strip()
                scholar['作者机构'] = s.find_element_by_class_name("personInstitution").text.strip()
                scholar['发表文章'] = s.find_element_by_class_name("articleNum").text.strip()
                scholar['被引次数'] = s.find_element_by_class_name("quoteNum").text.strip()
                try:
                    scholar['研究领域'] = s.find_element_by_class_name("aFiled").text.strip()
                except NoSuchElementException:
                    pass
                scholar['url'] = s.find_element_by_class_name("personName").get_attribute('href')
                scholar['uid'] = scholar['url'].split('/')[-1]
                if scholar['作者姓名'] == name:
                    table.update_one({"uid": scholar["uid"]}, {"$set": scholar}, True)
                    end = time.time()
                    spend = end - start
                    unit_spend = spend / (e + 1)
                    remain = (len(name_list) - e - 1) * unit_spend
                    print(
                        f"\r进度({e + 1}/{len(name_list)})条咨询信息数据, "
                        f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                        f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')
        return None

    def get_scholar_detail(self, url_list):
        table = self.db['学者信息']
        table.create_index('uid')

        start = time.time()
        for e, url in enumerate(url_list):
            r = req_get(url, header=self.header, proxy=self.proxy)
            if not r:
                print(f'{e}/{len(url_list)}..', end='')
                continue
            r.encoding = r.apparent_encoding
            soup = BeautifulSoup(r.text, 'lxml')

            scholar = dict()
            scholar['url'] = url
            try:
                scholar['uid'] = soup.find('span', class_='p_scholarID_id').text.strip()
            except AttributeError:
                print(f'{e}/{len(url_list)}..', end='')
                continue
            scholar['姓名'] = soup.find('div', class_='p_name').text.strip()
            scholar['机构'] = soup.find('div', class_='p_affiliate').text.strip()
            scholar['浏览数'] = soup.find('div', class_='p_volume').text.strip().replace("人看过", "")
            try:
                scholar['领域'] = soup.find('span', class_='person_domain').text
            except AttributeError:
                pass
            for item in soup.find_all('li', class_='p_ach_item'):
                scholar[item.find('p').text] = item.find('p', class_='p_ach_num').text
            for item in soup.find_all('div', class_='pie_map_container'):
                scholar[item.find('div', class_='pieText').contents[0]] = item.find('p', class_="number").text
            for item in soup.find_all('div', class_="pieBox"):
                box_detail = dict()
                for i in item.find_all('p'):
                    box_detail[i.contents[0]] = i.find('span', class_="boxnum").text
                scholar[item.h3.contents[0] + "数据"] = box_detail
            try:
                scholar['引用数据'] = [(x['year'], x['num']) for x in
                                   eval(re.search(r'lineMapCitedData = (.+);', r.text).group(1))]
            except AttributeError:
                pass
            try:
                scholar['成果数据'] = [(x['year'], x['num']) for x in
                                   eval(re.search(r'lineMapAchData = (.+);', r.text).group(1))]
            except AttributeError:
                pass

            table.update_one({"uid": scholar["uid"]}, {"$set": scholar}, True)
            end = time.time()
            spend = end - start
            unit_spend = spend / (e + 1)
            remain = (len(url_list) - e - 1) * unit_spend
            print(
                f"\r{url}, 进度({e + 1}/{len(url_list)})条咨询信息数据, "
                f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')
        return None

    def get_essay_link(self, url_list):
        table = self.db['论文网址']
        table.create_index('uid')

        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(3)
        start = time.time()
        for e, url in enumerate(url_list):
            self.driver.get(url)
            go_next = True
            n = 0
            while go_next:
                time.sleep(3)
                items = self.driver.find_elements_by_class_name("result")
                for i in items:
                    try:
                        title = i.find_element_by_tag_name('a')
                        essay = dict()
                        essay['url'] = title.get_attribute('href')
                        essay['学者url'] = url
                        essay['学者code'] = i.find_element_by_class_name('p_scholarID_id').text
                        essay['标题'] = title.text.strip()
                        essay['uid'] = essay['标题']
                    except StaleElementReferenceException:
                        continue
                    essay['作者'] = ''
                    col_list = [
                        ('年份', '.res_year'),
                        ('作者', '.res_info > span:nth-child(2)'),
                        ('期刊', '.res_info > a'),
                        ('被引量', '.cite_cont'),
                    ]
                    for col, rule in col_list:
                        try:
                            essay[col] = i.find_element_by_css_selector(rule).text.strip()
                        except (NoSuchElementException, StaleElementReferenceException):
                            pass
                    if essay['作者'].startswith("被引量"):
                        essay['作者'] = ''
                    n += 1
                    t1 = time.time()
                    table.update_one({"uid": essay["uid"]}, {"$set": essay}, True)
                    end = time.time()
                    spend = end - start
                    unit_spend = spend / (e + 1)
                    remain = (len(url_list) - e - 1) * unit_spend
                    print(
                        f"\r{url}, 进度({e + 1}/{len(url_list)}), 从该作者获得{n}条文献信息数据, 本次存储用时{round(end - t1, 4)}秒，"
                        f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                        f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')

                try:
                    nxt_btn = self.driver.find_element_by_class_name('res-page-next')
                    if nxt_btn.get_attribute('style') == "display: none;":
                        go_next = False
                    else:
                        nxt_btn.click()
                except NoSuchElementException:
                    go_next = False
        return None

    def get_essay_detail(self, url_list):
        table = self.db['论文信息']
        table.create_index('uid')

        start = time.time()
        for e, url in enumerate(url_list):
            r = req_get(url, header=self.header, proxy=self.proxy)
            if not r:
                print(f'{e}/{len(url_list)}..', end='')
                continue
            soup = BeautifulSoup(r.text, 'lxml')
            essay = dict()
            try:
                essay['标题'] = soup.find('h3').text.strip()
            except AttributeError:
                print(f"\r进度({e + 1}/{len(url_list)})", end='')
                continue

            try:
                essay['来源'] = re.search(r'来自\s+(\S+)', soup.find('div', class_="love_wr").text.strip()).group(1)
            except AttributeError:
                pass

            try:
                essay['喜欢'] = re.search(r'喜欢\s+(\S+)', soup.find('div', class_="love_wr").text.strip()).group(1)
            except AttributeError:
                pass

            try:
                essay['阅读量'] = re.search(r'阅读量：\s+(\S+)', soup.find('div', class_="love_wr").text.strip()).group(1)
            except AttributeError:
                pass

            try:
                for item in soup.find('div', class_="love_wr").find_next_siblings('div'):
                    col = item.text.split('：')[0].strip()
                    value = item.text.split('：', 1)[1].strip() if item.text.split('：', 1) else '0'
                    essay[col] = value.replace('\n展开\ue634', '')
            except AttributeError:
                pass

            try:
                for item in soup.find('div', class_="allversion_content").find_all('a'):
                    key_name = item.text.strip()
                    if key_name not in essay.keys() and key_name != "查看更多" and "(" not in key_name:
                        key_name = key_name.replace('.', '_')
                        essay[key_name] = item['href']
            except (AttributeError, KeyError):
                pass

            try:
                essay['期刊'] = soup.find('a', class_="journal_title")['title']
                essay['期刊网址'] = 'http://xueshu.baidu.com' + soup.find('a', class_="journal_title")['href']
                essay['期次'] = soup.find('div', class_="journal_content")['title']
            except (AttributeError, TypeError, KeyError):
                pass

            try:
                string = soup.find('p', class_="author_text").find('a')['href']
                string = re.search(r'%29%20((%[0-9A-Z]{2})+)', string).group(1)
                essay['机构'] = unquote(string, encoding='UTF-8')
            except AttributeError:
                pass

            essay['uid'] = essay['标题']
            essay['url'] = url
            t1 = time.time()
            try:
                table.update_one({"uid": essay["uid"]}, {"$set": essay}, True)
            except WriteError:
                print(f"\r进度({e}/{len(url_list)}", end='')
                continue
            end = time.time()
            spend = end - start
            unit_spend = spend / (e + 1)
            remain = (len(url_list) - e - 1) * unit_spend
            print(
                f"\r进度({e + 1}/{len(url_list)}), 本次存储用时{round(end - t1, 4)}秒，"
                f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')
        return None


if __name__ == "__main__":
    import pandas as pd

    db = pymongo.MongoClient("mongodb://localhost:27017")
    d1 = list(pd.read_excel('HCP list_0414.xlsx', sheet_name=0)['HCP '])
    d2 = list(pd.read_excel('HCP list_0414.xlsx', sheet_name=1)['姓名'])
    names = list(set(d1 + d2))
    got = db['百度学术']['学者网址'].aggregate([
        {"$group": {"_id": '$作者姓名', "count": {"$sum": 1}}},
        {"$match": {"count": {"$eq": 1}}}
    ])
    got = [g["_id"] for g in got]
    names = [n for n in names if n in got]

    h = "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36"
    c = "Hm_lvt_f28578486a5410f35e6fbd0da5361e5f=1576123001; BAIDUID=3179CBBC74CC1AB8C9047E47521B587F:FG=1; PSTM=1586876295; BIDUPSID=1AAB03EE9D09AB07E4AB9BCFA3E6C96A; BDRCVFR[w2jhEs_Zudc]=mbxnW11j9Dfmh7GuZR8mvqV; delPer=0; BDSVRTM=10; BD_HOME=0; H_PS_PSSID=; Hm_lvt_d0e1c62633eae5b65daca0b6f018ef4c=1587181956; Hm_lpvt_d0e1c62633eae5b65daca0b6f018ef4c=1587181956"
    cr = BaiduScholar(headers=h, cookies=c)
    while True:
        try:
            cr.get_scholar_link(names, affl_keyword='医院')
            break
        except TimeoutException:
            cr.driver.close()
