import datetime as dt
import re

import requests
from requests.exceptions import SSLError, ProxyError, ChunkedEncodingError, ReadTimeout, ConnectTimeout, ConnectionError


def req_get(url, header, cookie=None, proxy=None):
    r = requests.models.Response()
    n = 0
    # 尝试获取问诊标签
    if proxy:
        commend = "requests.get(url, headers=header, proxies=proxy, timeout=10, verify=False)"
    elif cookie:
        commend = "requests.get(url, headers=header, cookies=cookie, timeout=10, verify=False)"
    else:
        commend = "requests.get(url, headers=header, timeout=10)"
    while n < 10:
        try:
            # r = requests.get(url, headers=header, cookies=cookie, verify=False)
            r = eval(commend)
            break
        except (SSLError, ProxyError, ChunkedEncodingError, ReadTimeout, ConnectTimeout, ConnectionError):
            n += 1
            print(f'\r遇到异常, 第{n}次重新尝试中...', end='')
            continue
    if r.status_code == 200:
        print(f'\r', end='')
        return r
    else:
        print(f'\r', end='')
        return None


def get_proxies(user='H2M12R22R225AQ9D', password='E0186CBE7B689583', host='http-dyn.abuyun.com', port='9020'):
    p = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
        "host": host,
        "port": port,
        "user": user,
        "pass": password,
    }
    ip = {
        "http": p,
        "https": p,
    }
    return ip


def jaccard_similarity(sent1, sent2):
    import re
    if re.search("[\u4e00-\u9fa5]", sent1 + sent2):
        a = set([x for x in sent1])
        b = set([x for x in sent2])
    else:
        a = set(sent1.lower().split())
        b = set(sent2.lower().split())
    c = a.intersection(b)
    return float(len(c)) / (len(a) + len(b) - len(c))


def generate_datelist(start_date, end_date=None):

    if re.match(r'\d{8}', start_date):
        try:
            start_date = dt.datetime.strptime(start_date, '%Y%m%d').date()
        except ValueError:
            raise ValueError("wrong parameter start_date, para should be like 'yyyymmdd'")
    else:
        raise ValueError("wrong parameter start_date, para should be like 'yyyymmdd'")

    if end_date:
        if re.match(r'\d{8}', end_date):
            try:
                end_date = dt.datetime.strptime(end_date, '%Y%m%d').date()
            except ValueError:
                raise ValueError("wrong parameter end_date, para should be like 'yyyymmdd'")
        else:
            raise ValueError("wrong parameter end_date, para should be like 'yyyymmdd'")
    else:
        end_date = dt.date.today()

    day = start_date
    days = list()
    while day < end_date:
        days.append(str(day).replace('-', ''))
        day += dt.timedelta(days=1)

    return days


if __name__ == "__main__":
    d = generate_datelist('20200303')