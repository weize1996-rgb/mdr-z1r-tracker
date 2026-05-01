import requests

def search_shopee():
    url = "https://shopee.tw/api/v4/search/search_items"
    params = {"keyword": "sony mdr z1r", "limit": 20}

    r = requests.get(url, params=params).json()

    items = []
    for i in r.get("items", []):
        b = i["item_basic"]

        items.append({
            "id": f"shopee_{b['itemid']}",
            "title": b["name"],
            "price": b["price"]/100000,
            "url": f"https://shopee.tw/product/{b['shopid']}/{b['itemid']}"
        })

    return items