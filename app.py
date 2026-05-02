from flask import Flask
import requests
import time
import redis
import os
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# ===== 環境變數 =====
REDIS_URL = os.environ.get("REDIS_URL")
LINE_TOKEN = os.environ.get("LINE_TOKEN")

if not REDIS_URL:
    raise Exception("❌ REDIS_URL 沒設定")

if not LINE_TOKEN:
    raise Exception("❌ LINE_TOKEN 沒設定")

# ===== Redis =====
r = redis.from_url(REDIS_URL, decode_responses=True)

# ===== LINE 推播 =====
def send_line(msg):
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messages": [{"type": "text", "text": msg}]
    }

    try:
        res = requests.post(url, headers=headers, json=data)
        print("📨 LINE:", res.status_code, res.text)
    except Exception as e:
        print("❌ LINE 發送錯誤:", e)

# ===== 爬蟲（先用假資料）=====
def fetch_all():
    print("⚠️ 使用 fallback 測試資料")
    return [{
        "id": "sony-z1r",
        "title": "Sony MDR-Z1R",
        "price": 29000,
        "url": "https://example.com"
    }]

# ===== 判斷邏輯 =====
COOLDOWN = 60 * 60 * 6  # 6小時
DROP_RATIO = 0.95

def should_notify(item):
    key = f"item:{item['id']}"
    now = int(time.time())

    last_time = r.get(f"{key}:time")
    last_price = r.get(f"{key}:price")

    if last_time:
        if now - int(last_time) < COOLDOWN:
            print("⏳ 冷卻中")
            return False

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

# ===== 主任務 =====
def job():
    print("🔥 JOB START")

    try:
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

    except Exception as e:
        print("❌ JOB ERROR:", e)

    print("🏁 JOB END\n")

# ===== Scheduler（避免重複啟動）=====
scheduler = BackgroundScheduler()

def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(job, "interval", minutes=10)
        scheduler.start()
        print("⏰ Scheduler started")

# ===== API =====
@app.route("/")
def home():
    return "✅ running"

# ===== Render 啟動 =====
if __name__ == "__main__":
    start_scheduler()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
