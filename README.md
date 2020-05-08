# KevinCrawler
网站数据爬虫
## BaiduScholar - 百度学术
- get_scholar_link: 通过selenium 爬取学者链接，参数为学者姓名列表和机构关键词;
- get_scholar_detail: 通过requests 爬取学者信息，参数为学者链接列表;
- get_essay_link: 通过selenium 爬取论文链接，参数为学者链接列表;
- get_essay_detail: 通过requests 爬取论文信息，参数为论文链接列表
## CDT - 药物临床试验登记和信息公示平台(ChinaDrugTrails)
- get_test: 通过selenium 爬取临床实验信息，参数为试验关键词;
## ChunYu - 春雨医生
- get_hospital_id: 通过requests 爬取医院链接，参数无;
- get_depart_id: 通过requests 爬取科室链接，参数为医院链接列表;
- get_doctor_id: 通过requests 爬取医生链接，参数为科室链接列表;
- get_query_id: 通过requests 爬取问诊链接，参数为医生链接列表;
- get_doctor_info: 通过requests 爬取医生信息，参数为医生链接列表;
- get_query_info: 通过requests 爬取问诊信息，参数为问诊链接列表;
