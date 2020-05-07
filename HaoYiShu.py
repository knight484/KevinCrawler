import datetime as dt
import logging
import re
import time

import pymongo
import demjson
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

from Base import *

logging.captureWarnings(True)


class HaoYiShu:
    def __init__(self, headers, cookies):
        self.header = {headers.split(': ')[0]: headers.split(': ')[1]}
        self.cookie = {}
        for i in cookies.split("; "):
            self.cookie[i.split('=')[0]] = i.split('=')[1]
        self.proxy = get_proxies()
        mongo = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = mongo['好医术']

    def get_open_id(self):
        table = self.db['公开课网址']
        table.create_index('uid')

        url = 'https://www.haoyishu.org/web/course/openCourse'
        r = req_get(url, header=self.header, proxy=self.proxy)
        soup = BeautifulSoup(r.text, 'lxml')
        max_page = int(soup.find_all('li', class_='number')[-1].text)

        start = time.time()
        n = 0
        for i in range(max_page):
            url = f'https://www.haoyishu.org/api/video/open/list/403010/{i + 1}?sourceId=0&typeId=0&departmentId=0&website=true'
            r = req_get(url=url, header=self.header, proxy=self.proxy)
            contents = demjson.decode(r.text)
            videos = contents['data']['list']

            for video in videos:
                video['url'] = f'https://www.haoyishu.org/web/videoplay/open?albumId={video["albumId"]}'
                video['uid'] = video['albumId']
                table.update_one({"uid": video["uid"]}, {"$set": video}, True)
                n += 1
                end = time.time()
                spend = end - start
                unit_spend = spend / (i + 1 / max_page)
                remain = (max_page - i - 1 / max_page) * unit_spend
                print(f"\r进度({i + 1}/{max_page}), 获得{n}条视频数据, "
                      f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                      f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')

    def get_vip_id(self):
        table = self.db['会员课网址']
        table.create_index('uid')

        url = 'https://www.haoyishu.org/web/course/vipCourse'
        r = req_get(url, header=self.header, proxy=self.proxy)
        soup = BeautifulSoup(r.text, 'lxml')
        max_page = int(soup.find_all('li', class_='number')[-1].text)

        start = time.time()
        n = 0
        for i in range(max_page):
            url = f'https://www.haoyishu.org/api/video/vip/list/403010/{i + 1}?sourceId=0&typeId=0&departmentId=0&website=true'
            r = req_get(url=url, header=self.header, proxy=self.proxy)
            contents = demjson.decode(r.text)
            videos = contents['data']['list']

            for video in videos:
                video['url'] = f'https://www.haoyishu.org/web/videoplay/vip?albumId={video["albumId"]}'
                video['uid'] = video['albumId']
                table.update_one({"uid": video["uid"]}, {"$set": video}, True)
                n += 1
                end = time.time()
                spend = end - start
                unit_spend = spend / (i + 1 / max_page)
                remain = (max_page - i - 1 / max_page) * unit_spend
                print(f"\r进度({i + 1}/{max_page}), 获得{n}条视频数据, "
                      f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                      f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')


if __name__ == "__main__":
    h = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36'
    c = 'gr_user_id=df512dd0-f7c1-4210-a576-0e2ca3f3309c; grwng_uid=e9403df9-4d2d-46a8-8336-9f8927c61f69; Hm_lvt_b8d21f481877d7af7d19f0ee88d98f33=1588320918; 87f7e3c4c896ecf7_gr_session_id=a7014c54-1b75-4c79-8b9e-215a8cd065b8; 87f7e3c4c896ecf7_gr_session_id_a7014c54-1b75-4c79-8b9e-215a8cd065b8=true; sid=s%3AUGHMivjOzKRPETounjfpfupP1RnZWAqn.GaL3tsoFNkc9eL0xLiHRnGVg69uAsekT9psgJwlduOQ; Hm_lpvt_b8d21f481877d7af7d19f0ee88d98f33=1588479277'

    hys = HaoYiShu(headers=h, cookies=c)
    hys.get_open_id()
    hys.get_vip_id()
