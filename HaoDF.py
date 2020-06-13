import logging
import time

import pymongo
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

from Base import *

logging.captureWarnings(True)


class HaoDF:
    def __init__(self, headers, cookies):
        self.header = {headers.split(': ')[0]: headers.split(': ')[1]}
        self.cookie = {}
        for i in cookies.split("; "):
            self.cookie[i.split('=')[0]] = i.split('=')[1]
        self.proxy = get_proxies()
        mongo = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = mongo['好大夫']

    def get_hospital_id(self, max_page=105):
        # 初始化 =========
        table = self.db['医院编号']
        url_list = []

        # 获得来源url清单 ========
        for i in range(max_page):
            url = f'https://www.haodf.com/sitemap-ys/p_{i + 1}'
            url_list.append(url)

        # 主循环 爬取数据 ========
        n = 0
        for u in url_list:
            r = req_get(u, header=self.header, proxy=self.proxy)
            if not r:
                continue
            soup = BeautifulSoup(r.text, 'lxml')
            for i in soup.find_all('li')[-1].find_all('a'):
                hospital = dict()
                hospital['uid'] = i['href'].split('_')[-2]
                hospital['url'] = 'https://www.haodf.com' + i['href']
                hospital['医院'] = i.text
                table.update_one({'uid': hospital['uid']}, {"$set": hospital}, True)
                n += 1
                print(f'\r已爬取{n}条数据', end='')
        print(f"爬取医院id完成, 共获取{n}条数据")
        return url_list

    def get_depart_id(self, url_list):
        # 初始化 ========
        table = self.db['科室编号']

        # 主循环 获取数据 ============
        n = 0
        start = time.time()
        for e, u in enumerate(url_list):
            r1 = req_get(u, header=self.header, proxy=self.proxy)
            if not r1:
                continue
            soup = BeautifulSoup(r1.text, 'lxml')
            hospital_name = re.search(r'>(.+)医生信息', str(soup.h1)).group(1)
            for i in soup.find_all('li')[0].find_all('a'):
                depart = dict()
                depart['uid'] = i['href'].split('_')[-2]
                print(depart['uid'])
                depart['url'] = 'https://www.haodf.com' + i['href']
                depart['医院'] = hospital_name
                depart['科室'] = i.text
                table.update_one({'uid': depart['uid']}, {"$set": depart}, True)
                n += 1
            end = time.time()
            spend = end - start
            unit_spend = spend / (e + 1)
            remain = (len(url_list) - e - 1) * unit_spend
            print(f"\r进度({e + 1}/{len(url_list)}), 获得{n}条科室数据, "
                  f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                  f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')
        print(f"爬取科室id完成, 共获取{n}条数据")

    def get_doctor_id(self, url_list):
        # 初始化 ========
        table = self.db['医生编号']

        # 主循环 爬取数据 ==========
        n = 0
        start = time.time()
        for e, u in enumerate(url_list):
            hospital_code = u.split('_')[-2]
            r1 = req_get(u, header=self.header, proxy=self.proxy)
            if not r1:
                continue
            soup = BeautifulSoup(r1.text, 'lxml')
            hospital_name = re.search(r'>(.+)医生信息', str(soup.h1)).group(1)
            try:
                max_page = int(re.search(r'(\d+)" class="p_num">尾页', r1.text).group(1))
            except AttributeError:
                max_page = 1
            for i in range(max_page):
                url = f'https://www.haodf.com/sitemap-ys/hos_{hospital_code}_{i + 1}'
                r2 = req_get(u, header=self.header, proxy=self.proxy)
                if not r2:
                    continue
                soup = BeautifulSoup(r2.text, 'lxml')
                for j in soup.find_all('li')[-1].find_all('a'):
                    try:
                        doctor_info = dict()
                        doctor_info['所在医院'] = hospital_name
                        doctor_info['医院编码'] = hospital_code
                        doctor_info['医生姓名'] = j.text
                        doctor_info['url'] = 'https:' + j['href']
                        doctor_info['uid'] = re.search(r'doctor/(.+).htm', j['href']).group(1)
                        table.update_one({'uid': doctor_info['uid']}, {"$set": doctor_info}, True)
                        n += 1
                    except AttributeError:
                        continue
                    end = time.time()
                    spend = end - start
                    unit_spend = spend / (e + 1)
                    remain = (len(url_list) - e - 1) * unit_spend
                    print(f"\r进度({e + 1}/{len(url_list)}), 获得{n}条医生数据, "
                          f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                          f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}。", end='')
        print(f"\r爬取医生id完成, 共获取{n}条数据")
        return n

    def get_query_id(self, url_list):
        # 初始化 ==========
        table = self.db['问诊编号']
        table.create_index('uid')

        # 主循环 爬取数据====================
        n = 0
        start = time.time()
        for e, u in enumerate(url_list):
            d = re.search(r'/(20\d{6})_1', u).group(1)
            r1 = req_get(u, header=self.header, proxy=self.proxy)
            if not r1:
                continue
            try:
                max_page = int(re.search(r'(\d+)/" class="p_num">尾页', r1.text).group(1))
            except AttributeError:
                max_page = 1

            i = 0
            while i < max_page:
                url = u.replace('_1/', f'_{i + 1}/')  # 该数据日期
                r = req_get(u, header=self.header, proxy=self.proxy)
                if not r:
                    continue
                soup = BeautifulSoup(r.text, 'lxml')
                try:
                    lst = soup.find('li', class_='hh').find_all('a')  # 该分页元素组
                except AttributeError:
                    time.sleep(1)
                    continue
                for l in lst:
                    query = dict()
                    query['url'] = 'https:' + l['href']
                    query['标题'] = l.text
                    query['日期'] = d
                    query['uid'] = l['href'].split('/')[-1].split('.')[0]
                    # 保存数据
                    table.update_one({'uid': query['uid']}, {"$set": query}, True)
                    n += 1
                    # 输出进度报告
                    end = time.time()
                    spend = end - start
                    unit_spend = spend / (e + 1 + (i + 1) / max_page)
                    remain = (len(url_list) - e - 1 - (i + 1) / max_page) * unit_spend
                    d = re.search(r'(\d{8})', u).group(1)
                    print(f"\r正在爬取{d}的数据, 进度({e + 1}/{len(url_list)}), 获得{n}条问诊数据, "
                          f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                          f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')
                i += 1
        print(f"\r爬取问诊分流id完成, 共获取{n}条数据")
        return n

    def get_doctor_info(self, url_list):
        # 初始化 ========
        table = self.db['医生信息']
        table.create_index('uid')

        n = 0
        driver = webdriver.Chrome()
        driver.implicitly_wait(10)
        start = time.time()
        for e, c in enumerate(url_list):
            try:
                doctor = {}
                driver.get(c)
                doctor['uid'] = c.split('/')[-1].split('.')[0]
                doctor['主页'] = driver.current_url
                doctor['姓名'] = driver.find_element_by_css_selector('h1.doctor-name').text
                doctor['职称'] = driver.find_element_by_class_name('positon').text
                faculty = re.sub(r'\s+', ' ', driver.find_element_by_class_name('doctor-faculty').text)
                doctor['医院'] = faculty.split(' ')[0]
                doctor['科室'] = faculty.split(' ')[1]
                good_at = driver.find_elements_by_css_selector('.good-at-con > .clearfix')
                for i in good_at:
                    doctor[i.find_element_by_class_name('good-at-label').text] = i.find_element_by_class_name(
                        'good-at-text').text
                status = driver.find_element_by_class_name('profile-sta').find_elements_by_tag_name('p')
                for s in status:
                    doctor[s.text.split('\n')[0]] = s.text.split('\n')[1]
                web = driver.find_elements_by_css_selector('.person-web >  .item-body > .clearfix')
                for w in web:
                    try:
                        doctor[w.text.split('：\n')[0]] = w.text.split('：\n')[1]
                    except IndexError:
                        pass
                del doctor['']
                table.update_one({'uid': doctor['uid']}, {"$set": doctor}, True)
                n += 1
            except NoSuchElementException:
                time.sleep(5)
                continue
            end = time.time()
            spend = end - start
            unit_spend = spend / (e + 1)
            remain = (len(url_list) - e - 1) * unit_spend
            print(f"\r进度({e + 1}/{len(url_list)}), 获得{n}条医生信息数据, "
                  f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                  f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')
        print(f"\r爬取医生id完成, 共获取{n}条数据")
        return n

    def get_query_info(self, url_list):
        # 初始化 ========
        table = self.db['问诊分流']
        table.create_index('uid')

        # =================== 主循环 ====================
        n = 0
        start = time.time()
        for e, u in enumerate(url_list):
            r = req_get(u, header=self.header, proxy=self.proxy)
            if not r:
                print(f"\r进度({e + 1}/{len(url_list)})", end='')
                continue
            soup = BeautifulSoup(r.text, 'lxml')
            query = dict()
            query['url'] = u
            query['uid'] = query['url'].split('/')[-1].split('.')[0]
            try:
                query['标题'] = soup.find('div', id='lidingbu').find('span', class_='fl').text.strip()
            except AttributeError:
                print(f"\r进度({e + 1}/{len(url_list)})", end='')
                continue
            query['医生姓名'] = soup.find('h1', class_='doctor-name').text.strip()
            query['医师职称'] = re.sub(r' ', '', soup.find('span', class_='positon').text).strip()
            query['医师医院'] = soup.find('p', class_='doctor-faculty').text.split('\n')[1]
            query['医师科室'] = soup.find('p', class_='doctor-faculty').text.split('\n')[2]
            query['医师主页'] = 'https:' + soup.find('a', class_='tab-item first')['href']

            date = soup.find_all('div', class_='yh_l_times')[-1].text
            if not date.startswith('20'):
                if '.' in date:
                    date = f'{dt.date.today().year}.{date}'
                else:
                    date = f'{dt.date.today()}'
            query['日期'] = date.replace('-', '.')

            for elem in soup.find_all(['script', 'style', 'h4']):
                elem.extract()
            items = soup.find_all('div', class_='stream_yh_right')
            query['患者'] = str()
            query['对话'] = str()
            query['医生'] = str()
            for i in items:
                img = i.find('img')['src']
                txt = re.sub(r'\s+', '.', i.text.strip())
                if 'huan' in img:
                    query['患者'] += txt + '\n=========\n'
                    query['对话'] += "患者:\n" + txt + '\n=========\n'
                elif 'yi' in img:
                    query['医生'] += txt + '\n=========\n'
                    query['对话'] += "医生:\n" + txt + '\n=========\n'
                else:
                    pass
            table.update_one({"uid": query["uid"]}, {"$set": query}, True)
            n += 1

            end = time.time()
            spend = end - start
            unit_spend = spend / (e + 1)
            remain = (len(url_list) - e - 1) * unit_spend
            print(f"\r进度({e + 1}/{len(url_list)}), 获得{n}条问诊数据, "
                  f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                  f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')
        print(f"\r爬取问诊数据完成, 共获取{n}条数据")
        return n


if __name__ == "__main__":
    header = "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"
    cookie = "__jsluid_s=407d73fe92cacf1c7f8b30c6d557decc; g=80095_1572235575983; CNZZDATA-FE=CNZZDATA-FE; UM_distinctid=16e108b03c640e-02d44ed443a997-b363e65-1fa400-16e108b03c766a; _ga=GA1.2.1766741159.1572235577; g=HDF.236.5dbfe00cf04df; CNZZDATA2724401=cnzz_eid%3D202540008-1576389546-https%253A%252F%252Fwww.haodf.com%252F%26ntime%3D1576389546; Hm_lvt_d7682ab43891c68a00de46e9ce5b76aa=1576955893,1577798867; __cdnuid_s=b9917fb409e557831790510436fe5f9d; __cdnuid_h=42bbb6dfac2c100493961bca9b4d1b81; __jsluid_h=47644098b8113ef423d6a71995d87ed2; Hm_lvt_dfa5478034171cc641b1639b2a5b717d=1583680765,1583720206,1583934965,1585470427; CNZZDATA1914877=cnzz_eid%3D314167335-1572855236-https%253A%252F%252Fso.haodf.com%252F%26ntime%3D1585735435; CNZZDATA1256706712=2014827536-1572230889-%7C1585756971"
    cr = HaoDF(headers=header, cookies=cookie)