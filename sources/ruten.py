import requests
import re

def search_ruten():
    url = "https://www.ruten.com.tw/find/?q=sony%20mdr%20z1r"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    html = requests.get(url, headers=headers, timeout=10).text

    titles = re.findall(r'"name":"([^"]+)"', html)
    prices = re.findall(r'"price":"(\d+)"', html)

    items = []

    for i in range(min(len(titles), len(prices), 20)):
        items.append({
            "id": f"ruten_{i}_{hash(titles[i])}",
            "title": titles[i],
            "price": int(prices[i]),
            "url": url
        })

    print("Ruten items:", len(items))
    return items
