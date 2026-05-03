import os
import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# ===== ENV =====
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

print("🔥 ENV CHECK")
print("LINE_TOKEN =", "OK" if LINE_TOKEN else None)
print("LINE_USER_ID =", LINE_USER_ID)


# ===== LINE =====
def send_line(msg):
    if not LINE_TOKEN or not LINE_USER_ID:
        print("❌ LINE env missing")
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

    r = requests.post(url, headers=headers, json=data)

    print("📨 LINE:", r.status_code, r.text)


# ===== Shopee 抓取（穩定版） =====
def shopee_search(keyword):
    print(f"🟠 Shopee: {keyword}")

    url = "https://shopee.tw/api/v4/search/search_items"

    params = {
        "by": "relevancy",
        "keyword": keyword,
        "limit": 20,
        "newest": 0,
        "order": "asc",
        "page_type": "search"
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": f"https://shopee.tw/search?keyword={keyword}"
    }

    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)

        if res.status_code != 200:
            print("❌ Shopee status:", res.status_code)
            return []

        data = res.json()

        items = []

        for i in data.get("items", []):
            item = i.get("item_basic", {})

            price = item.get("price", 0) / 100000  # Shopee 價格格式

            items.append({
                "id": item.get("itemid"),
                "title": item.get("name"),
                "price": int(price),
                "url": f"https://shopee.tw/product/{item.get('shopid')}/{item.get('itemid')}"
            })

        print("Shopee items:", len(items))
        return items

    except Exception as e:
        print("❌ Shopee error:", e)
        return []


# ===== 抓最低價 =====
def get_best_price():
    keywords = ["MDR-Z1R", "Sony Z1R"]

    all_items = []

    for kw in keywords:
        all_items += shopee_search(kw)

    if not all_items:
        print("⚠️ fallback")
        return {
            "title": "Sony MDR-Z1R (fallback)",
            "price": 40000,
            "url": "https://shopee.tw"
        }

    best = min(all_items, key=lambda x: x["price"])

    print("📦 總商品:", len(all_items))
    print("🏆 最低價:", best)

    return best


# ===== 任務 =====
last_price = None

def job():
    global last_price

    print("\n🔥 JOB START")

    item = get_best_price()
    price = item["price"]

    if last_price is None or price < last_price:
        print("👉 發送 LINE")

        msg = f"🎧 {item['title']}\n💰 {price}\n{item['url']}"
        send_line(msg)

        last_price = price
    else:
        print("💤 價格沒變")

    print("🏁 JOB END\n")


# ===== Scheduler =====
scheduler = BackgroundScheduler()
scheduler.add_job(job, "interval", minutes=5)
scheduler.start()

print("⏰ Scheduler started")


# ===== 路由 =====
@app.route("/")
def home():
    return "OK"


@app.route("/test")
def test():
    job()
    return "OK"
