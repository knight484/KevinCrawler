if __name__ == "__main__":
    import pandas as pd
    from DrVoice import *

    c = 'Hm_lvt_f5b5599fdcae9b1c564fa66762058be6=1588257401; sszztauth=6c4dDfPFniabW4xLOUxdnI2kGUWzSDFHGY42w5DRlLOq87AsCWm_m7Wlc0MOpivdd2vvgZNEJ4nzmYha-3z_4HVkqNROd24OS6OXw43kDVLAv_AoAl79AAw6BoomSptJqF31cQIqmzwd3-GLk_2tNg; sszzt_userid=7999PIYzhluoBzUviB4XRKZMFcf-frjzDOguWVoV4VevHmg; sszzt_username=51aeUjDCv7sDmJk8DjTNl-o1JPOcUVeAKvrtnAE8Y5XAtazNv_V1yGjT0Mk; sszzt_nickname=d20fQ1zS75I7ySnvPza-M8FYAyj04n21BokGJMDNb-mZHXY; sszzt_groupid=621a6OlD7Yd_y9soj9KYW4XRffF1DkWVdy0zqKl6; sszztcookietime=3bd7M29xc0VUhnvszneepcqtUWT880jMz6sIbhorst_F4qjYbAAn; Hm_lpvt_f5b5599fdcae9b1c564fa66762058be6=1588257710'
    h = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36'
    dr = DrVoice(headers=h, cookies=c)
    ids = dr.db['医生信息'].distinct('uid')
    ids = [n for n in range(300000) if n not in ids]
    ids = ids[int(len(ids) / 2):]
    dr.get_doctor_info(n_list=ids)
