import logging
import time

import pymongo
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

from Base import *

logging.captureWarnings(True)


class WeiYi:

    def __init__(self, headers, cookies):
        self.header = {headers.split(': ')[0]: headers.split(': ')[1]}
        self.cookie = {}
        for i in cookies.split("; "):
            self.cookie[i.split('=')[0]] = i.split('=')[1]
        self.proxy = get_proxies()
        mongo = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = mongo['微医']

    def get_hospital_id(self):
        # 初始化
        table = self.db['医院网址']
        table.create_index('uid')

        start_url = 'https://www.guahao.com/nav'
        r = req_get(start_url, header=self.header, proxy=self.proxy)
        soup = BeautifulSoup(r.text, 'lxml')

        # 获取全部地区链接
        cities = []
        for city in soup.find_all('ul', class_="content")[1].find_all('li'):
            if '热点' not in city.text:
                for a in city.find('div').find_all('a'):
                    cities.append(a['href'])

        # 遍历城市地区
        start = time.time()
        for e, c in enumerate(cities):
            r = req_get(c, header=self.header, proxy=self.proxy)
            soup = BeautifulSoup(r.text, 'lxml')
            root_url = soup.find('h3', class_="title").find('a')['href']

            # 主循环 获取数据
            for i in range(1, 61):
                url = f'{root_url}/p{i}'
                r = req_get(url, header=self.header, proxy=self.proxy)
                soup = BeautifulSoup(r.text, 'lxml')
                items = soup.find_all('div', class_='hos-total')

                for item in items:
                    hospital = dict()
                    hospital['医院'] = item.find('dt').find('a').text.strip()
                    hospital['等级'] = item.find('dt').find('em').text.strip()
                    hospital['电话'] = item.find('p', class_='tel').text.strip()
                    hospital['地址'] = item.find('p', class_='addr').text.strip()
                    hospital['url'] = item.a['href']
                    hospital['uid'] = item.a['href'].split('/')[-1]
                    comment = item.find('div', class_='comment').find('label')
                    hospital['预约'] = comment.text.strip()
                    hospital['评价'] = comment.find_next('label').text.strip()
                    hospital['省市'] = root_url.split('/')[5]
                    hospital['地区'] = root_url.split('/')[7]
                    table.update_one({"uid": hospital["uid"]}, {"$set": hospital}, True)
                    spend = time.time() - start
                    unit_time = spend / (e + 1)
                    remain = (len(cities) - (e + 1)) * unit_time
                    print(f'\r({e + 1}/{len(cities)})正在爬取医院网址数据...'
                          f'用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, '''
                          f'预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}...', end='')

                # 检查是否为尾页，若尾页则break循环
                if not soup.find('a', class_="next"):
                    break
        return None


if __name__ == "__main__":
    h = 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'
    c = '_sid_=1573292055390018725013185; _wysid_=1575043658891080843004962; _fp_code_=188d03dcfa6a70eeb37d5349e55faf25; monitor_sid=19; mst=1583722192942; mlt=1583722527152; monitor_seq=62; _ipgeo=province%3A%E5%8C%97%E4%BA%AC%7Ccity%3A%E4%B8%8D%E9%99%90; Hm_lvt_3a79c3f192d291eafbe9735053af3f82=1587009383,1589033426; _sh_ssid_=1589033427355; _e_m=1589033427360; searchHistory=%E5%86%85%E5%88%86%E6%B3%8C%2C%7C%E7%96%BE%E7%97%85%2C%7C%E7%B4%A2%E6%8B%89%E8%8F%B2%E5%B0%BC%2C%7C%E5%B0%84%E9%A2%91%E6%B6%88%E8%9E%8D%2C%7C%E7%BB%8F%E5%8A%A8%E8%84%89%E6%94%BE%E5%B0%84%E6%A0%93%E5%A1%9E%E6%B3%95TARE%2C%7C%E7%BB%8F%E5%8A%A8%E8%84%89%E6%A0%93%E5%A1%9ETACE%2C%7C%E8%82%9D%E7%A7%BB%E6%A4%8D%2C%7C%E7%94%B2%E8%83%8E%E8%9B%8B%E7%99%BDAFP%2C%7C%E8%82%9D%E7%A1%AC%E5%8C%96%2C%7C%E5%8E%9F%E5%8F%91%E6%80%A7%E8%82%9D%E7%99%8C%2C%7C%2Cclear; __rf__=7chG/BRT+pOqEPGyftYg5mrGZeCmeBOiVpl+MchAJxYHrpeORtDzCTY7KSUeL4WYllbJIK+A8d2L3OYDejVVLTQAsNqZAjfekME39l870n4pG0SN/lH52ngYXHzVK0D5; _area_=%7B%22provinceId%22%3A%222%22%2C%22provinceName%22%3A%22%E4%B8%8A%E6%B5%B7%22%2C%22cityId%22%3A%22all%22%2C%22cityName%22%3A%22%E4%B8%8D%E9%99%90%22%7D; Hm_lpvt_3a79c3f192d291eafbe9735053af3f82=1589034788; _fmdata=zKKAwUAZCKIuszqDcZJTXVY69WdEUIMjTyPw%2F7d%2BnZpz4zN2EylKLVJwzLZBp55ZDJWH%2BxivzUBvuth0EvKBSYSNkRR6Nenz6mnawqsCQSk%3D; _fm_code=eyJ2IjoiNGs1N0wzVUh0QVU5U1RMZUFPdDZLRkV4anZvR1NVTU90bzRMTXRWTUxhOW1nMXcyM0kwUm9iRlpDenBHNzI2bSIsIm9zIjoid2ViIiwiaXQiOjExMDAsInQiOiJsci9VLytmUS9EQ1Y0ZnNNbU1WYnNhaEZQYjFFMGRrai83bHY5bXM2amFqM1IrR3lwWUVlUkNORlB5QlV6YmJxT2VNQ3lRU2dvN0RzNG92T1VzRUEyZz09In0%3D'
    wy = WeiYi(headers=h, cookies=c)
    wy.get_hospital_id()
