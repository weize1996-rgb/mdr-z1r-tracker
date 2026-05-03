from flask import Flask
import requests
import redis
import os
from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup
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

if not LINE_USER_ID:
    raise Exception("❌ LINE_USER_ID 沒設定")

r = redis.from_url(REDIS_URL, decode_responses=True)

KEYWORDS = ["MDR-Z1R", "Sony Z1R"]

# ===== headers（防擋）=====
HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)"
}

# ===== LINE =====
def send_line(msg):
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
        res = requests.post(url, headers=headers, json=data, timeout=10)
        print("📨 LINE:", res.status_code)
    except Exception as e:
        print("❌ LINE錯誤:", e)

# ===== 工具 =====
def parse_price(text):
    if not text:
        return None
    text = re.sub(r"[^\d]", "", text)
    return int(text) if text else None

# ===== Shopee（主力）=====
def fetch_shopee(keyword):
    print("🟠 Shopee:", keyword)

    url = "https://shopee.tw/api/v4/search/search_items"

    params = {
        "keyword": keyword,
        "limit": 20,
        "newest": random.randint(0, 1000)
    }

    try:
        res = requests.get(url, headers=HEADERS, params=params, timeout=10)
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

        print("Shopee:", len(items))
        return items

    except Exception as e:
        print("Shopee error:", e)
        return []

# ===== 露天（簡化穩定版）=====
def fetch_ruten(keyword):
    print("🔵 Ruten:", keyword)

    url = f"https://www.ruten.com.tw/find/?q={keyword}"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        items = []

        for tag in soup.find_all(text=re.compile(r"\$\d+"))[:20]:
            price = parse_price(tag)

            if price and 1000 < price < 200000:
                items.append({
                    "id": f"ruten-{hash(tag)}",
                    "title": tag.strip()[:30],
                    "price": price,
                    "url": url
                })

        print("Ruten:", len(items))
        return items[:5]

    except Exception as e:
        print("Ruten error:", e)
        return []

# ===== fallback =====
def fallback_items():
    print("⚠️ fallback")
    return [{
        "id": "fallback",
        "title": "Sony MDR-Z1R (fallback)",
        "price": 50000,
        "url": "https://example.com"
    }]

# ===== 聚合 =====
def fetch_all():
    all_items = []

    for kw in KEYWORDS:
        all_items += fetch_shopee(kw)
        all_items += fetch_ruten(kw)

    if not all_items:
        all_items = fallback_items()

    print("📦 總數:", len(all_items))
    return all_items

# ===== 比價 =====
def get_best(items):
    return min(items, key=lambda x: x["price"])

# ===== 通知邏輯 =====
def should_notify(item):
    last = r.get("best_price")

    if last:
        if int(last) <= item["price"]:
            return False

    return True

def save_price(item):
    r.set("best_price", item["price"])

# ===== 任務 =====
def job():
    print("🔥 START")

    items = fetch_all()
    best = get_best(items)

    print("🏆", best)

    if should_notify(best):
        msg = f"""🔥 最低價！
💰 {best['price']}
📝 {best['title']}
🔗 {best['url']}"""

        send_line(msg)
        save_price(best)
        print("✅ 已通知")
    else:
        print("💤 無變化")

    print("🏁 END\n")

# ===== 排程 =====
scheduler = BackgroundScheduler()
scheduler.add_job(job, "interval", minutes=10)
scheduler.start()

# ===== API =====
@app.route("/")
def home():
    return "running"

@app.route("/test")
def test():
    job()
    return "OK"

# ===== 啟動 =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
