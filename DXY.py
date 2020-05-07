import logging
import logging
import time

import pymongo
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

from Base import *

logging.captureWarnings(True)


class DXY:

    def __init__(self, headers, cookies):
        self.header = {headers.split(': ')[0]: headers.split(': ')[1]}
        self.cookie = {}
        for i in cookies.split("; "):
            self.cookie[i.split('=')[0]] = i.split('=')[1]
        mongo = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = mongo['丁香园']
        self.proxy = get_proxies()

    def get_video_link(self):
        """
        获取网站全部视频链接
        :return:
        """
        table = self.db['视频网址']
        table.create_index('uid')

        driver = webdriver.Chrome()
        driver.implicitly_wait(5)
        driver.get('https://e.dxy.cn/broadcast/all/rewrite')
        max_page = int(driver.find_element_by_css_selector("li.number:last-child").text)
        start = time.time()
        n = 0

        for _ in range(max_page):
            items = driver.find_elements_by_css_selector('div.spin__blur > div.row > div')
            for item in items:
                video = dict()
                try:
                    video['主题'] = item.find_element_by_css_selector('h2.cast__theme').text
                    video['机构'] = item.find_element_by_css_selector('h2.cast__hospital').text
                    video['url'] = item.find_element_by_tag_name('a').get_attribute('href')
                except StaleElementReferenceException:
                    continue
                try:
                    video['观看'] = item.find_element_by_class_name('total-views').text.replace('次学习', '')
                except (NoSuchElementException, StaleElementReferenceException):
                    pass
                video['类型'] = video['url'].split('/')[-3]
                video['uid'] = video['url'].split('/')[-1]
                t1 = time.time()
                table.update_one({"uid": video["uid"]}, {"$set": video}, True)
                t2 = time.time()
                n += 1
                end = time.time()
                spend = end - start
                unit_spend = spend / n
                remain = (max_page * 15 - n) * unit_spend
                print(f"\r进度({n}/{max_page * 15})条咨询信息数据, 本次数据存储用时{round(t2 - t1, 6)}秒"
                      f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                      f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')

            nxt = driver.find_element_by_class_name('btn-next')
            nxt.click()
            time.sleep(1)

    def get_live_video(self, url_list):
        table = self.db['直播视频']
        table.create_index('uid')

        driver = webdriver.Chrome()
        driver.implicitly_wait(5)
        start = time.time()

        for n, url in enumerate(url_list):
            video = dict()
            driver.get(url)
            time.sleep(1)
            try:
                video['课程名称'] = driver.find_element_by_class_name('live__title').text
            except NoSuchElementException:
                continue
            video['讲师姓名'] = driver.find_element_by_css_selector('h4.live__anchor > span:first-child').text
            try:
                video['讲师职称'] = driver.find_element_by_class_name('live__professional').text
            except NoSuchElementException:
                pass
            video['讲师单位'] = driver.find_element_by_class_name('live__hospital').text.split(' ')[0]
            if len(driver.find_element_by_class_name('live__hospital').text.split(' ')) > 1:
                video['讲师科室'] = driver.find_element_by_class_name('live__hospital').text.split(' ')[1]
            video['课程简介'] = driver.find_element_by_class_name('live__diff').text
            try:
                video['观看量'] = driver.find_element_by_class_name('total-views').text.replace('次学习', '')
            except NoSuchElementException:
                pass
            try:
                video['内容介绍'] = driver.find_element_by_class_name('col-md-8').text
            except NoSuchElementException:
                video['内容介绍'] = driver.find_element_by_class_name('col-md-12').text
            try:
                video['课程时间'] = driver.find_element_by_class_name('live__time').text
                video['课程概述'] = driver.find_element_by_class_name('live__summary').text
                video['讲师简介'] = driver.find_element_by_class_name('live__lecturer').text
            except NoSuchElementException:
                pass
            video['uid'] = url.split('/')[-1]
            video['url'] = url
            t1 = time.time()
            table.update_one({"uid": video["uid"]}, {"$set": video}, True)
            t2 = time.time()
            n += 1
            end = time.time()
            spend = end - start
            unit_spend = spend / n
            remain = (len(url_list) - n) * unit_spend
            print(f"\r进度({n}/{len(url_list)})条咨询信息数据, 本次数据存储用时{round(t2 - t1, 6)}秒"
                  f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                  f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')


if __name__ == "__main__":
    h = "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36"
    c = 'DXY_USER_GROUP=3; Hm_lvt_8a6dad3652ee53a288a11ca184581908=1586012165; __auc=9b0e8ac417145b142dcf6a2aae5; __utma=1.375619337.1586020735.1586020735.1586020735.1; __utmz=1.1586020735.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); XSRF-TOKEN=isQ5XRiUBwFCb53sI3jVCCguIUr3874YUuEGF6WX; dxy_session=fQ4JG46enbmq3NMyCzgdrdWazAibEqrX7U8ghvpi; _ga=GA1.2.375619337.1586020735; _gid=GA1.2.751806177.1587034700; Hm_lvt_585d79beabf9368e8c8bdcc5a01b3940=1587034701; route_e_biz=4f9c5872296df4c1ecddd0816d7c694b; Hm_lpvt_585d79beabf9368e8c8bdcc5a01b3940=1587034752'
    cr = DXY(headers=h, cookies=c)
    cr.get_live_video()
