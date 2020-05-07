import logging
import logging
import re
import time

import pymongo
from bs4 import BeautifulSoup

from Base import *

logging.captureWarnings(True)


class ChunYu:

    def __init__(self, headers, cookies):
        self.header = {headers.split(': ')[0]: headers.split(': ')[1]}
        self.cookie = {}
        for i in cookies.split("; "):
            self.cookie[i.split('=')[0]] = i.split('=')[1]
        mongo = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = mongo['春雨医生']
        self.proxy = get_proxies()

    def get_hospital_id(self):
        table = self.db['医院网址']
        start_url = 'https://www.chunyuyisheng.com/pc/hospitals/'
        r1 = req_get(start_url, header=self.header, cookie=self.cookie)
        soup = BeautifulSoup(r1.text, 'lxml')
        cities = ['https://www.chunyuyisheng.com' + city['href'] for city in
                  soup.find('ul', class_='city').find_all('a')]

        for e, u in enumerate(cities):
            print(f"\r进度为{e + 1}/{len(cities)}...")
            r2 = req_get(u, header=self.header, cookie=self.cookie)
            soup = BeautifulSoup(r2.text, 'lxml')
            lists = soup.find_all('div', class_='list')
            for l in lists:
                for hos in l.find_all('a', class_='hospital-name'):
                    hospital = dict()
                    hospital['医院'] = hos.text
                    hospital['url'] = 'https://www.chunyuyisheng.com' + hos['href']
                    hospital['uid'] = hos['href'].split('/')[-2]
                    table.update_one({'医院': hos.text}, {"$set": hospital}, True)
        return None

    def get_depart_id(self, url_list):
        # 初始化 ==========
        table = self.db['科室网址']
        table.create_index('uid')

        # 主循环 获取数据 ================
        n = 0
        start = time.time()
        for e, u in enumerate(url_list):
            r = req_get(u, header=self.header, cookie=self.cookie)
            if not r:
                continue
            soup = BeautifulSoup(r.text, 'lxml')
            try:
                departs = soup.find('ul', id='clinic').find_all('a')
            except AttributeError:
                print(f'\r{u}, 无科室信息, 跳过本次循环({e}/{len(url_list)})', end='')
                continue
            for dp in departs:
                depart = dict()
                depart['医院'] = soup.find('h3', class_='title').text
                depart['科室'] = re.sub(r'\s', '', dp.text)
                depart['url'] = 'https://www.chunyuyisheng.com' + dp['href']
                depart['uid'] = dp['href'].split('/')[-2]
                try:
                    depart['人数'] = dp.find_parent('li').find('i').text
                except AttributeError:
                    depart['人数'] = '0'
                table.update_one({'uid': depart['uid']}, {"$set": depart}, True)
                end = time.time()
                spend = end - start
                unit_spend = spend / (e + 1)
                remain = (len(url_list) - e - 1) * unit_spend
                n += 1
                print(f"\r进度({e + 1}/{len(url_list)}), 获得{n}条科室信息数据, "
                      f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                      f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')
        print(f"\r爬取科室id完成, 共获取{n}条数据")
        return None

    def get_doctor_id(self, url_list):

        # 初始化 ==========
        table = self.db['医生网址']
        table.create_index('uid')

        n = 1
        start = time.time()
        for e, url in enumerate(url_list):
            r = req_get(url, header=self.header, cookie=self.cookie)
            if not r:
                continue
            soup = BeautifulSoup(r.text, 'lxml')
            lst = soup.find('div', class_='doctor-list clearfix').find_all('div', class_='doctor-info-item')
            if not lst:
                continue
            for l in lst:
                doctor = dict()
                doctor['姓名'] = re.sub(r'\s+', '', l.find('span', class_='name').text)
                doctor['科室'] = re.sub(r'\s+', '', l.find('span', class_='clinic').text)
                doctor['职称'] = re.sub(r'\s+', '', l.find('span', class_='grade').text)
                doctor['医院'] = re.sub(r'\s+', '', l.find('a', class_='hospital').text)
                des = l.find_all('span', class_='half-item')
                for d in des:
                    value = d.find('i').text
                    key = d.text.replace(value, '').strip()
                    doctor[key] = value
                doctor['擅长'] = l.find('p', class_='des').text.replace('擅长：', '').strip()
                try:
                    doctor['状态'] = l.find('span', class_='available').text
                except AttributeError:
                    doctor['状态'] = ''
                doctor['url'] = 'https://www.chunyuyisheng.com' + l.find('a', class_='name-wrap')['href']
                doctor['uid'] = doctor['url'].split('/')[-2]
                table.update_one({'uid': doctor['uid']}, {"$set": doctor}, True)
                end = time.time()
                spend = end - start
                unit_spend = spend / (e + 1)
                remain = (len(url_list) - e - 1) * unit_spend
                n += 1
                print(f"\r进度({e + 1}/{len(url_list)}), 获得{n}条医生信息数据, "
                      f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                      f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')
        print(f"\r爬取医生id完成, 共获取{n}条数据")
        return None

    def get_query_id(self, url_list):

        # 初始化 ==========
        table = self.db['问诊网址']
        table.create_index('uid')

        # 主循环 爬取数据 =========
        start = time.time()
        for e, u in enumerate(url_list):
            n = 1
            # 尝试获取问诊标签
            r0 = req_get(u + 'qa/', header=self.header, cookie=self.cookie)
            if not r0:
                continue
            soup = BeautifulSoup(r0.text, 'lxml')
            tags = [t.text.strip() for t in soup.find('ul', class_='tags').find_all('li')]
            # 根据标签，进一步细化分页器
            for tag in tags:
                if tag == "全部":
                    tag = ''
                # 主循环 获得数据
                while n <= 30:
                    url = f"{u}qa/?tag={tag}&page={n}"
                    n += 1
                    r = req_get(url, header=self.header, cookie=self.cookie)
                    if not r:
                        continue
                    soup = BeautifulSoup(r.text, 'lxml')
                    items = soup.find_all('div', class_='hot-qa-item')
                    if len(items) == 0:
                        break
                    for i in items:
                        query = dict()
                        query['问题'] = re.sub(r'[\s问]+', '', i.find('a').text)
                        query['回答'] = re.sub(r'[\s答]+', '', i.find('div', class_='qa-item-answer').text)
                        query['日期'] = i.find('span', class_='date').text
                        query['url'] = 'https://www.chunyuyisheng.com' + i.find('a')['href']
                        query['uid'] = i.find('a')['href'].split('/')[-2]
                        table.update_one({'uid': query['uid']}, {"$set": query}, True)
            spend = time.time() - start
            unit_time = spend / (e + 1)
            remain = (len(url_list) - (e + 1)) * unit_time
            print(f'\r({e + 1}/{len(url_list)})正在爬取问诊数据...'
                  f'用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, '''
                  f'预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}...', end='')
        return None

    def get_doctor_info(self, url_list):
        # 初始化 ========
        table = self.db['医生信息']
        table.create_index('uid')

        # 主循环 获取数据 ===========
        start = time.time()
        for e, url in enumerate(url_list):
            r = req_get(url, header=self.header, proxy=self.proxy)
            if not r:
                continue
            soup = BeautifulSoup(r.text, 'lxml')
            doctor = dict()
            try:
                doctor['姓名'] = re.sub(r'[\s]+', '', soup.find('span', class_='name').text)
            except AttributeError:
                continue
            if soup.find('span', class_='verified-bage'):
                doctor['认证'] = soup.find('span', class_='verified-bage').text
            else:
                doctor['认证'] = str()
            doctor['科室'] = re.sub(r'[\s]+', '', soup.find('a', class_='clinic').text)
            doctor['职称'] = re.sub(r'[\s]+', '', soup.find('span', class_='grade').text)
            doctor['医院'] = re.sub(r'[\s]+', '', soup.find('a', class_='hospital').text)
            if soup.find('div', class_='doctor-hospital'):
                hos_info = soup.find('div', class_='doctor-hospital').find_all('span')
            else:
                hos_info = list()
            for i in hos_info:
                if '医院' in i.text:
                    doctor['医院等级'] = i.text
                elif '从业' in i.text:
                    doctor['从业'] = i.text
                elif '市' in i.text:
                    doctor['城市'] = i.text
            doc_info = soup.find('ul', class_='doctor-data').find_all('li')
            for i in doc_info:
                doctor[i.find('span', class_='des').text] = i.find('span', class_='number').text
            doctor['关注人数'] = re.search(r'(\d+)', soup.find('div', class_='footer-des').text).group(1)
            intro = soup.find_all('div', class_='paragraph j-paragraph')
            for i in intro:
                key = re.sub(r'\s+', '', i.text.split(' :', 1)[0])
                value = re.sub(r'\s+', '', i.text.split(' :', 1)[1])
                doctor[key] = value.replace('展开收起', '').replace('【春雨提示：部分医院有多个院区，请先与医生确认好地点后再前往就诊】', '')
            doctor['uid'] = url.split('/')[-2]
            doctor['url'] = r.url
            table.update_one({'uid': doctor['uid']}, {"$set": doctor}, True)
            spend = time.time() - start
            unit_time = spend / (e + 1)
            remain = (len(url_list) - (e + 1)) * unit_time
            print(f'\r({e + 1}/{len(url_list)})正在爬取...'
                  f'用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, '''
                  f'预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}...', end='')

        return None

    def get_query_info(self, url_list):

        # 初始化 ========
        table = self.db['问诊信息']
        table.create_index('uid')

        start = time.time()
        for e, url in enumerate(url_list):
            r = req_get(url, header=self.header, proxy=self.proxy)
            if not r:
                continue
            soup = BeautifulSoup(r.text, 'lxml')
            query = dict()
            query['标题'] = soup.find('span', class_='title').text
            query['医师姓名'] = re.sub(r'\s+', '', soup.find('span', class_='hight-light').text)
            query['医师科室'] = soup.find('span', class_='c-gray').text.split(' ')[0].replace(' ', '')
            query['医师职称'] = soup.find('span', class_='c-gray').text.split(' ')[1].replace(' ', '')
            query['医师医院'] = soup.find('div', class_='fixed-layer').find('div', class_='detail').find_all('span')[
                -1].text
            qna = soup.find_all('div', class_='context-left')
            query['患者'] = str()
            query['医生'] = str()
            query['对话'] = str()
            for q in qna:
                txt = re.sub(r'\s|\n', '', q.find('p').text)
                if '患者' in q.find('h6').text:
                    query['患者'] += txt + '\n---------\n'
                    query['对话'] += '患者：\n' + txt + '\n---------\n'
                else:
                    query['医生'] += txt + '\n---------\n'
                    query['对话'] += '医生：\n' + txt + '\n---------\n'
            query['日期'] = re.search(r'([\d-]+)', soup.find('span', class_='ask-time-body').text).group(1)
            query['uid'] = query['标题'] + '.' + query['日期']
            query['url'] = url
            table.update_one({'uid': query['uid']}, {'$set': query}, True)
            spend = time.time() - start
            unit_time = spend / (e + 1)
            remain = (len(url_list) - (e + 1)) * unit_time
            print(f'\r({e + 1}/{len(url_list)})正在爬取...'
                  f'用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, '''
                  f'预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}...', end='')
        return len(url_list)


if __name__ == "__main__":
    h = 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'
    c = 'Hm_lvt_c153f37e6f66b16b2d34688c92698e4b=1585702850,1585879123,1586029343,1586257989; Hm_lpvt_c153f37e6f66b16b2d34688c92698e4b=1586356224'
    cr = ChunYu(headers=h, cookies=c)
    # cr.sync_database()
    # cr.sync_database(keyword="肺动脉高压")
    cr.get_doctor_info(amount=10)
    # cr.get_doctor_info()
