from flask import Flask
import requests
import time
import redis
import os
from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# ===== 環境變數 =====
REDIS_URL = os.environ.get("REDIS_URL")
LINE_TOKEN = os.environ.get("LINE_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")

print("🔥 ENV CHECK LINE_USER_ID =", repr(LINE_USER_ID))

if not REDIS_URL:
    raise Exception("❌ REDIS_URL 沒設定")

if not LINE_TOKEN:
    raise Exception("❌ LINE_TOKEN 沒設定")

# ===== Redis =====
r = redis.from_url(REDIS_URL, decode_responses=True)

# ===== 關鍵字 =====
KEYWORDS = [
    "MDR-Z1R",
    "Sony Z1R"
]

# ===== LINE =====
def send_line(msg):
    print("👉 準備送 LINE")
    print("USER_ID:", LINE_USER_ID)

    if not LINE_USER_ID:
        print("❌ LINE_USER_ID 沒設定，跳過發送")
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

    try:
        res = requests.post(url, headers=headers, json=data)
        print("📨 LINE 回應:", res.status_code)
        print("📨 LINE 內容:", res.text)
    except Exception as e:
        print("❌ LINE 發送錯誤:", e)

# ===== 工具 =====
def parse_price(text):
    if not text:
        return None
    text = re.sub(r"[^\d]", "", text)
    return int(text) if text else None

# ===== Shopee（簡化穩定版）=====
def fetch_shopee(keyword):
    print("🟠 Shopee:", keyword)

    try:
        url = "https://shopee.tw/api/v4/search/search_items"
        params = {
            "keyword": keyword,
            "limit": 5
        }

        res = requests.get(url, params=params, timeout=10)
        data = res.json()

        items = []
        for i in data.get("items", []):
            item = i.get("item_basic", {})
            price = item.get("price_min", 0) / 100000

            if price > 0:
                items.append({
                    "id": f"shopee-{item.get('itemid')}",
                    "title": item.get("name"),
                    "price": int(price),
                    "url": f"https://shopee.tw/product/{item.get('shopid')}/{item.get('itemid')}"
                })

        print("Shopee items:", len(items))
        return items

    except Exception as e:
        print("Shopee error:", e)
        return []

# ===== fallback（一定會有資料）=====
def fallback_items():
    print("⚠️ 使用 fallback")
    return [{
        "id": "fallback-1",
        "title": "Sony MDR-Z1R (fallback)",
        "price": 40000,
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
    return min(items, key=lambda x: x["price"]) if items else None

# ===== 通知判斷 =====
def should_notify(item):
    key = f"best:{item['title']}"
    last_price = r.get(key)

    if last_price:
        last_price = int(last_price)
        if item["price"] >= last_price:
            return False

    return True

def mark_price(item):
    key = f"best:{item['title']}"
    r.set(key, item["price"])

# ===== 主任務 =====
def job():
    print("\n🔥 JOB START")

    items = fetch_all()
    best = get_best_price(items)

    if not best:
        print("❌ 沒抓到")
        return

    print("🏆 最低價:", best)

    msg = f"""🔥 最低價
💰 {best['price']}
📝 {best['title']}
🔗 {best['url']}"""

    if should_notify(best):
        send_line(msg)
        mark_price(best)
        print("✅ 已通知")
    else:
        print("💤 價格沒變")

    print("🏁 JOB END\n")

# ===== Scheduler =====
scheduler = BackgroundScheduler()
scheduler.add_job(job, "interval", minutes=10)
scheduler.start()
print("⏰ Scheduler started")

# ===== 測試 API =====
@app.route("/test")
def test():
    job()
    return "OK"

# ===== 首頁 =====
@app.route("/")
def home():
    return "running"

# ===== 啟動 =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
