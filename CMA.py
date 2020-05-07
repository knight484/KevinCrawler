import re

import pymongo
from selenium import webdriver


class CMA:

    def __init__(self, headers, cookies):
        self.header = {headers.split(': ')[0]: headers.split(': ')[1]}
        self.cookie = {}
        for i in cookies.split("; "):
            self.cookie[i.split('=')[0]] = i.split('=')[1]
        mongo = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = mongo['中华医学会']

    def get_association(self):
        table = self.db['委员名单']
        driver = webdriver.Chrome()
        driver.implicitly_wait(3)
        start_url = 'https://www.cma.org.cn/col/col183/index.html'
        driver.get(start_url)
        driver.switch_to.frame('showIframe')
        items = driver.find_elements_by_css_selector('table.table2 a')
        urls = []
        for i in items:
            urls.append(i.get_attribute('href'))

        for e, u in enumerate(urls):
            doctor = dict()
            driver.get(u)
            doctor['专科分会'] = re.search(r'中华医学会(.+分会)', driver.find_element_by_class_name('title').text).group(1)
            doctor['来源'] = u
            doctor['届次'] = str()
            print(f"({e+1}/{len(urls)})正在爬取{doctor['专科分会']}名单...")
            content = driver.find_element_by_id('zoom').find_elements_by_tag_name('p')
            for con in content:
                if re.search(r'\d+年\d+月', con.text):
                    doctor['换届时间'] = re.search(r'(\d+年\d+月)', con.text).group(1)
                elif re.search(r'第.+届委员会', con.text):
                    doctor['届次'] = re.search(r'第(.+)届委员会', con.text).group(1)
                else:
                    text = re.split(r'[:：]', con.text)
                    if len(text) > 1:
                        doctor['职务'] = re.sub(r'[(（].+[)）]', '', text[0])
                        names = re.sub(r'[\s、]+', ' ', text[1])
                    else:
                        names = re.sub(r'[\s、]+', ' ', text[0])
                    names = re.findall(r'[^ ]{2,}|[^ ] [^ ]', names)
                    for n in names:
                        doctor['姓名'] = n.replace(' ', '')
                        doctor['uid'] = doctor['届次'] + '届' + doctor['专科分会'] + '_' + doctor['职务'] + doctor['姓名']
                        table.update_one({'uid': doctor['uid']}, {"$set": doctor}, True)


if __name__ == "__main__":
    h = "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36"
    c = "a=k; b=10"
    cr = CMA(headers=h, cookies=c)
    cr.get_association()
