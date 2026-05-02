from sources.shopee import search_shopee
from sources.ruten import search_ruten
from sources.yahoo import search_yahoo

from filter import is_valid, is_used, seen_before
from notify import send_line
from ai_engine import update, score, is_scam, avg

import time

TARGET = 99999

def run():
    print("🔥 run() START")

    # 1️⃣ 抓所有平台
    items = []

    try:
        items += search_shopee()
    except:
        print("❌ Shopee error")

    try:
        items += search_ruten()
    except:
        print("❌ Ruten error")

    try:
        items += search_yahoo()
    except:
        print("❌ Yahoo error")

    # 2️⃣ fallback
    if len(items) == 0:
        print("⚠️ 全平台沒資料，啟用 fallback")
        items = [{
            "id": f"test_{int(time.time())}",
            "title": "Sony MDR-Z1R 測試商品",
            "price": 29000,
            "url": "https://example.com"
        }]

    print("📦 總商品數:", len(items))

    # 3️⃣ 分析
    for item in items:
        print("👉", item["title"], item["price"])

        price = item["price"]

        update(price)

        if not is_valid(item):
            continue

        if is_scam(item):
            continue

        s = score(item)
        a = avg()

        if (price < TARGET or s > 40) and not seen_before(item["id"]):
            print("✅ 發送:", item["title"])

            tag = "二手" if is_used(item) else "新品"

            msg = f"""🔥 AI撿到好價！
💰 {price}（市場約 {int(a) if a else '?'}）
📊 評分: {s}
📦 {tag}
📝 {item['title']}
🔗 {item['url']}"""

            send_line(msg)

    print("🏁 run() END")
