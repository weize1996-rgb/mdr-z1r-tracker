import requests, re

def search_ruten():
    url = "https://www.ruten.com.tw/find/?q=sony+mdr+z1r"
    html = requests.get(url).text

    items = []

    # 簡單抓標題（示意用，夠用就好）
    for m in re.findall(r'data-name="([^"]+)"', html)[:20]:
        items.append({
            "id": f"ruten_{hash(m)}",
            "title": m,
            "price": 999999,  # 露天這版先不抓價格（避免被擋）
            "url": url
        })

    return items
