import asyncio
import time
import requests
from lxml import etree
import re
import pandas as pd
from tqdm import tqdm
from config import config

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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Cookie': config.bing_cookie,
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Sec-GPC': '1',
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

async def get_search_result_async(keyword):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, get_search_result, keyword)
    return result

if __name__ == "__main__":
    print(get_search_result("nu world"))