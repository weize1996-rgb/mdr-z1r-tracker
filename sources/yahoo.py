import requests, re

def search_yahoo():
    url = "https://tw.bid.yahoo.com/search/auction/product?p=sony+mdr+z1r"
    html = requests.get(url).text

    items = []

    for m in re.findall(r'"name":"([^"]+)"', html)[:20]:
        items.append({
            "id": f"yahoo_{hash(m)}",
            "title": m,
            "price": 999999,
            "url": url
        })

    return items
