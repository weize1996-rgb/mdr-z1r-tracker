from sources.shopee import search_shopee
from filter import is_valid, is_used, seen_before
from notify import send_line
from ai_engine import update, score, is_scam, avg

TARGET = 999999

def run():
    print("🔥 run() START")

    items = search_shopee()
    print("📦 抓到商品數:", len(items))

    for item in items:
        print("👉 檢查商品:", item["title"], item["price"])

        price = item["price"]

        update(price)

        if not is_valid(item):
            print("❌ 被 is_valid 擋掉")
            continue

        if is_scam(item):
            print("❌ 被判定詐騙")
            continue

        s = score(item)
        a = avg()

        print("📊 評分:", s, "平均價:", a)

        if (price < TARGET or s > 40) and not seen_before(item["id"]):
            print("✅ 符合條件，準備發送")

            tag = "二手" if is_used(item) else "新品"

            msg = f"""🔥 AI撿到好價！
💰 {price}（市場約 {int(a) if a else '?'}）
📊 評分: {s}
📦 {tag}
📝 {item['title']}
🔗 {item['url']}"""

            send_line(msg)
        else:
            print("❌ 不符合通知條件")
