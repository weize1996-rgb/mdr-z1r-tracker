from sources.shopee import search_shopee
from filter import is_valid, is_used, seen_before
from notify import send_line
from ai_engine import update, score, is_scam, avg

TARGET = 50000

def run():
    items = search_shopee()

    for item in items:
        price = item["price"]

        update(price)

        if not is_valid(item):
            continue

        if is_scam(item):
            continue

        s = score(item)
        a = avg()

        if (price < TARGET or s > 40) and not seen_before(item["id"]):
            tag = "二手" if is_used(item) else "新品"

            msg = f"""🔥 AI撿到好價！
💰 {price}（市場約 {int(a) if a else '?'}）
📊 評分: {s}
📦 {tag}
📝 {item['title']}
🔗 {item['url']}"""

            send_line(msg)
