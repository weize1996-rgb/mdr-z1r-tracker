from sources.shopee import search_shopee
from filter import is_valid, is_used, seen_before
from notify import send_line
from ai_engine import update, score, is_scam, avg

TARGET = 99999

def run():
    print("🔥 run() START")

    # 1️⃣ 抓資料
    items = search_shopee()

    # 2️⃣ fallback（防止抓不到）
    if len(items) == 0:
        print("⚠️ Shopee 沒資料，啟用 fallback")
        items = [{
            "id": "test",
            "title": "Sony MDR-Z1R 測試商品",
            "price": 29000,
            "url": "https://example.com"
        }]

    print("📦 抓到商品數:", len(items))

    # 3️⃣ 開始分析
    for item in items:
        print("👉 檢查商品:", item["title"], item["price"])

        price = item["price"]

        # 更新市場價格
        update(price)

        # 過濾垃圾商品
        if not is_valid(item):
            print("❌ 被 is_valid 擋掉")
            continue

        # 詐騙檢查
        if is_scam(item):
            print("❌ 被判定詐騙")
            continue

        # AI評分
        s = score(item)
        a = avg()

        print("📊 評分:", s, "平均價:", a)

        # 4️⃣ 判斷是否通知
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

    print("🏁 run() END")
