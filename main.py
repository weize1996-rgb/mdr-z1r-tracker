from sources.shopee import search_shopee
from filter import is_valid, is_used, seen_before
from notify import send_line

TARGET = 999999

def run():
    items = search_shopee()

    for item in items:
        if not is_valid(item):
            continue

        if item["price"] < TARGET and not seen_before(item["id"]):
            tag = "二手" if is_used(item) else "新品"

            msg = f"""🔥 MDR-Z1R 降價（{tag}）
💰 {item['price']}
📝 {item['title']}
🔗 {item['url']}"""

            send_line(msg)
