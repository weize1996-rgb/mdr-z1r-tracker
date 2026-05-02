price_history = []

def update(price):
    price_history.append(price)
    if len(price_history) > 100:
        price_history.pop(0)

def avg():
    if not price_history:
        return None
    return sum(price_history) / len(price_history)

def is_low(price):
    a = avg()
    if not a:
        return False
    return price < a * 0.85  # 低於市場15%

def score(item):
    s = 0
    name = item["title"].lower()
    price = item["price"]

    a = avg()
    if a:
        if price < a * 0.8:
            s += 50
        elif price < a * 0.9:
            s += 30

    if any(k in name for k in ["二手","中古","used","9成"]):
        s += 10

    if price < 20000:
        s -= 50  # 可疑

    return s

def is_scam(item):
    name = item["title"].lower()
    price = item["price"]

    if price < 15000:
        return True

    bad = ["模型","空盒","replica","假"]
    return any(b in name for b in bad)
