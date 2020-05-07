import logging
import random
import time

import pymongo
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys

from Base import *

logging.captureWarnings(True)


class YiXueJie:

    def __init__(self, headers, cookies):
        self.header = {headers.split(': ')[0]: headers.split(': ')[1]}
        self.cookie = {}
        for i in cookies.split("; "):
            self.cookie[i.split('=')[0]] = i.split('=')[1]
        mongo = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = mongo['医学界']
        self.proxy = get_proxies()

        # 登陆
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)
        self.driver.get("https://web.yishengzhan.cn/#/home")
        self.driver.find_element_by_class_name('loginbtn').click()
        self.driver.find_element_by_css_selector('div.content-tab > span:nth-child(2)').click()
        user = self.driver.find_element_by_xpath('//*[@id="app"]/div[2]/div[2]/div/div[2]/div[2]/div[1]/input')
        pswd = self.driver.find_element_by_xpath('//*[@id="app"]/div[2]/div[2]/div/div[2]/div[2]/div[2]/input')
        user.clear()
        user.send_keys("13482426317")
        pswd.clear()
        pswd.send_keys("860606")
        self.driver.find_element_by_class_name("content-btn").click()
        input("继续")

    def get_course_link(self):
        table = self.db['课程网址']
        table.create_index('uid')

        self.driver.get('https://web.yishengzhan.cn/video.html')
        start = time.time()
        n = 0

        while True:
            items = self.driver.find_elements_by_class_name("col-xs-3")
            if len(items) == 0:
                print("元素未加载完成，重试中...")
                continue

            for i in items:
                course = dict()
                course['标签'] = i.find_element_by_class_name("s_tag").text.strip()
                course['标题'] = i.find_element_by_class_name("dTitle").text.strip()
                course['讲师'] = i.find_element_by_class_name("dTeacher").text.strip()
                course['uid'] = i.get_attribute('data-id')
                course['url'] = f'https://web.yishengzhan.cn/video_detail.html?vdoid={course["uid"]}'
                time.sleep(random.random())
                t1 = time.time()
                table.update_one({"uid": course["uid"]}, {"$set": course}, True)
                t2 = time.time()
                end = time.time()
                spend = end - start
                print(f"\r进度{n}..条咨询信息数据, 本次数据存储用时{round(t2 - t1, 6)}秒"
                      f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}. ", end='')

            nxt_btn = self.driver.find_element_by_css_selector('li.next-page > button')
            if not nxt_btn.get_attribute("disabled"):
                while True:
                    try:
                        nxt_btn.click()
                        break
                    except ElementClickInterceptedException:
                        self.driver.find_element_by_tag_name('body').send_keys(Keys.END)
                time.sleep(1)
            else:
                break
        return None

    def get_course_info(self, url_list):
        table = self.db['课程详情']
        table.create_index('uid')

        start = time.time()
        t1 = t2 = int()
        for n, url in enumerate(url_list):
            while True:
                self.driver.get(url)
                time.sleep(1)
                retry = 0
                try:
                    tab = self.driver.find_element_by_link_text("讲师介绍")
                    course = dict()
                    course['url'] = url
                    course['uid'] = url.split('=')[-1]
                    course['课程标题'] = str()
                    while not course['课程标题']:
                        course['课程标题'] = self.driver.find_element_by_class_name('videoTit').text.strip()
                        retry += 1
                        time.sleep(random.random() * 3)
                        if retry > 10:
                            retry = 0
                            break
                    course['课程详情'] = self.driver.find_element_by_class_name('keepBlock').text.strip()
                    course['观看'] = self.driver.find_element_by_class_name('clickCount').text.strip()
                    course['点赞'] = self.driver.find_element_by_class_name('supportNum').text.strip()
                    tab.click()
                    course['讲师姓名'] = self.driver.find_element_by_class_name('proName').text.strip()
                    course['讲师科室'] = self.driver.find_element_by_class_name('keshi').text.strip()
                    course['讲师职称'] = self.driver.find_element_by_class_name('prorank').text.strip()
                    course['讲师介绍'] = str()
                    while not course['讲师介绍']:
                        course['讲师介绍'] = self.driver.find_element_by_css_selector('#profile .keepBlock').text.strip()
                        retry += 1
                        time.sleep(random.random() * 3)
                        if retry > 10:
                            break
                    t1 = time.time()
                    table.update_one({"uid": course["uid"]}, {"$set": course}, True)
                    t2 = time.time()
                    break
                except NoSuchElementException:
                    continue
            n += 1
            end = time.time()
            spend = end - start
            unit_spend = spend / n
            remain = (len(url_list) - n) * unit_spend
            print(f"\r进度({n}/{len(url_list)})条咨询信息数据, 本次数据存储用时{round(t2 - t1, 6)}秒"
                  f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                  f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')
        return None


if __name__ == "__main__":
    h = "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36"
    c = 'acw_tc=707c9fdd15871334981463246e306e925120c3b73489e3054860c427960dfe; Hm_lvt_b4b32a80fe822df6eceef9be77f3512b=1587133503; sajssdk_2015_cross_new_user=1; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2217188875f1b2e6-0109315509ce5a-5313f6f-2073600-17188875f1cad3%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22%24device_id%22%3A%2217188875f1b2e6-0109315509ce5a-5313f6f-2073600-17188875f1cad3%22%7D; uuid=bcc995e4-dee2-460a-9a4d-cccc2e36e195; Hm_lpvt_b4b32a80fe822df6eceef9be77f3512b=1587133617'
    cr = YiXueJie(headers=h, cookies=c)
    cr.get_course_info([])
