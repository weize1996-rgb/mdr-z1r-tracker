import requests

def search_shopee():
    url = "https://shopee.tw/api/v4/search/search_items"

    params = {
        "by": "relevancy",
        "keyword": "sony mdr z1r",
        "limit": 20,
        "newest": 0,
        "order": "desc",
        "page_type": "search"
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    r = requests.get(url, params=params, headers=headers)
    data = r.json()

    items = []

    for i in data.get("items", []):
        item = i["item_basic"]

        price = item["price"] / 100000  # 蝦皮單位

        items.append({
            "id": str(item["itemid"]),
            "title": item["name"],
            "price": int(price),
            "url": f"https://shopee.tw/product/{item['shopid']}/{item['itemid']}"
        })

    return items
