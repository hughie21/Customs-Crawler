import asyncio
import requests
import json
from config import coniguration

def get_company_intro(name, web):
    url = "https://ark.cn-beijing.volces.com/api/v3/bots/chat/completions"

    payload = json.dumps({
    "model": "bot-20250304111228-6nf52",
    "stream": False,
    "stream_options": {
        "include_usage": True
    },
    "messages": [
        {
        "role": "user",
        "content": f"企业名称：{name}\n企业官网：{web}"
        }
    ]
    })
    headers = {
    'Authorization': f'Bearer {coniguration["api_key"]}',
    'Content-Type': 'application/json'
    }
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
    except:
        return None
    
    data = response.json()
    if len(data["choices"]) == 0:
        return None
    
    content = data["choices"][0]["message"]["content"].replace("\n", "")

    return content

def translate_goods(content):
    url = "https://ark.cn-beijing.volces.com/api/v3/bots/chat/completions"
    payload = json.dumps({
    "model": "bot-20250304155348-94wnh",
    "stream": False,
    "stream_options": {
        "include_usage": True
    },
    "messages": [
        {
        "role": "user",
        "content": content
        }
    ]
    })
    headers = {
    'Authorization': f'Bearer {coniguration["api_key"]}',
    'Content-Type': 'application/json'
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
    except:
        return None

    data = response.json()
    if len(data["choices"]) == 0:
        return None
    
    content = data["choices"][0]["message"]["content"].replace("\n", "")

    return content

async def translate_goods_async(content):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, translate_goods, content)
    return result

async def get_company_intro_async(name, web):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, get_company_intro, name, web)
    return result