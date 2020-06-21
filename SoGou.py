import random
import re
import time
import warnings
import requests
import pymongo
from bs4 import BeautifulSoup
import pandas as pd

from Base import *

warnings.filterwarnings("ignore")


class SoGou:

    def __init__(self, headers, cookies):
        self.header = {headers.split(': ')[0]: headers.split(': ')[1]}
        self.cookie = {}
        for i in cookies.split("; "):
            self.cookie[i.split('=')[0]] = i.split('=')[1]
        mongo = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = mongo['搜狗']
        self.proxy = get_proxies()

    def get_wechat_id(self, keyword):

        table = self.db['微信']
        table.create_index('uid')

        n = 1
        t1 = int()
        start = time.time()
        while True:
            url = f'https://weixin.sogou.com/weixin?query={keyword}&_sug_type_=&s_from=input&_sug_=n&type=2&page={n}&ie=utf8'
            r = req_get(url, header=self.header, cookie=self.cookie)
            time.sleep(random.random())
            soup = BeautifulSoup(r.text, 'lxml')

            items = soup.find('ul', class_="news-list").find_all('li')
            for item in items:
                wc = dict()
                wc['link'] = 'https://weixin.sogou.com' + item.a['href']
                wc['title'] = item.h3.text.strip()
                wc['abstract'] = item.p.text.strip()
                wc['public_account'] = item.find('a', class_='account').text.strip()
                d = time.localtime(int(re.search(r'(\d+)', item.find('span', class_="s2").text).group(1)))
                wc['date'] = f"{d.tm_year}.{d.tm_mon}.{d.tm_mday}"
                wc['uid'] = wc['title'] + ">" + wc['public_account']
                t1 = time.time()
                table.update_one({"uid": wc["uid"]}, {"$set": wc}, True)
            end = time.time()
            spend = end - start
            print(
                f"\r{url}, 进度..获得{n * 10}条文献信息数据, 本次存储用时{round(end - t1, 4)}秒，"
                f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, ", end='')
            if soup.find('a', id='sogou_next'):
                n += 1
            else:
                break
        return None

    def get_zhihu_id(self, keyword):
        table = self.db['知乎']
        table.create_index('uid')

        # 爬取数据
        n = 0
        start = time.time()
        for cur_pg in range(1, 11):
            url = f'http://www.sogou.com/sogou?insite=zhihu.com&query={keyword}&page={cur_pg}&ie=utf8'
            r = req_get(url, header=self.header, proxy=self.proxy)
            if not r:
                continue
            time.sleep(random.random())
            soup = BeautifulSoup(r.text, 'lxml')

            items = soup.find_all('div', class_='vrwrap')
            for item in items:
                zh = dict()
                try:
                    zh['source'] = 'https://www.sogou.com' + item.a['href']
                except TypeError:
                    continue
                zh['url'] = re.search(r'\("(.+)"\)',
                                      req_get(zh['source'], header=self.header, proxy=self.proxy).text).group(1)
                zh['title'] = item.h3.text.strip()
                try:
                    zh['answer'] = re.search(r'([\d.]+万?)个回答', item.text).group(1)
                except AttributeError:
                    pass
                try:
                    zh['follow'] = re.search(r'([\d.]?万?)人关注', item.text).group(1)
                except AttributeError:
                    pass
                try:
                    zh['read'] = re.search(r'([\d.]+万?)次浏览', item.text).group(1)
                except AttributeError:
                    pass
                try:
                    _like = re.search(r'(\d+)', item.i.text).group(1)
                    zh['like'] = int(_like) if '万' not in str(_like) else int(float(_like.replace('万', '')) * 10000)
                except AttributeError:
                    pass
                zh['type'] = '文章' if '/p/' in zh['url'] else '问答' if '/question/' in zh['url'] else '其它'
                try:
                    zh['publish'] = re.search(r'发布于 (\d{4}-\d{2}-\d{2})',
                                              req_get(zh['url'], header=self.header, proxy=self.proxy).text).group(1)
                except AttributeError:
                    zh['publish'] = re.search(r'(\d{4}-\d{1,2}-\d{1,2})', item.text).group(1)
                zh['uid'] = zh['url']
                t1 = time.time()
                table.update_one({"uid": zh['uid']}, {"$set": zh}, True)
                end = time.time()
                spend = end - start
                print(
                    f"\r{url}, 进度..获得{n}条文献信息数据, 本次存储用时{round(end - t1, 4)}秒，"
                    f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, ", end='')
                n += 1
            cur_pg += 1

        return None


if __name__ == "__main__":
    c = 'CXID=8FD1DB73CBFDAF416B04444F6E40BE6E; SUID=456B58654B238B0A5DCAD9F4000B5057; SUV=0097AE23DE43C1495DDCA4EC321DC510; wuid=AAGiE/VHLgAAAAqLMXUfoQ0AGwY=; ABTEST=0|1587440623|v1; weixinIndexVisited=1; ad=hyllllllll2Wu@LElllllVfO7B9lllllBqla9lllllwlllllpklll5@@@@@@@@@@; SNUID=D2CA91A4C2C76543D683741BC2978CD0; IPLOC=CN3100; JSESSIONID=aaaRK2aSO-I0G859fZRgx; LSTMV=315%2C32; LCLKINT=3767; sct=8; ppinf=5|1588254265|1589463865|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZToyMzolRTIlOUMlQThTYWxseSVFMiU5QyVBOHxjcnQ6MTA6MTU4ODI1NDI2NXxyZWZuaWNrOjIzOiVFMiU5QyVBOFNhbGx5JUUyJTlDJUE4fHVzZXJpZDo0NDpvOXQybHVORy1DNXhWWHIzZVROWEh2UzhiXzRrQHdlaXhpbi5zb2h1LmNvbXw; pprdig=fwxOEPRquXlnBDBDEwYSwgs7IUHCdswiNGVqFf2Cy_cDyBqebprx9OqwpXA0Hz1wXaTQ_eJmqvw7g55HyTsB64acv1et6vDR9vGEoR21lD5HBEhoW9CH3kZqZQhWXkV2LFS3vcbpErTCz_IeSV9LZCGVH-137KBZmmqH8Y8tqBY; sgid=19-47731999-AV6q1jkeJ5E4icvrheUpAmuk; ppmdig=15882542650000005657b7c44e04eb5dd0530933a2c6b52d'
    h = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36'

    sg = SoGou(headers=h, cookies=c)
    sg.get_zhihu_id('python')
