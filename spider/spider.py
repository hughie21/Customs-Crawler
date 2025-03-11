import asyncio
import cloudscraper
from lxml import etree
import re
import json
import pandas as pd
import sys
from config import config

def country_code_to_name(code):
    if code == "":
        return "未知"
    table = pd.read_csv("国家地区代码.csv")
    name = table[table["两字母代码"] == code]["中文简称"].values[0]
    if name:
        return name
    else:
        return code 

def get_search_results(keyword, page=1):
    scraper = cloudscraper.create_scraper()
    search_result = []
    keyword = "+".join(keyword.split())
    url = f"https://www.importyeti.com/api/search?page={page}&q={keyword}"
    payload = {}
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'api_auth': 'true',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Referer': 'https://www.importyeti.com/search?q=C%20%26%20C%20Offset%20Printing&page=1',
    'Cookie': config.importyeti_cookie_searching,
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-GPC': '1',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'TE': 'trailers'
    }
    response = scraper.request("GET", url, headers=headers, data=payload)

    result = response.json()

    

    if len(result["searchResults"]) == 0:
        return search_result
    
    for item in result["searchResults"]:
        t = {}
        t["name"] = item["title"]
        t["country"] = country_code_to_name(item.get("countryCode", ""))
        if item["type"] == "supplier":
            t["type"] = "供应商"
        else:
            t["type"] = "买家"
        t["total"] = item["totalShipments"]
        t["time"] = item["mostRecentShipment"]
        t["url"] = item["url"]
        search_result.append(t)

    return search_result

async def get_search_results_async(keyword, page=1):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, get_search_results, keyword, page)
    return result


def get_custom_info(url):
    scraper = cloudscraper.create_scraper()
    payload = {}
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Cookie': config.importyeti_cookie_details,
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
    
    response = scraper.request("GET", url, headers=headers, data=payload)

    html = etree.HTML(response.text)

    scripts = html.xpath("//script/text()")
    json_str = None
    for i,v in enumerate(scripts):
        if "vendor_table" in v:
            matches = re.search(r"(?<=(self.__next_f.push\())(.*)(?=\))", v)
            if matches:
                json_str = matches.group(0)
            else:
                return None
    else:
        if not json_str:
            return None

    data = json.loads(json_str)

    second_item = data[1]

    json_sub_str = second_item.split(":", 1)[1]

    json_data = json.loads(json_sub_str)
    form = pd.read_excel("template.xlsx")

    print("数据获取成功，开始处理数据")
    tables = json_data[3]["children"][1][3]["organization"]["data"]["vendor_table"]

    names = list(set([x["vendor_name"].strip().lower() for x in tables]))

    form["客户名称"] = pd.Series(names)

    for vendor in tables:
        customer_name = vendor["vendor_name"].strip().lower()
        form.loc[form["客户名称"] == customer_name, "海关提单数"] = vendor["total_shipments_company"]
        form.loc[form["客户名称"] == customer_name, "海关提单时间"] = list(vendor["vendor_time_series"].keys())[-1]
        form.loc[form["客户名称"] == customer_name, "HS Code商品描述"] = vendor["product_descriptions"]
        form.loc[form["客户名称"] == customer_name, "国家"] = vendor["country"]
        if len(vendor["top_companies"]) == 1:
            form.loc[form["客户名称"] == customer_name, "合作供应商1"] = vendor["top_companies"][0]["company_name"]
        elif len(vendor["top_companies"]) == 2:
            form.loc[form["客户名称"] == customer_name, "合作供应商1"] = vendor["top_companies"][0]["company_name"]
            form.loc[form["客户名称"] == customer_name, "合作供应商2"] = vendor["top_companies"][1]["company_name"]
        elif len(vendor["top_companies"]) > 2:
            form.loc[form["客户名称"] == customer_name, "合作供应商1"] = vendor["top_companies"][0]["company_name"]
            form.loc[form["客户名称"] == customer_name, "合作供应商2"] = vendor["top_companies"][1]["company_name"]
            form.loc[form["客户名称"] == customer_name, "合作供应商3"] = vendor["top_companies"][2]["company_name"]

    print("数据处理完成")
    form["海关提单时间"] = pd.to_datetime(form["海关提单时间"], format="%d/%m/%Y")
    return form

async def get_custom_info_async(url):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, get_custom_info, url)
    return result

if __name__ == "__main__":
    print(get_search_results('"Winner Printing"'))