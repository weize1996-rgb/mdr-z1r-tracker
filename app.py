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
r = redis.from_url(
    REDIS_URL,
    decode_responses=True
)

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


# ===== 爬蟲（先用假資料，之後可擴充）=====
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
DROP_RATIO = 0.95       # 降價 5%

def should_notify(item):
    key = f"item:{item['id']}"
    now = int(time.time())

    last_time = r.get(f"{key}:time")
    last_price = r.get(f"{key}:price")

    # 冷卻時間
    if last_time:
        if now - int(last_time) < COOLDOWN:
            print("⏳ 冷卻中")
            return False

    # 價格變化
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


# ===== Scheduler =====
scheduler = BackgroundScheduler()
scheduler.add_job(job, "interval", minutes=10)
scheduler.start()


# ===== Web API =====
@app.route("/")
def home():
    return "✅ running"


# ===== Render 啟動 =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)            send_line(msg)
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
