import pymongo
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException


class CDT:
    def __init__(self, headers, cookies):
        self.header = {headers.split(': ')[0]: headers.split(': ')[1]}
        self.cookie = {}
        for i in cookies.split("; "):
            self.cookie[i.split('=')[0]] = i.split('=')[1]
        mongo = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = mongo['药物临床实验登记与信息公示平台']

    def get_test(self, keyword=None):
        table = self.db['临床试验']
        start_url = 'http://www.chinadrugtrials.org.cn/eap/clinicaltrials.searchlist'
        driver = webdriver.Chrome()
        driver.get(start_url)
        driver.implicitly_wait(10)
        if keyword:
            search_bar = driver.find_element_by_xpath('//*[@id="searchfrm"]/div/div[1]/div[1]/input[1]')
            search_btn = driver.find_element_by_id('button')
            search_bar.send_keys(keyword)
            search_btn.click()
        driver.find_element_by_css_selector('table.Tab > tbody a').click()
        n = 1
        while True:
            test = {'': ''}
            key = str()
            driver.find_element_by_css_selector('tr.Tab_title input').click()
            basic = driver.find_element_by_class_name('cxtj_tm').find_elements_by_tag_name('td')
            for b in basic:
                if b.get_attribute('align') == 'right':
                    key = b.text.replace('：', '').strip()
                else:
                    test[key] = b.text
                    key = ''
            tables = driver.find_elements_by_css_selector('#div_open_close_01 > table')
            for i in tables[0].find_elements_by_tag_name('td'):
                if i.get_attribute('align') == 'left':
                    key = i.text.replace('：', '').strip()
                else:
                    test[key] = i.text
                    key = ''
            for i in tables[1].find_elements_by_xpath('./tr/td'):
                if i.get_attribute('align') == 'left':
                    key = i.text.replace('：', '').strip()
                else:
                    test[key] = i.text
                    key = ''
            for e, i in enumerate(
                    tables[2].find_elements_by_css_selector('tbody tbody')[1].find_elements_by_xpath('./tr/td')):
                if e % 3 == 1:
                    key = i.text.replace('：', '').strip()
                elif e % 3 == 2:
                    test[key] = i.text
                else:
                    pass
            for i in tables[5].find_elements_by_css_selector('tbody tbody')[1].find_elements_by_xpath('./tr/td'):
                if i.get_attribute('align') == 'center':
                    key = i.text.replace('：', '').strip()
                else:
                    test[key] = i.text
                    key = ''
            test['uid'] = test['登记号']
            del test['']
            table.update_one({'uid': test['uid']}, {"$set": test}, True)
            print(f"\r已爬取{n}条临床信息...")
            try:
                driver.find_element_by_class_name('next_test').click()
                n += 1
            except NoSuchElementException:
                break
        return None


if __name__ == '__main__':
    header = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'
    cookie = 'UM_distinctid=171299b3453e3-00fd68ebf57018-4313f6a-1fa400-171299b3454377; CNZZDATA1256895572=1181329185-1585536870-null%7C1585925095; JSESSIONID=0000_Lkr467vWAQIQFCz06B1QCA:-1'
    cr = CDT(headers=header, cookies=cookie)
    cr.get_test(keyword='肺动脉高压')
