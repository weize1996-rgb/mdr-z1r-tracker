from flask import Flask
import requests
import time
import redis
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# ===== Redis（Render 要另外開 Redis）=====
r = redis.from_url("你的REDIS_URL")

# ===== LINE =====
LINE_TOKEN = "你的token"

def send_line(msg):
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messages": [{"type": "text", "text": msg}]
    }
    rqs = requests.post(url, headers=headers, json=data)
    print("LINE:", rqs.status_code, rqs.text)


# ===== 爬蟲（示範版，之後可升級）=====
def fetch_shopee():
    print("🟠 Shopee")
    return []

def fetch_yahoo():
    print("🟡 Yahoo")
    return []

def fetch_ruten():
    print("🔵 Ruten")
    return []


def fetch_all():
    items = []
    items += fetch_shopee()
    items += fetch_yahoo()
    items += fetch_ruten()

    if not items:
        print("⚠️ fallback 測試資料")
        items = [{
            "id": "sony-z1r",
            "title": "Sony MDR-Z1R",
            "price": 29000,
            "url": "https://example.com"
        }]
    return items


# ===== 判斷邏輯 =====
COOLDOWN = 60 * 60 * 6  # 6小時
DROP_RATIO = 0.95

def should_notify(item):
    key = f"item:{item['id']}"
    now = int(time.time())

    last_time = r.get(f"{key}:time")
    last_price = r.get(f"{key}:price")

    # 冷卻
    if last_time and now - int(last_time) < COOLDOWN:
        print("⏳ 冷卻中")
        return False

    # 價格判斷
    if last_price:
        last_price = int(last_price)
        if item["price"] >= last_price * DROP_RATIO:
            print("💤 沒降價")
            return False

    return True


def mark_sent(item):
    key = f"item:{item['id']}"
    now = int(time.time())

    r.set(f"{key}:time", now)
    r.set(f"{key}:price", item["price"])


# ===== 主流程 =====
def job():
    print("🔥 JOB START")

    items = fetch_all()

    for item in items:
        print("👉", item["title"], item["price"])

        if should_notify(item):
            msg = f"""🔥 AI撿到好價！
💰 {item['price']}
📝 {item['title']}
🔗 {item['url']}"""

            send_line(msg)
            mark_sent(item)
            print("✅ 已發送")
        else:
            print("❌ 略過")

    print("🏁 JOB END\n")


# ===== Scheduler（重點）=====
scheduler = BackgroundScheduler()
scheduler.add_job(job, "interval", minutes=10)  # 每10分鐘跑一次
scheduler.start()


# ===== API =====
@app.route("/")
def home():
    return "running"
