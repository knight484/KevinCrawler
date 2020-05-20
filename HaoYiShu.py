import logging
import time

import demjson
import pymongo
from bs4 import BeautifulSoup

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

        url = 'https://www.haoyishu.org/web/video/open'
        r = req_get(url, header=self.header, proxy=self.proxy)
        soup = BeautifulSoup(r.text, 'lxml')
        max_type = len(soup.find('ul', class_='condition_list').find_all('li', style='display:;'))

        start = time.time()
        n = 0
        for j in range(1, max_type):
            url = f'https://www.haoyishu.org/api/v2/open/list/0/1?sourceId=0&typeId=0&departmentId={j}&website=true'
            r = req_get(url=url, header=self.header, proxy=self.proxy)
            contents = demjson.decode(r.text)
            max_page = contents['data']['pageCount']

            for i in range(max_page):
                url = f'https://www.haoyishu.org/api/v2/open/list/0/{i + 1}?sourceId=0&typeId=0&departmentId={j}&website=true'
                r = req_get(url=url, header=self.header, proxy=self.proxy)
                contents = demjson.decode(r.text)
                videos = contents['data']['list']

                for video in videos:
                    video['url'] = f'https://www.haoyishu.org/web/video/open/{video["albumId"]}'
                    video['uid'] = video['albumId']
                    video['departmentId'] = j
                    del video['article']

                    table.update_one({"uid": video["uid"]}, {"$set": video}, True)
                    n += 1
                    end = time.time()
                    spend = end - start
                    unit_spend = spend / (i + 1 / max_page)
                    remain = (max_page - i - 1 / max_page) * unit_spend
                    print(f"\r正在进行'第{j}类科室'的信息爬取，进度({i + 1}/{max_page}), 获得{n}条视频数据, "
                          f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                          f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')

    def get_vip_id(self):
        table = self.db['会员课网址']
        table.create_index('uid')

        url = 'https://www.haoyishu.org/web/video/vip'
        r = req_get(url, header=self.header, proxy=self.proxy)
        soup = BeautifulSoup(r.text, 'lxml')
        # max_page = int(soup.find_all('li', class_='number')[-1].text)
        max_type = len(soup.find('ul', class_='condition_list').find_all('li'))

        start = time.time()
        n = 0
        for j in range(1, max_type):
            url = f'https://www.haoyishu.org/api/v2/vip/list/0/1?sourceId=0&typeId=0&departmentId={j}&website=true'
            r = req_get(url=url, header=self.header, proxy=self.proxy)
            contents = demjson.decode(r.text)
            max_page = contents['data']['pageCount']

            for i in range(max_page):
                url = f'https://www.haoyishu.org/api/v2/vip/list/0/{i + 1}?sourceId=0&typeId=0&departmentId={j}&website=true'
                r = req_get(url=url, header=self.header, proxy=self.proxy)
                contents = demjson.decode(r.text)
                videos = contents['data']['list']

                for video in videos:
                    video['url'] = f'https://www.haoyishu.org/web/video/vip/{video["albumId"]}'
                    video['uid'] = video['albumId']
                    video['departmentId'] = j
                    del video['article']

                    table.update_one({"uid": video["uid"]}, {"$set": video}, True)
                    n += 1
                    end = time.time()
                    spend = end - start
                    unit_spend = spend / (i + 1 / max_page)
                    remain = (max_page - i - 1 / max_page) * unit_spend
                    print(f"\r正在进行'第{j}类科室'的信息爬取，进度({i + 1}/{max_page}), 获得{n}条视频数据, "
                          f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                          f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')

    def get_case_id(self):
        table = self.db['案例课网址']
        table.create_index('uid')

        url = 'https://www.haoyishu.org/web/video/case'
        r = req_get(url, header=self.header, proxy=self.proxy)
        soup = BeautifulSoup(r.text, 'lxml')
        # max_page = int(soup.find_all('li', class_='number')[-1].text)
        max_type = len(soup.find('ul', class_='stateList').find_all('li'))

        start = time.time()
        n = 0
        for j in range(1, max_type):
            url = f'https://www.haoyishu.org/api/v2/case/list/0/1?sourceId=0&typeId=0&departmentId={j}&website=true'
            r = req_get(url=url, header=self.header, proxy=self.proxy)
            contents = demjson.decode(r.text)
            max_page = contents['data']['pageCount']

            for i in range(max_page):
                url = f'https://www.haoyishu.org/api/v2/case/list/0/{i + 1}?sourceId=0&typeId=0&departmentId={j}&website=true'
                r = req_get(url=url, header=self.header, proxy=self.proxy)
                contents = demjson.decode(r.text)
                videos = contents['data']['list']

                for video in videos:
                    video['url'] = f'https://www.haoyishu.org/web/video/case/{video["albumId"]}'
                    video['uid'] = video['albumId']
                    video['departmentId'] = j
                    del video['article']

                    table.update_one({"uid": video["uid"]}, {"$set": video}, True)
                    n += 1
                    end = time.time()
                    spend = end - start
                    unit_spend = spend / (i + 1 / max_page)
                    remain = (max_page - i - 1 / max_page) * unit_spend
                    print(f"\r正在进行'第{j}类科室'的信息爬取，进度({i + 1}/{max_page}), 获得{n}条视频数据, "
                          f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                          f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')

    def get_meeting_id(self):
        table = self.db['学习班网址']
        table.create_index('uid')

        url = 'https://www.haoyishu.org/web/meeting'
        r = req_get(url, header=self.header, proxy=self.proxy)
        soup = BeautifulSoup(r.text, 'lxml')
        max_type = len(soup.find('section', class_='container').find_all('li', style='display:;')) + 1

        start = time.time()
        n = 0
        for j in range(1, max_type):
            url = f'https://www.haoyishu.org/api/meeting/past/0/1?departmentId={j}&website=true'
            r = req_get(url=url, header=self.header, proxy=self.proxy)
            contents = demjson.decode(r.text)
            max_page = contents['data']['pageCount']

            for i in range(max_page + 1):
                if i == 0:
                    url = f'https://www.haoyishu.org/api/meeting/comming/0?departmentId={j}&website=true'
                    r = req_get(url=url, header=self.header, proxy=self.proxy)
                    contents = demjson.decode(r.text)
                    meetings = contents['data']
                else:
                    url = f'https://www.haoyishu.org/api/meeting/past/0/{i}?departmentId={j}&website=true'
                    r = req_get(url=url, header=self.header, proxy=self.proxy)
                    contents = demjson.decode(r.text)
                    meetings = contents['data']['list']

                for meeting in meetings:
                    meeting['url'] = f'https://www.haoyishu.org/web/meeting/detail?meetingId={meeting["meetingId"]}'
                    meeting['uid'] = meeting['meetingId']
                    meeting['departmentId'] = j
                    for k in meeting['album']:
                        meeting['album' + k] = meeting['album'][k]
                    del meeting['album']

                    table.update_one({"uid": meeting["uid"]}, {"$set": meeting}, True)
                    n += 1
                    end = time.time()
                    spend = end - start
                    unit_spend = spend / (i + 1 / max_page)
                    remain = (max_page - i - 1 / max_page) * unit_spend
                    print(f"\r正在进行'第{j}类科室'的信息爬取，进度({i + 1}/{max_page}), 获得{n}条学习班数据, "
                          f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                          f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')

    def get_article_id(self):
        table = self.db['早读文章网址']
        table.create_index('uid')

        url = 'https://www.haoyishu.org/web/article'
        r = req_get(url, header=self.header, proxy=self.proxy)
        soup = BeautifulSoup(r.text, 'lxml')
        max_type = len(soup.find('ul', class_='condition_list').find_all('li', style='display:;'))

        start = time.time()
        n = 0
        for j in range(1, max_type):
            url = f'https://www.haoyishu.org/api/article/list/1/0?website=true&departmentId={j}&tag='
            r = req_get(url=url, header=self.header, proxy=self.proxy)
            contents = demjson.decode(r.text)
            max_page = contents['data']['pageCount']

            for i in range(max_page):
                url = f'https://www.haoyishu.org/api/article/list/{i + 1}/0?website=true&departmentId={j}&tag='
                r = req_get(url=url, header=self.header, proxy=self.proxy)
                contents = demjson.decode(r.text)
                articles = contents['data']['list']

                for article in articles:
                    article['url'] = f'https://www.haoyishu.org/web/article/detail?articleId={article["articleId"]}'
                    article['uid'] = article['articleId']
                    article['departmentId'] = j

                    table.update_one({"uid": article["uid"]}, {"$set": article}, True)
                    n += 1
                    end = time.time()
                    spend = end - start
                    unit_spend = spend / (i + 1 / max_page)
                    remain = (max_page - i - 1 / max_page) * unit_spend
                    print(f"\r正在进行'第{j}类科室'的信息爬取，进度({i + 1}/{max_page}), 获得{n}条文章数据, "
                          f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                          f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')


if __name__ == "__main__":
    h = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36'
    c = 'gr_user_id=df512dd0-f7c1-4210-a576-0e2ca3f3309c; grwng_uid=e9403df9-4d2d-46a8-8336-9f8927c61f69; Hm_lvt_b8d21f481877d7af7d19f0ee88d98f33=1588320918; 87f7e3c4c896ecf7_gr_session_id=a7014c54-1b75-4c79-8b9e-215a8cd065b8; 87f7e3c4c896ecf7_gr_session_id_a7014c54-1b75-4c79-8b9e-215a8cd065b8=true; sid=s%3AUGHMivjOzKRPETounjfpfupP1RnZWAqn.GaL3tsoFNkc9eL0xLiHRnGVg69uAsekT9psgJwlduOQ; Hm_lpvt_b8d21f481877d7af7d19f0ee88d98f33=1588479277'

    hys = HaoYiShu(headers=h, cookies=c)
    hys.get_meeting_id()
    # hys.get_article_id()
