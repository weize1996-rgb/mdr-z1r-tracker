from flask import Flask
import requests
import time
import redis
import os
from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup

app = Flask(__name__)

# ===== 環境變數 =====
REDIS_URL = os.environ.get("REDIS_URL")
LINE_TOKEN = os.environ.get("LINE_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")

print("LINE_USER_ID =", LINE_USER_ID)

# ===== Redis =====
r = None
if REDIS_URL:
    r = redis.from_url(REDIS_URL, decode_responses=True)
else:
    print("⚠️ 沒設定 REDIS_URL（將無法記錄價格）")

# ===== LINE 推播（自動 fallback）=====
def send_line(msg):
    if not LINE_TOKEN:
        print("❌ LINE_TOKEN 沒設定")
        return

    if LINE_USER_ID:
        url = "https://api.line.me/v2/bot/message/push"
        data = {
            "to": LINE_USER_ID,
            "messages": [{"type": "text", "text": msg}]
        }
    else:
        url = "https://api.line.me/v2/bot/message/broadcast"
        data = {
            "messages": [{"type": "text", "text": msg}]
        }

    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        res = requests.post(url, headers=headers, json=data)
        print("📨 LINE:", res.status_code, res.text)
    except Exception as e:
        print("❌ LINE error:", e)


# ===== Shopee 爬蟲（API版）=====
def fetch_shopee():
    print("🟠 Shopee")
    items = []

    try:
        url = "https://shopee.tw/api/v4/search/search_items"
        params = {
            "by": "relevancy",
            "keyword": "MDR-Z1R",
            "limit": 5,
            "newest": 0,
            "order": "asc"
        }

        res = requests.get(url, params=params)
        data = res.json()

        for i in data.get("items", []):
            item = i["item_basic"]
            price = item["price"] // 100000

            items.append({
                "id": f"shopee-{item['itemid']}",
                "title": item["name"],
                "price": price,
                "url": f"https://shopee.tw/product/{item['shopid']}/{item['itemid']}"
            })

    except Exception as e:
        print("❌ Shopee error:", e)

    return items


# ===== Yahoo 爬蟲 =====
def fetch_yahoo():
    print("🟡 Yahoo")
    items = []

    try:
        url = "https://tw.search.yahoo.com/search?p=MDR-Z1R"
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")

        for a in soup.select("h3 a")[:5]:
            title = a.get_text()
            link = a.get("href")

            items.append({
                "id": f"yahoo-{hash(title)}",
                "title": title,
                "price": 0,
                "url": link
            })

    except Exception as e:
        print("❌ Yahoo error:", e)

    return items


# ===== 露天 爬蟲 =====
def fetch_ruten():
    print("🔵 Ruten")
    items = []

    try:
        url = "https://www.ruten.com.tw/find/?q=MDR-Z1R"
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")

        for a in soup.select("a.rt-search-product-name")[:5]:
            title = a.get_text(strip=True)
            link = a.get("href")

            items.append({
                "id": f"ruten-{hash(title)}",
                "title": title,
                "price": 0,
                "url": link
            })

    except Exception as e:
        print("❌ Ruten error:", e)

    return items


# ===== 總抓取 =====
def fetch_all():
    items = []
    items += fetch_shopee()
    items += fetch_yahoo()
    items += fetch_ruten()

    if not items:
        print("⚠️ fallback 測試資料")
        items = [{
            "id": "test-sony",
            "title": "Sony MDR-Z1R",
            "price": 29000,
            "url": "https://example.com"
        }]

    return items


# ===== 判斷邏輯 =====
COOLDOWN = 60 * 60 * 6
DROP_RATIO = 0.95

def should_notify(item):
    if not r:
        return True

    key = f"item:{item['id']}"
    now = int(time.time())

    last_time = r.get(f"{key}:time")
    last_price = r.get(f"{key}:price")

    if last_time and now - int(last_time) < COOLDOWN:
        return False

    if last_price:
        if item["price"] >= int(last_price) * DROP_RATIO:
            return False

    return True


def mark_sent(item):
    if not r:
        return

    key = f"item:{item['id']}"
    now = int(time.time())

    r.set(f"{key}:time", now)
    r.set(f"{key}:price", item["price"])


# ===== 主任務 =====
def job():
    print("🔥 JOB START")

    try:
        items = fetch_all()

        for item in items:
            print("👉", item["title"], item["price"])

            if should_notify(item):
                msg = f"""🔥 好價通知
💰 {item['price']}
📝 {item['title']}
🔗 {item['url']}"""

                send_line(msg)
                mark_sent(item)

    except Exception as e:
        print("❌ JOB ERROR:", e)

    print("🏁 JOB END\n")


# ===== Scheduler（避免重複）=====
scheduler = BackgroundScheduler()

if os.environ.get("RENDER") or os.environ.get("PYTHONUNBUFFERED"):
    scheduler.add_job(job, "interval", minutes=10)
    scheduler.start()
    print("⏰ Scheduler started")


# ===== API =====
@app.route("/")
def home():
    return "running"


@app.route("/test")
def test():
    send_line("✅ 測試成功")
    return "sent"


# ===== 本地用 =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
