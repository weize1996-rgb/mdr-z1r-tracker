import requests
import statistics
import os
from flask import Flask
import redis
import hashlib

app = Flask(__name__)

# ===== Redis（Upstash）=====
REDIS_URL = os.getenv("REDIS_URL")
r = redis.from_url(REDIS_URL, decode_responses=True)

# ===== LINE =====
LINE_TOKEN = os.getenv("LINE_TOKEN")

# ===== 發送 LINE =====
def send_line(msg):
    print("🔥 sending LINE:", msg)
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    data = {"message": msg}
    res = requests.post(
        "https://notify-api.line.me/api/notify",
        headers=headers,
        data=data
    )
    print("LINE status:", res.status_code, res.text)

# ===== 去重（防重複通知）=====
def is_sent(item_id):
    return r.get(item_id)

def mark_sent(item_id):
    r.setex(item_id, 86400, "1")  # 1天不重複

def hash_item(name, price):
    return hashlib.md5(f"{name}{price}".encode()).hexdigest()

# ===== Shopee =====
def get_shopee():
    try:
        # ⚠️ 這裡先留空（避免被 ban）
        return []
    except:
        return []

# ===== Ruten =====
def get_ruten():
    try:
        return []
    except:
        return []

# ===== Yahoo =====
def get_yahoo():
    try:
        return []
    except:
        return []

# ===== fallback =====
def fallback():
    return [{
        "name": "Sony MDR-Z1R",
        "price": 29000,
        "condition": "新品",
        "url": "https://example.com"
    }]

# ===== 主邏輯 =====
def run():
    print("🔥 run() START")

    items = []

    shopee = get_shopee()
    print("Shopee items:", len(shopee))
    items += shopee

    ruten = get_ruten()
    print("Ruten items:", len(ruten))
    items += ruten

    yahoo = get_yahoo()
    print("Yahoo items:", len(yahoo))
    items += yahoo

    if not items:
        print("⚠️ 全平台沒資料，啟用 fallback")
        items = fallback()

    print("📦 總商品數:", len(items))

    prices = [i["price"] for i in items if i["price"] > 0]

    if not prices:
        print("❌ 沒有有效價格")
        return

    avg_price = statistics.mean(prices)

    for item in items:
        name = item["name"]
        price = item["price"]
        url = item["url"]
        cond = item.get("condition", "未知")

        item_id = hash_item(name, price)

        print("👉", name, price)

        if is_sent(item_id):
            print("⏩ 已發過，跳過")
            continue

        score = (avg_price - price) / avg_price * 100

        if score > 20:
            msg = f"""
🔥 AI撿到好價！
💰 {price}（市場約 {int(avg_price)}）
📊 便宜 {score:.1f}%
📦 {cond}
📝 {name}
🔗 {url}
"""
            send_line(msg)
            mark_sent(item_id)
            print("✅ 發送:", name)
        else:
            print("❌ 不符合條件")

    print("🏁 run() END")

# ===== 路由 =====
@app.route("/")
def home():
    print("🔥 ROUTE HIT")
    run()
    return "OK"
