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

if not REDIS_URL:
    raise Exception("❌ REDIS_URL 沒設定")

if not LINE_TOKEN:
    raise Exception("❌ LINE_TOKEN 沒設定")

if not LINE_USER_ID:
    raise Exception("❌ LINE_USER_ID 沒設定")

# ===== Redis =====
r = redis.from_url(REDIS_URL, decode_responses=True)

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
        res = requests.post(url, headers=headers, json=data)
        print("📨 LINE:", res.status_code)
    except Exception as e:
        print("❌ LINE error:", e)


# =========================
# 🟠 Shopee API
# =========================
def fetch_shopee():
    print("🟠 Shopee")

    url = "https://shopee.tw/api/v4/search/search_items"

    params = {
        "by": "relevancy",
        "keyword": "sony mdr z1r",
        "limit": 5,
        "newest": 0
    }

    headers = {"User-Agent": "Mozilla/5.0"}

    items = []

    try:
        res = requests.get(url, params=params, headers=headers)
        data = res.json()

        for item in data.get("items", []):
            info = item["item_basic"]

            price = int(info["price"] / 100000)

            items.append({
                "id": f"shopee-{info['itemid']}",
                "title": info["name"],
                "price": price,
                "url": f"https://shopee.tw/product/{info['shopid']}/{info['itemid']}"
            })

    except Exception as e:
        print("❌ Shopee error:", e)

    return items


# =========================
# 🟡 Yahoo API
# =========================
def fetch_yahoo():
    print("🟡 Yahoo")

    url = "https://tw.buy.yahoo.com/api/v1/search"

    params = {
        "p": "sony mdr z1r"
    }

    headers = {"User-Agent": "Mozilla/5.0"}

    items = []

    try:
        res = requests.get(url, params=params, headers=headers)
        data = res.json()

        for product in data.get("data", [])[:5]:
            items.append({
                "id": f"yahoo-{product['id']}",
                "title": product["name"],
                "price": int(product["price"]),
                "url": product["url"]
            })

    except Exception as e:
        print("❌ Yahoo error:", e)

    return items


# =========================
# 🔵 露天 HTML 爬蟲
# =========================
def fetch_ruten():
    print("🔵 Ruten")

    url = "https://www.ruten.com.tw/find/?q=sony+mdr+z1r"

    headers = {"User-Agent": "Mozilla/5.0"}

    items = []

    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        products = soup.select(".rt-product-card")[:5]

        for p in products:
            title = p.select_one(".rt-product-card-name")
            price = p.select_one(".rt-product-card-price")
            link = p.select_one("a")

            if not title or not price or not link:
                continue

            price_text = price.text.replace(",", "").replace("$", "")

            items.append({
                "id": f"ruten-{link['href']}",
                "title": title.text.strip(),
                "price": int(price_text),
                "url": link["href"]
            })

    except Exception as e:
        print("❌ Ruten error:", e)

    return items


# =========================
# 整合
# =========================
def fetch_all():
    items = []
    items += fetch_shopee()
    items += fetch_yahoo()
    items += fetch_ruten()

    print(f"📦 總數: {len(items)}")
    return items


# =========================
# 判斷邏輯
# =========================
COOLDOWN = 60 * 60 * 6
DROP_RATIO = 0.95

def should_notify(item):
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
    key = f"item:{item['id']}"
    r.set(f"{key}:time", int(time.time()))
    r.set(f"{key}:price", item["price"])


# =========================
# 主任務
# =========================
def job():
    print("🔥 JOB START")

    items = fetch_all()

    for item in items:
        print("👉", item["title"], item["price"])

        if should_notify(item):
            msg = f"""🔥 撿到便宜！
💰 {item['price']}
📝 {item['title']}
🔗 {item['url']}"""

            send_line(msg)
            mark_sent(item)

    print("🏁 JOB END\n")


# =========================
# Scheduler
# =========================
scheduler = BackgroundScheduler()

def start_scheduler():
    scheduler.add_job(job, "interval", minutes=10)
    scheduler.start()
    print("⏰ Scheduler started")


# =========================
# API
# =========================
@app.route("/")
def home():
    return "running"

@app.route("/test")
def test():
    send_line("🧪 測試成功")
    return "ok"


# =========================
# 啟動
# =========================
if __name__ == "__main__":
    start_scheduler()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
