import re
import time
import warnings

import pymongo
from bs4 import BeautifulSoup

from Base import *

warnings.filterwarnings("ignore")


class DrVoice:

    def __init__(self, headers, cookies):
        self.header = {headers.split(': ')[0]: headers.split(': ')[1]}
        self.cookie = {}
        for i in cookies.split("; "):
            self.cookie[i.split('=')[0]] = i.split('=')[1]
        mongo = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = mongo['严道医声']
        self.proxy = get_proxies()

    def get_course_id(self):
        table = self.db['学院网址']
        table.create_index('uid')

        n = 1
        max_page = 1
        t1 = int()
        start = time.time()
        while n <= int(max_page):
            url = f'http://www.drvoice.cn/courses?page={n}'
            r = req_get(url, header=self.header, proxy=self.proxy)
            if not r:
                time.sleep(10)
                continue
            soup = BeautifulSoup(r.text, 'lxml')

            items = soup.find('div', class_='course-list row').find_all('a')
            for item in items:
                course = dict()
                course['url'] = item['href']
                course['start_date'] = re.search(r'(\d{4}-\d\d-\d\d \d\d:\d\d) 至',
                                                 item.find('div', class_='course-list-item-label').text).group(1)
                course['end_date'] = re.search(r'至 (\d{4}-\d\d-\d\d \d\d:\d\d)',
                                               item.find('div', class_='course-list-item-label').text).group(1)
                course['title'] = item.find('div', class_='course-list-item-description-container').text.strip()
                course['uid'] = item['href'].split('/')[-1]
                t1 = time.time()
                table.update_one({"uid": course["uid"]}, {"$set": course}, True)
                end = time.time()
                spend = end - start
                unit_spend = spend / n
                remain = (int(max_page) - n) * unit_spend
                print(f"\r进度({n}/{max_page}), 本次数据存储用时{round(end - t1, 4)}秒"
                      f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                      f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')

            pages = soup.find('div', class_='pages-container').find_all('a')
            max_page = pages[-2]['href'].split('=')[-1]
            n += 1
        return None

    def get_class_id(self):
        table = self.db['课程网址']
        table.create_index('uid')

        n = 1
        max_page = 1
        start = time.time()
        while n <= int(max_page):
            url = f'http://www.drvoice.cn/classes?page={n}'
            r = req_get(url, header=self.header, proxy=self.proxy)
            if not r:
                time.sleep(10)
                continue
            soup = BeautifulSoup(r.text, 'lxml')

            items = soup.find('ul', class_="class-item-list").find_all('li')
            for item in items:
                cls = dict()
                cls['标题'] = item.a.text
                cls['url'] = item.a['href']
                cls['uid'] = item.a['href'].split('/')[-1]
                t1 = time.time()
                table.update_one({"uid": cls["uid"]}, {"$set": cls}, True)
                end = time.time()
                spend = end - start
                unit_spend = spend / n
                remain = (int(max_page) - n) * unit_spend
                print(f"\r进度({n}/{max_page}), 本次数据存储用时{round(end - t1, 4)}秒"
                      f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                      f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')

            pages = soup.find('div', class_='pages-container').find_all('a')
            max_page = pages[-2]['href'].split('=')[-1]
            n += 1
        return None

    def get_news_id(self):
        table = self.db['文章网址']
        table.create_index('uid')

        n = 1
        max_page = 1
        start = time.time()
        while n <= int(max_page):
            url = f'http://www.drvoice.cn/news?page={n}'
            r = req_get(url, header=self.header, proxy=self.proxy)
            if not r:
                time.sleep(10)
                continue
            soup = BeautifulSoup(r.text, 'lxml')

            items = soup.find('ul', class_="transverse-list").find_all('li')
            for item in items:
                news = dict()
                news['标题'] = item.find('div', class_='transverse-list-title').find('a').text.strip()
                news['url'] = item.a['href']
                news['uid'] = item.a['href'].split('/')[-1]

                t1 = time.time()
                table.update_one({"uid": news["uid"]}, {"$set": news}, True)
                end = time.time()
                spend = end - start
                unit_spend = spend / n
                remain = (int(max_page) - n) * unit_spend
                print(f"\r进度({n}/{max_page}), 本次数据存储用时{round(end - t1, 4)}秒"
                      f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                      f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')

            pages = soup.find('div', class_='pages-container').find_all('a')
            max_page = pages[-2]['href'].split('=')[-1]
            n += 1
        return None

    def get_meeting_id(self):
        table = self.db['会议网址']
        table.create_index('uid')

        n = 1
        max_page = 1
        start = time.time()
        while n <= int(max_page):
            url = f'http://www.drvoice.cn/meetings?page={n}'
            r = req_get(url, header=self.header, proxy=self.proxy)
            if not r:
                time.sleep(10)
                continue
            soup = BeautifulSoup(r.text, 'lxml')

            items = soup.find('ul', class_="vertical-list").find_all('li')
            for item in items:
                meeting = dict()
                meeting['标题'] = item.find('div', class_='vertical-list-title').find('a').text.strip()
                meeting['url'] = item.a['href']
                meeting['uid'] = item.a['href'].split('/')[-1]
                meeting['日期'] = item.article.find('span', class_='meetingTime meetingday').text.strip()
                try:
                    meeting['地点'] = item.article.find('span', class_='meetingAddress meetingAddressicon').text.strip()
                except AttributeError:
                    pass

                t1 = time.time()
                table.update_one({"uid": meeting["uid"]}, {"$set": meeting}, True)
                end = time.time()
                spend = end - start
                unit_spend = spend / n
                remain = (int(max_page) - n) * unit_spend
                print(f"\r进度({n}/{max_page}), 本次数据存储用时{round(end - t1, 4)}秒"
                      f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                      f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')

            pages = soup.find('div', class_='pages-container').find_all('a')
            max_page = pages[-2]['href'].split('=')[-1]
            n += 1
        return None

    def get_news_info(self, url_list):
        table = self.db['文章信息']
        table.create_index('uid')

        start = time.time()
        for e, url in enumerate(url_list):
            r = req_get(url, header=self.header, proxy=self.proxy)
            if not r:
                print(f'\r{e}/{len(url_list)}..', end='')
                continue
            soup = BeautifulSoup(r.text, 'lxml')

            news = dict()
            news['title'] = soup.find('div', class_='article-title').text.strip()
            news['url'] = url
            news['uid'] = url.split('/')[-1]
            news['date'] = soup.find('span', class_='article-date').text.strip()
            news['author'] = soup.find('span', class_='article-author').text.strip()
            try:
                news['content'] = soup.find('div', class_='article-content').text.strip()
            except AttributeError:
                pass
            try:
                news['read'] = re.search(r'(\d+)', soup.find('span', class_='count-container').text).group(1)
            except AttributeError:
                pass

            t1 = time.time()
            table.update_one({"uid": news["uid"]}, {"$set": news}, True)
            end = time.time()
            spend = end - start
            unit_spend = spend / (e + 1)
            remain = (len(url_list) - (e + 1)) * unit_spend
            print(f"\r进度({(e + 1)}/{len(url_list)}), 本次数据存储用时{round(end - t1, 4)}秒"
                  f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                  f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')


if __name__ == "__main__":
    c = 'Hm_lvt_f5b5599fdcae9b1c564fa66762058be6=1588257401; sszztauth=6c4dDfPFniabW4xLOUxdnI2kGUWzSDFHGY42w5DRlLOq87AsCWm_m7Wlc0MOpivdd2vvgZNEJ4nzmYha-3z_4HVkqNROd24OS6OXw43kDVLAv_AoAl79AAw6BoomSptJqF31cQIqmzwd3-GLk_2tNg; sszzt_userid=7999PIYzhluoBzUviB4XRKZMFcf-frjzDOguWVoV4VevHmg; sszzt_username=51aeUjDCv7sDmJk8DjTNl-o1JPOcUVeAKvrtnAE8Y5XAtazNv_V1yGjT0Mk; sszzt_nickname=d20fQ1zS75I7ySnvPza-M8FYAyj04n21BokGJMDNb-mZHXY; sszzt_groupid=621a6OlD7Yd_y9soj9KYW4XRffF1DkWVdy0zqKl6; sszztcookietime=3bd7M29xc0VUhnvszneepcqtUWT880jMz6sIbhorst_F4qjYbAAn; Hm_lpvt_f5b5599fdcae9b1c564fa66762058be6=1588257710'
    h = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36'
    dr = DrVoice(headers=h, cookies=c)
    urls = dr.db['文章网址'].distinct('url')
    dr.get_news_info(urls)
