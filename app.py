from flask import Flask
import requests
import time
import os
import redis
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# ===== Redis（用環境變數）=====
REDIS_URL = os.environ.get("REDIS_URL")

if not REDIS_URL:
    raise Exception("❌ REDIS_URL 沒設定")

import os

r = redis.from_url(os.environ.get("REDIS_URL"))

# ===== LINE =====
LINE_TOKEN = os.environ.get("LINE_TOKEN")

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


# ===== 爬蟲 =====
def fetch_all():
    print("⚠️ fallback 測試資料")
    return [{
        "id": "sony-z1r",
        "title": "Sony MDR-Z1R",
        "price": 29000,
        "url": "https://example.com"
    }]


# ===== 判斷邏輯 =====
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
        last_price = int(last_price)
        if item["price"] >= last_price * DROP_RATIO:
            return False

    return True


def mark_sent(item):
    key = f"item:{item['id']}"
    now = int(time.time())

    r.set(f"{key}:time", now)
    r.set(f"{key}:price", item["price"])


def job():
    print("🔥 JOB START")

    items = fetch_all()

    for item in items:
        if should_notify(item):
            msg = f"""🔥 AI撿到好價！
💰 {item['price']}
📝 {item['title']}
🔗 {item['url']}"""

            send_line(msg)
            mark_sent(item)
            print("✅ 已發送")

    print("🏁 JOB END\n")


# ✅ 關鍵：只在主進程啟動 scheduler
if os.environ.get("RUN_MAIN") == "true" or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    scheduler = BackgroundScheduler()
    scheduler.add_job(job, "interval", minutes=10)
    scheduler.start()


# ===== API =====
@app.route("/")
def home():
    return "running"
