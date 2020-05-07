from requests.exceptions import SSLError, ProxyError, ChunkedEncodingError, ReadTimeout, ConnectTimeout, ConnectionError
import requests


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
        return r
    else:
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