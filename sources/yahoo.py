import requests
import re

def search_yahoo():
    url = "https://tw.bid.yahoo.com/search/auction/product?p=sony+mdr+z1r"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    html = requests.get(url, headers=headers, timeout=10).text

    titles = re.findall(r'"title":"([^"]+)"', html)
    prices = re.findall(r'"price":(\d+)', html)

    items = []

    for i in range(min(len(titles), len(prices), 20)):
        items.append({
            "id": f"yahoo_{i}_{hash(titles[i])}",
            "title": titles[i],
            "price": int(prices[i]),
            "url": url
        })

    print("Yahoo items:", len(items))
    return items
