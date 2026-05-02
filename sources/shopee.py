import requests
import re

def search_shopee():
    items = []

    try:
        url = "https://shopee.tw/search?keyword=sony%20mdr%20z1r"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }

        html = requests.get(url, headers=headers, timeout=10).text

        # 抓商品名稱
        titles = re.findall(r'"name":"([^"]+)"', html)
        prices = re.findall(r'"price":(\d+)', html)

        for i in range(min(len(titles), len(prices), 20)):
            price = int(prices[i]) // 100000

            items.append({
                "id": f"shopee_{i}_{hash(titles[i])}",
                "title": titles[i],
                "price": price,
                "url": url
            })

    except Exception as e:
        print("❌ Shopee error:", e)

    print("Shopee items:", len(items))
    return items
