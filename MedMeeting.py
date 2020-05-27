import re
import time
import warnings

import pymongo
from bs4 import BeautifulSoup

from Base import *

warnings.filterwarnings("ignore")


class MedMeeting:
    def __init__(self, headers, cookies):
        self.header = {headers.split(': ')[0]: headers.split(': ')[1]}
        self.cookie = {}
        for i in cookies.split("; "):
            self.cookie[i.split('=')[0]] = i.split('=')[1]
        mongo = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = mongo['会务通']
        self.proxy = get_proxies()

    def get_doctor_link(self, url_list):
        # 初始化 ==========
        table = self.db['医生网址']
        table.create_index('uid')

        # 主循环 获取数据 ================
        start = time.time()
        for e, u in enumerate(url_list):
            r = requests.get(u, headers=self.header, cookies=self.cookie)
            while r.status_code == 502:
                time.sleep(30)
                r = requests.get(u, headers=self.header, cookies=self.cookie)
            soup = BeautifulSoup(r.text, 'lxml')
            max_page = re.search(r'(\d+)', soup.find('div', class_='show_page').find_all('a')[-1]['href']).group(1)
            items = soup.find_all('div', class_='s-item')
            if len(items) != 10:
                break
            for i in items:
                doctor = dict()
                doctor['姓名'] = i.find('span', class_='f20').text
                if i.find('span', class_='bgqlan iblock'):
                    doctor['科室'] = i.find('span', class_='bgqlan iblock').text
                doctor['机构'] = i.find('div', class_='hospital').text
                infos = i.find('div', class_='hui t10').find_all('td')
                for info in infos:
                    doctor[re.sub(r'\d+', '', info.text).strip()] = re.search(r'(\d+)', info.text).group(1)
                doctor['简历'] = i.find('div', class_='desc').text.strip()
                doctor['url'] = 'https://www.medmeeting.org' + i.find('div', class_='sperkerInfo media').find('a')[
                    'href']
                doctor['uid'] = re.search(r'(\d+)', doctor['url']).group(1)
                try:
                    del doctor['']
                except KeyError:
                    pass
                table.update_one({"uid": doctor['uid']}, {"$set": doctor}, True)
            end = time.time()
            spend = end - start
            unit_spend = spend / (e + 1)
            remain = (int(max_page) - e) * unit_spend
            print(f"\r进度({e}/{max_page}), "
                  f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                  f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')
        return None

    def get_meeting_info(self, url_list):
        # 初始化 ==========
        table = self.db['会议']
        table.create_index('uid')

        # 主循环 获取数据 ================
        start = time.time()
        for e, u in enumerate(url_list):
            r = req_get(u, header=self.header, cookie=self.cookie)
            soup = BeautifulSoup(r.text, 'lxml')
            items = soup.find('div', class_='history t20').find_all('dt')
            for i in items:
                meeting = dict()
                meeting['url'] = i.a['href'] if i.a['href'].startswith('http') \
                    else 'https://www.medmeeting.org' + i.a['href']
                meeting['来源'] = u
                try:
                    meeting['uid'] = re.search(r'http://(.+)\.me', i.a['href']).group(1) + '_' + r.url.split('/')[-1]
                except AttributeError:
                    meeting['uid'] = i.a['href'].split('/')[-1] + "_" + r.url.split('/')[-1]
                meeting['会议名称'] = i.a.text
                meeting['会议日期'] = i.find('div', class_='hui f14 t5').text.split(' ')[0]
                meeting['会议地点'] = i.find('div', class_='hui f14 t5').text.split(' ')[1]
                meeting['参会专家'] = re.sub(r'\s+', '', soup.find('div', class_='fl f36 t').text)
                meeting['专家id'] = r.url.split('/')[-1]
                try:
                    meeting['会议细节'] = 'https://www.medmeeting.org' + i.find('small').find('a')['href']
                except AttributeError:
                    pass
                for j in i.find_all('small', class_="mr10"):
                    if j:
                        meeting[j.text.split("（")[0].strip()] = re.search(r'(\d+)', j.text).group(1)
                table.update_one({"uid": meeting['uid']}, {"$set": meeting}, True)
            end = time.time()
            spend = end - start
            unit_spend = spend / (e + 1)
            remain = (len(url_list) - e) * unit_spend
            print(f"\r进度({e}/{len(url_list)}), "
                  f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                  f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')
        return None

    def get_video_info(self, url_list):
        # 初始化 ==========
        table = self.db['视频']
        table.create_index('uid')

        # 主循环 获取数据 ================
        start = time.time()
        for e, u in enumerate(url_list):
            r = req_get(u, header=self.header, cookie=self.cookie)
            soup = BeautifulSoup(r.text, 'lxml')
            try:
                items = soup.find('div', class_='zj-shipin clearfix t20').find_all('li')
            except AttributeError:
                continue
            for i in items:
                video = dict()
                video['url'] = "https://www.medmeeting.org" + i.a['href']
                video['来源'] = u
                video['uid'] = i.a['href'].split('/')[-1] + '_' + r.url.split('/')[-1]
                video['视频名称'] = i.find('div', class_='desc').a.text
                video['参会专家'] = re.sub(r'\s+', '', soup.find('div', class_='fl f36 t').text)
                video['专家id'] = r.url.split('/')[-1]
                desc = i.find_all('td')
                for d in desc:
                    video[d['title']] = re.search(r'(\d+)', d.a.text).group(1)
                table.update_one({"uid": video['uid']}, {"$set": video}, True)
            end = time.time()
            spend = end - start
            unit_spend = spend / (e + 1)
            remain = (len(url_list) - e) * unit_spend
            print(f"\r进度({e}/{len(url_list)}), "
                  f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                  f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')
        return None

    def get_meeting_detail(self, url_list):
        table = self.db['会议细节']
        table.create_index('uid')

        start = time.time()
        for e, url in enumerate(url_list):
            r = req_get(url, header=self.header, proxy=self.proxy)
            soup = BeautifulSoup(r.text, 'lxml')
            message = dict()
            message['conf_id'] = url.split('?')[0].split('/')[-1]
            message['speaker_id'] = url.split('=')[-1]
            message['url'] = url

            if soup.find('div', class_="sperkerInfo"):
                message['speaker'] = soup.find('div', class_="sperkerInfo").find("strong").text
                try:
                    message['org'] = soup.find('div', class_="f14 qhui").text
                except AttributeError:
                    pass
                for item in soup.find_all("div", class_="duty-box"):
                    message['date'] = item.find('div', class_='fl l').text.strip()
                    for record in item.find_all('div', class_="cic"):
                        cols = ['role', 'time', 'address', 'topic']
                        for col, p in zip(cols, record.find_all('p')):
                            message[col] = p.text.strip()
                        message['role'] = message['role'] if message['role'] == '主持' else '发言'
                        message['uid'] = message['conf_id'] + '_' + message['speaker_id'] + '_' + message[
                            'date'] + '_' + message['time']
                        table.update_one({"uid": message["uid"]}, {"$set": message}, True)
                    for record in item.find_all('div', class_="cic2"):
                        cols = ['role', 'info', 'time', 'address', 'topic', 'segment']
                        for col, p in zip(cols, record.find_all('p')):
                            message[col] = p.text.strip()
                        message['role'] = message['role'] if message['role'] == '主持' else '发言'
                        message['uid'] = message['conf_id'] + '_' + message['speaker_id'] + '_' + message[
                            'date'] + '_' + message['time']
                        table.update_one({"uid": message["uid"]}, {"$set": message}, True)
            else:
                try:
                    message['speaker'] = soup.find("div", class_="expertIntro").find("h3").text
                except AttributeError:
                    continue
                try:
                    message['org'] = soup.find("div", class_="expertIntro").find("p").text
                except AttributeError:
                    pass
                for item in soup.find('div', class_="mess-content").find_all('li'):
                    message['topic'] = item.find('h3').text.strip()
                    message['role'] = item.find('h4').text.strip()
                    if message['role'] != "主持":
                        message['info'] = message['role'].split('：')[-1]
                        message['role'] = "发言"
                    message['date'] = re.search(r'(20\d\d-\d\d-\d\d)', item.find('p', class_="time").text).group()
                    message['time'] = re.search(r'(\d\d:\d\d-\d\d:\d\d)', item.find('p', class_="time").text).group()
                    message['address'] = item.find('p', class_="address").text.strip()
                    message['uid'] = message['conf_id'] + '_' + message['speaker_id'] + '_' + message['date'] + '_' + \
                                     message['time']
                    table.update_one({"uid": message["uid"]}, {"$set": message}, True)
            end = time.time()
            spend = end - start
            unit_spend = spend / (e + 1)
            remain = (len(url_list) - e) * unit_spend
            print(f"\r进度({e}/{len(url_list)}), "
                  f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                  f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')
        return None

    def get_doctor_detail(self, url_list):
        table = self.db['医生信息']
        table.create_index('uid')

        start = time.time()
        for e, url in enumerate(url_list):
            r = req_get(url, header=self.header, cookie=self.cookie)
            soup = BeautifulSoup(r.text, "lxml")
            doctor = dict()
            doctor['name'] = soup.find("div", class_='fl f36 t').text.strip()
            items = soup.find("div", class_='zj-num fr').find_all('li')
            for i in items:
                doctor[re.search(r'([^\d\s]+)', i.text).group(1)] = re.search(r'(\d+)', i.text).group(1)
            info = re.sub(r'\s+', ' ', soup.find('table', class_="jjtable").find('tr').text).replace("： ", ":").strip()
            for i in info.split(" "):
                try:
                    doctor[i.split(':')[0]] = i.split(':')[1]
                except IndexError:
                    continue
            intro = soup.find('table', class_="jjtable").find('tr').find_next_siblings('tr')
            for i in intro[:-1]:
                doctor[i.text.split('：')[0].strip()] = re.sub(r'[更多\s]+', ',', i.text.split('：')[1])
                doctor['uid'] = url.split('/')[-1]
                doctor['url'] = url
            table.update_one({"uid": doctor['uid']}, {"$set": doctor}, True)
            end = time.time()
            spend = end - start
            unit_spend = spend / (e + 1)
            remain = (len(url_list) - e) * unit_spend
            print(f"\r进度({e}/{len(url_list)}), "
                  f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                  f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')
        return None


if __name__ == '__main__':
    c = '__jsluid_s=7e7b3d050e53033df2f394f60f0932cb; Union_CommitteeID=0; __jsluid_h=9a958f28316df9148afcb898d1842ca8; Hm_lvt_d7682ab43891c68a00de46e9ce5b76aa=1586146085,1586251847,1587458191; _pk_id.981.5632=678ad6bccee740a0.1587457350.0.1587458962..; _pk_id.3459.5632=72899dbd774d15b6.1587477090.1.1587477090.1587477090.; _pk_id.4281.5632=6489a60aa5392111.1587477067.1.1587477108.1587477067.; _pk_id.4884.5632=542cb43082041f7b.1587475600.1.1587477109.1587475600.; _pk_id.4981.5632=d1bc5f49269a52ec.1587477129.0.1587477129..; _pk_id.5963.5632=16362c3aaf3564f4.1587477145.1.1587477226.1587477172.; _pk_id.2755.5632=dbbc8c11379f2308.1587477243.1.1587477243.1587477243.; _pk_id.5743.5632=6e788578c3a8d5eb.1587476237.1.1587477804.1587476237.; _pk_id.5745.5632=94e7253729a8044f.1587477782.1.1587478972.1587477811.; _pk_id.5751.5632=6e170607f8d4f027.1587478131.0.1587522520..; _pk_id.737.5632=0d416182e0d14985.1587523481.0.1587523481..; ASP.NET_SessionId=ppkdqo3ddekarid0jj4riklw; __RequestVerificationToken=BmifaDms6reZVZFd7xb6SH4THntaB4OqFobuSUxVUFNRUJUMiBm0S5HUXFY165pEgDVlvqJVS9R2l8YhiqGIdEl0_spiuQrkqbO6_J7xsebDHZnVQVSacPKI4x01; medmeeting.org=CB42313CD46DFCFF6B16422F1AF593664433F56CA482AC264A7D5C72A940190866D5E841D35B8467F0400307EC5DB95EB51804FAA3787D8893BC2A1B8CE150207B8354C9E5826CD65EF8CF3B8246002A01C61DD5D8F54D33F09F918657EEF620F5E7B65C2BF0AE1A4B01853B; SERVERID=35524be371e9a92e7c5ee185698673e4|1587739300|1587739288; __tins__18866278=%7B%22sid%22%3A%201587739299100%2C%20%22vd%22%3A%201%2C%20%22expires%22%3A%201587741099100%7D; __51cke__=; __51laig__=1; Hm_lvt_5dd192c493a8ddd50217f61393478f3f=1586142387,1586148433,1587457283,1587739299; Hm_lpvt_5dd192c493a8ddd50217f61393478f3f=1587739299; _pk_ref.1.5632=%5B%22%22%2C%22%22%2C1587739310%2C%22https%3A%2F%2Fwww.google.com%2F%22%5D; _pk_id.1.5632=28786e8204a59e9c.1585982754.11.1587739310.1587739310.; _pk_ses.1.5632=*'
    h = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'
    cr = MedMeeting(headers=h, cookies=c)
    cr.get_meeting_info()
    # cr.get_video_info()
    # cr.get_meeting_detail()
    # urls = ['https://www.medmeeting.org/resource/speaker/2414639', 'https://www.medmeeting.org/resource/speaker/2212919']
    # cr.get_doctor_detail(url_list=urls)
