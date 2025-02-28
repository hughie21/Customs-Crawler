import time
import requests
from lxml import etree
import re
import pandas as pd
from tqdm import tqdm

def get_domain(x):
    if match := re.search(r"https?://([^/]+)", x):
        return match.group(1)
    else:
        return x

def check_useless_web(web):
    skip_web = ["onlydomains", "wikipedia", "facebook", "linkin", "baidu", "youtube", "tiktok", "instagram", "amazon"]
    for sw in skip_web:
        if sw in web:
            return True
    return False

def get_search_result(keyword: str):
    if not isinstance(keyword, str):
        return ""
    keyword = "+".join(keyword.split() + ["official", "website"])

    url = f"https://www.bing.com/search?pc=MOZI&form=MOZLBR&q={keyword}"
    payload = {}
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Connection': 'keep-alive',
    'Cookie': 'MUIDB=02D5D3F7E11B62641E79C69BE01363D2; USRLOC=HS=1&ELOC=LAT=23.00850486755371|LON=113.337890625|N=%E7%95%AA%E7%A6%BA%E5%8C%BA%EF%BC%8C%E5%B9%BF%E4%B8%9C%E7%9C%81|ELT=4|&DLOC=LAT=23.011241|LON=113.3417824|A=23.059|N=Panyu+District%2c+Guangzhou|C=|S=|TS=241212084329|ETS=241212091916|; SRCHUSR=DOB=20250106&T=1739330487000; _RwBf=r=0&ilt=15745&ihpd=0&ispd=62&rc=200&rb=0&gb=0&rg=200&pc=200&mtu=0&rbb=0&g=0&cid=&clo=0&v=62&l=2025-02-11T08:00:00.0000000Z&lft=2024-12-26T00:00:00.0000000-08:00&aof=0&o=2&p=&c=&t=0&s=0001-01-01T00:00:00.0000000+00:00&ts=2025-02-12T03:30:03.7388375+00:00&rwred=0&wls=&wlb=&lka=0&lkt=0&TH=&aad=0&ccp=&wle=&ard=0001-01-01T00:00:00.0000000&rwdbt=0&rwflt=0&cpt=&rwaul2=0; SRCHHPGUSR=SRCHLANG=zh-Hans&IG=5B9503345E524B6D91AE0814D8F8BB3A&DM=1&BRW=M&BRH=S&CW=1279&CH=354&SCW=1261&SCH=3598&DPR=1.5&UTC=480&EXLTT=31&WTS=63874927287&HV=1739331004&PRVCW=1279&PRVCH=560&AV=14&ADV=14&RB=1739327072482&MB=1739327072483&CIBV=1.1816.0; _tarLang=default=zh-Hans&newFeature=tonetranslation; _TTSS_IN=isADRU=0&hist=WyJlcyIsImZyIiwiZW4iLCJhdXRvLWRldGVjdCJd; _TTSS_OUT=hist=WyJlbiIsInpoLUhhbnQiLCJ6aC1IYW5zIl0=; MUID=02D5D3F7E11B62641E79C69BE01363D2; SRCHD=AF=QBRE; SRCHUID=V=2&GUID=4F1D077E81CC4C418C7791D677AF17F9&dmnchg=1; MMCASM=ID=24D8B9F9C0884778B44FE15AEE511553; _HPVN=CS=eyJQbiI6eyJDbiI6MTIsIlN0IjowLCJRcyI6MCwiUHJvZCI6IlAifSwiU2MiOnsiQ24iOjEyLCJTdCI6MCwiUXMiOjAsIlByb2QiOiJIIn0sIlF6Ijp7IkNuIjoxMiwiU3QiOjAsIlFzIjowLCJQcm9kIjoiVCJ9LCJBcCI6dHJ1ZSwiTXV0ZSI6dHJ1ZSwiTGFkIjoiMjAyNS0wMS0wNFQwMDowMDowMFoiLCJJb3RkIjowLCJHd2IiOjAsIlRucyI6MCwiRGZ0IjpudWxsLCJNdnMiOjAsIkZsdCI6MCwiSW1wIjoyMiwiVG9ibiI6MH0=; _UR=QS=0&TQS=0&OMD=13383800614&Pn=0; MSPTC=ngTpH3ICuUtr8Uf5v_0bcCrUqeAfOL8P0HsFG6yvPLs; TRBDG=FIMPR=1; TTRSL=ja; MUIDB=3099CC000A386E152DD1DF9D0B7B6FA1; BFBUSR=CMUID=3099CC000A386E152DD1DF9D0B7B6FA1; _EDGE_V=1; MSCCSC=1; SNRHOP=I=&TS=; _EDGE_S=SID=3560F8C20BC46232158BED530AA263F9&mkt=zh-cn; _SS=PC=MOZI&SID=3560F8C20BC46232158BED530AA263F9&R=200&RB=0&GB=0&RG=200&RP=200; _Rwho=u=d&ts=2025-02-12; ipv6=hit=1739334233252&t=4; BFPRResults=FirstPageUrls=19BA1BD1DFAA0085151B95ADDB6D6076&FPIG=B2234672866A4EDA8B46DD2DF0D58B48; ak_bmsc=7E2126714E1368E59F3E249C2BC82B6C~000000000000000000000000000000~YAAQyrkhF0ju6NOUAQAAyi8v+Bq2xPqdZPC6CZ0hjAsV+r+6MEgRMEx9NmA7fIu9BCTChMKswPlOIMv8aCMKehrDJxnGGt5HYcY55UU1TlRf865EnQN0VIxBTDQtyPPL2yhRT0l96obk1DW6opNmT8cfBi45iOA0UlwUpwMzSJsKFsAtuFjspfR18VGbRKRXPIDSdVAE+plwUafaZtKOUndPRR4tEMZ7B4Po/lv1o3DmcqWCU84Su+NrJj1fzpnRZeUxOBkCjKRSCaiHNJeQ1+seq0mfj5oMwjfowslEdUwOfTimL14Z1WS69ZtJTUYx9qZiKrJ7xSMyAvQidqB7iUuwXADD5xOXmmLq/ojYKeZNpPbyWkaM1qxGqOD5TzGluQsK+EtFwA==; _C_ETH=1; dsc=order=BingPages; SRCHS=PC=MOZI; SRCHHPGUSR=SRCHLANG=zh-Hans&HV=1729222965&BRW=M&BRH=S&CW=1278&CH=326&SCW=1261&SCH=3059&DPR=1.5&UTC=480&DM=1&WTS=63864818247&PRVCW=1278&PRVCH=326&EXLTT=31&IG=03B1B5390B70416D90E1B2C3EC5E1C00&CIBV=1.1814.0&CMUID=3099CC000A386E152DD1DF9D0B7B6FA1&AV=14&ADV=14&RB=1727751988365&MB=1727751988366&THEME=0&WEBTHEME=0; MUIDB=215588CE4EB66E0B2ACC9DFF4FBE6F36',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Priority': 'u=0, i',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'TE': 'trailers'
    }
    try:
        response = requests.request("GET", url, headers=headers, data=payload)
        response.raise_for_status()
    except Exception as e:
        for i in range(5):
            try:
                response = requests.request("GET", url, headers=headers, data=payload)
            except:
                time.sleep(1)
                continue
            if response.status_code == 200:
                break
            time.sleep(1)
        return None

    html = etree.HTML(response.text)
    try:
        domains = html.xpath("//cite")
        for domain in domains:
            domain_text = domain.xpath("string(.)").replace(" › ", "/")
            if not check_useless_web(domain_text):
                return domain_text
    except:
        return ""
    return ""

if __name__ == "__main__":
    data = pd.read_excel("莫斯科书展(manilabookfair.com)-53.xlsx")
    names = list(data[pd.isna(data["官网"])]["客户名称"].values)

    for i in tqdm(range(len(names))):
        name = names[i]
        web = get_search_result(name)
        if pd.isna(data.loc[data["客户名称"] == name, "官网"]).any() and web:
            data.loc[data["客户名称"] == name, "官网"] = web
    data.to_excel("莫斯科书展(manilabookfair.com)-53.xlsx", index=False)