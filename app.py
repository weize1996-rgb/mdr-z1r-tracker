from flask import Flask
import requests
import redis
import os
from apscheduler.schedulers.background import BackgroundScheduler
import re
import random

app = Flask(__name__)

# ===== 環境變數 =====
REDIS_URL = os.environ.get("REDIS_URL")
LINE_TOKEN = os.environ.get("LINE_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")

if not REDIS_URL:
    raise Exception("❌ REDIS_URL 沒設定")
if not LINE_TOKEN:
    raise Exception("❌ LINE_TOKEN 沒設定")

r = redis.from_url(REDIS_URL, decode_responses=True)

# ===== 關鍵字 =====
KEYWORDS = ["MDR-Z1R", "Sony Z1R"]

# ===== LINE =====
def send_line(msg):
    if not LINE_USER_ID:
        print("⚠️ 沒設定 LINE_USER_ID")
        return

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": msg}]
    }

    res = requests.post(url, headers=headers, json=data)
    print("📨 LINE:", res.status_code, res.text)

# ===== 工具 =====
def parse_price(text):
    text = re.sub(r"[^\d]", "", text)
    return int(text) if text else None

# ===== Shopee（主力）=====
def fetch_shopee(keyword):
    print("🟠 Shopee:", keyword)

    url = "https://shopee.tw/api/v4/search/search_items"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    params = {
        "keyword": keyword,
        "limit": 20,
        "newest": 0,
        "order": "asc"
    }

    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        data = res.json()

        items = []
        for i in data.get("items", []):
            item = i.get("item_basic", {})
            price = item.get("price_min", 0) / 100000

            if price <= 0:
                continue

            items.append({
                "id": f"shopee-{item.get('itemid')}",
                "title": item.get("name"),
                "price": int(price),
                "url": f"https://shopee.tw/product/{item.get('shopid')}/{item.get('itemid')}"
            })

        print("Shopee items:", len(items))
        return items

    except Exception as e:
        print("❌ Shopee error:", e)
        return []

# ===== fallback（保證有資料）=====
def fallback_items():
    print("⚠️ 使用 fallback")

    return [{
        "id": "fallback-1",
        "title": "Sony MDR-Z1R (fallback)",
        "price": random.randint(30000, 50000),
        "url": "https://shopee.tw"
    }]

# ===== 聚合 =====
def fetch_all():
    all_items = []

    for kw in KEYWORDS:
        all_items += fetch_shopee(kw)

    if not all_items:
        all_items = fallback_items()

    print("📦 總商品數:", len(all_items))
    return all_items

# ===== 比價 =====
def get_best_price(items):
    return min(items, key=lambda x: x["price"])

# ===== 通知 =====
def should_notify(item):
    key = f"best_price"
    last = r.get(key)

    if last:
        if item["price"] >= int(last):
            return False

    return True

def save_price(item):
    r.set("best_price", item["price"])

# ===== 任務 =====
def job():
    print("\n🔥 JOB START")

    items = fetch_all()
    best = get_best_price(items)

    print("🏆 最低價:", best)

    msg = f"""🔥 比價更新
💰 {best['price']}
📝 {best['title']}
🔗 {best['url']}"""

    # 強制送（debug用）
    send_line(msg)

    if should_notify(best):
        save_price(best)
        print("✅ 新低價")
    else:
        print("💤 價格沒變")

    print("🏁 JOB END\n")

# ===== Scheduler =====
scheduler = BackgroundScheduler()
scheduler.add_job(job, "interval", minutes=10)
scheduler.start()

# ===== API =====
@app.route("/test")
def test():
    job()
    return "OK"

@app.route("/")
def home():
    return "running"

# ===== 啟動 =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
