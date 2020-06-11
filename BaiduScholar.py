import logging
import time
from urllib.parse import unquote

import bs4
import demjson
import pymongo
from bs4 import BeautifulSoup
from pymongo.errors import WriteError

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
        # self.driver = webdriver.Chrome()

    def get_scholar_link(self, name_list, affl_keyword=None):
        table = self.db['学者网址']
        table.create_index('uid')

        start = time.time()
        for e, name in enumerate(name_list):
            start_url = f'https://xueshu.baidu.com/usercenter/data/authorchannel?cmd=inject_page&author={name}&affiliate={affl_keyword}'
            r = req_get(url=start_url, header=self.header, proxy=self.proxy)
            if not r:
                continue
            r.encoding = r.apparent_encoding
            token = re.search(r'bds.cf.token = "(.+)";', r.text).group(1)
            ts = re.search(r'bds.cf.ts = "(.+)";', r.text).group(1)
            sign = re.search(r'bds.cf.sign = "(.+)";', r.text).group(1)
            current_page = 1
            max_page = 100
            n = 0
            while current_page <= max_page:
                url = f'https://xueshu.baidu.com/usercenter/data/authorchannel?cmd=search_author&_token={token}&_ts={ts}&_sign={sign}&author={name}&affiliate={affl_keyword}&curPageNum={current_page}'
                r = req_get(url=url, header=self.header, proxy=self.proxy)
                if not r:
                    continue
                try:
                    contents = demjson.decode(r.text)
                except demjson.JSONDecodeError:
                    continue
                contents = contents['htmldata']
                try:
                    max_page = int(re.search(r'data-num="\d+">(\d+)</span><a', contents).group(1))
                except AttributeError:
                    max_page = 1

                soup = BeautifulSoup(contents, 'lxml')
                scholar_list = soup.find_all('div', class_="searchResultItem")
                for s in scholar_list:
                    n += 1
                    scholar = dict()
                    scholar['作者姓名'] = s.find('a', class_="personName").text.strip()
                    scholar['作者机构'] = s.find('p', class_="personInstitution").text.strip()
                    scholar['发表文章'] = s.find('span', class_="articleNum").text.strip()
                    scholar['被引次数'] = s.find('span', class_="quoteNum").text.strip()
                    try:
                        scholar['研究领域'] = s.find('span', class_="aFiled").text.strip()
                    except AttributeError:
                        pass
                    temp_url = 'http://xueshu.baidu.com' + s.find('a', class_="personName")['href']
                    temp_r = req_get(temp_url, header=self.header, proxy=self.proxy)
                    scholar['url'] = temp_r.url
                    scholar['uid'] = scholar['url'].split('/')[-1]
                    print(scholar)
                    table.update_one({"uid": scholar["uid"]}, {"$set": scholar}, True)
                    end = time.time()
                    spend = end - start
                    unit_spend = spend / (e + 1)
                    remain = (len(name_list) - e - 1) * unit_spend
                    print(
                        f"\r进度正在爬取第({e + 1}/{len(name_list)})名医生的({current_page + 1}/{max_page})页信息数据, "
                        f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                        f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')
                current_page += 1
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

    def get_essay_link_by_authorlink(self, url_list):
        table = self.db['论文网址(学者页)']
        table.create_index('uid')

        start = time.time()
        for e, start_url in enumerate(url_list):
            r = req_get(url=start_url, header=self.header, proxy=self.proxy)
            if not r:
                continue
            r.encoding = r.apparent_encoding
            top_soup = BeautifulSoup(r.text, 'lxml')
            author_id = top_soup.find("span", class_='p_scholarID_id').text

            post_dict = dict()
            post_dict['_token'] = re.search(r'bds.cf.token = "(.+)";', r.text).group(1)
            post_dict['_ts'] = re.search(r'bds.cf.ts = "(.+)";', r.text).group(1)
            post_dict['_sign'] = re.search(r'bds.cf.sign = "(.+)";', r.text).group(1)
            post_dict['cmd'] = 'academic_paper'
            post_dict['entity_id'] = re.search(r"entity_id: '(.+)'", r.text).group(1)
            post_dict['bsToken'] = re.search(r"bsToken: '(.+)'", r.text).group(1)
            post_dict['sc_sort'] = 'sc_time'

            current_page = 1
            max_page = 100
            while current_page <= max_page:

                post_dict['curPageNum'] = str(current_page)
                r = req_post(url='https://xueshu.baidu.com/usercenter/data/author', data=post_dict, header=self.header,
                             proxy=self.proxy)
                r.encoding = r.apparent_encoding
                try:
                    max_page = int(re.search(r'data-num="\d+">(\d+)</span><a', r.text).group(1))
                except AttributeError:
                    max_page = 1

                soup = BeautifulSoup(r.text, 'lxml')
                items = soup.find_all('div', class_="result")

                for i in items:
                    title = i.find('a')
                    essay = dict()
                    essay['url'] = 'http://' + title['href'] if not title['href'].startswith("http") else title['href']
                    essay['学者url'] = start_url
                    essay['学者code'] = author_id
                    essay['标题'] = title.text.strip()
                    essay['uid'] = essay['标题']
                    infos = i.find('div', class_='res_info').contents
                    for info in infos:
                        if isinstance(info, bs4.element.Tag) and 'res_year' in str(info):
                            essay['年份'] = info.text
                        elif isinstance(info, bs4.element.Tag) and 'cite_cont' in str(info):
                            essay['被引量'] = info.findChildren()[1].text
                        elif isinstance(info, bs4.element.Tag) and info.name == 'span':
                            essay['作者'] = info.text
                        elif isinstance(info, bs4.element.Tag) and info.name == 'a':
                            essay['期刊'] = info.text
                        else:
                            pass
                    table.update_one({"uid": essay["uid"]}, {"$set": essay}, True)
                    end = time.time()
                    spend = end - start
                    unit_spend = spend / (e + 1)
                    remain = (len(url_list) - e - 1) * unit_spend
                    print(
                        f"\r进度正在爬取第({e + 1}/{len(url_list)})名医生的({current_page + 1}/{max_page})页信息数据, "
                        f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                        f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')
                current_page += 1
        return None

    def get_essay_link_by_keyword(self, keyword, filter=None):

        table = self.db['论文网址(关键词)']
        table.create_index('uid')

        n = 0
        total = 0
        has_next = True
        start = time.time()
        while has_next:
            url = f'https://xueshu.baidu.com/s?wd={keyword}&pn={n}&tn=SE_baiduxueshu_c1gjeupa&ie=utf-8&sc_hit=1'
            if filter:
                url += filter

            r = req_get(url, header=self.header, proxy=self.proxy)
            if not r:
                n += 10
                continue
            soup = BeautifulSoup(r.text, 'lxml')

            for item in soup.find_all('div', class_='result'):
                essay = dict()
                essay['title'] = item.a.text.strip()
                essay['url'] = 'https:' + item.a['href']
                essay['uid'] = re.search(r'paperid=(.+)&', item.a['href']).group(1)
                essay['abstract'] = item.find('div', class_='c_abstract').text.strip()
                infos = item.find('div', class_='sc_info').find_all('span')
                for info in infos:
                    if re.search(r'(\d{4})年', info.text):
                        essay['publish'] = info.text.replace('年', '').strip()
                    elif '被引量:' in info.text:
                        essay['cite'] = info.text.replace('被引量:', '').strip()
                    elif not info.a or 'journal' in info.a['href']:
                        essay['journal'] = info.text.strip()
                    elif 'author' in info.a['href']:
                        essay['author'] = re.sub(r'\s+', ' ', info.text.strip())
                    else:
                        continue
                total += 1
                table.update_one({"uid": essay["uid"]}, {"$set": essay}, True)
                end = time.time()
                spend = end - start
                unit_spend = spend / total
                print(
                    f"\r进度正在爬取第({total})论文信息数据, 平均用时{round(unit_spend,4)}秒，"
                    f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}. ", end='')
            nxt = soup.find('i', class_='c-icon-pager-next')
            if not nxt:
                has_next = False
            else:
                n += 10
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
    h = "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36"
    c = "Hm_lvt_f28578486a5410f35e6fbd0da5361e5f=1576123001; BAIDUID=3179CBBC74CC1AB8C9047E47521B587F:FG=1; PSTM=1586876295; BIDUPSID=1AAB03EE9D09AB07E4AB9BCFA3E6C96A; BDRCVFR[w2jhEs_Zudc]=mbxnW11j9Dfmh7GuZR8mvqV; delPer=0; BDSVRTM=10; BD_HOME=0; H_PS_PSSID=; Hm_lvt_d0e1c62633eae5b65daca0b6f018ef4c=1587181956; Hm_lpvt_d0e1c62633eae5b65daca0b6f018ef4c=1587181956"
    cr = BaiduScholar(headers=h, cookies=c)
    cr.get_essay_link_by_authorlink(['https://xueshu.baidu.com/scholarID/CN-BB74BNKJ'])