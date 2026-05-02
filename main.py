from flask import Flask
import requests
import time
import os
import redis
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# ====== 環境變數 ======
LINE_TOKEN = os.getenv("LINE_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")

if not LINE_TOKEN:
    raise Exception("❌ LINE_TOKEN 沒設定")

if not REDIS_URL:
    raise Exception("❌ REDIS_URL 沒設定")

# ====== Redis ======
r = redis.from_url(REDIS_URL, decode_responses=True)

# ====== 參數 ======
COOLDOWN = 60 * 60 * 6       # 6小時
DROP_RATIO = 0.95           # 低於95%才通知

# ====== LINE 發送 ======
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
        res = requests.post(url, headers=headers, json=data, timeout=10)
        print("📨 LINE:", res.status_code, res.text)
    except Exception as e:
        print("❌ LINE 發送錯誤:", e)


# ====== 爬蟲（你之後填實作） ======
def fetch_shopee():
    print("🟠 Shopee items: 0")
    return []

def fetch_yahoo():
    print("🟡 Yahoo items: 0")
    return []

def fetch_ruten():
    print("🔵 Ruten items: 0")
    return []


def fetch_all():
    items = []
    items += fetch_shopee()
    items += fetch_yahoo()
    items += fetch_ruten()

    if not items:
        print("⚠️ 全平台沒資料，啟用 fallback")
        items = [{
            "id": "sony-z1r",
            "title": "Sony MDR-Z1R 測試商品",
            "price": 29000,
            "url": "https://example.com"
        }]

    print(f"📦 總商品數: {len(items)}")
    return items


# ====== 通知判斷 ======
def should_notify(item):
    key = f"item:{item['id']}"
    now = int(time.time())

    last_time = r.get(f"{key}:time")
    last_price = r.get(f"{key}:price")

    # ===== 冷卻 =====
    if last_time:
        if now - int(last_time) < COOLDOWN:
            print("⏳ 冷卻中:", item["title"])
            return False

    # ===== 價格判斷 =====
    if last_price:
        last_price = int(last_price)
        if item["price"] >= last_price * DROP_RATIO:
            print("💤 沒有明顯降價:", item["title"])
            return False

    return True


def mark_sent(item):
    key = f"item:{item['id']}"
    now = int(time.time())

    r.set(f"{key}:time", now)
    r.set(f"{key}:price", item["price"])


# ====== 主任務 ======
def run_job():
    print("\n🔥 JOB START")

    try:
        items = fetch_all()

        for item in items:
            print(f"👉 檢查商品: {item['title']} {item['price']}")

            if should_notify(item):
                msg = f"""🔥 AI撿到好價！
💰 {item['price']}
📝 {item['title']}
🔗 {item['url']}"""

                send_line(msg)
                mark_sent(item)
                print("✅ 發送成功")

            else:
                print("❌ 略過")

    except Exception as e:
        print("❌ JOB ERROR:", e)

    print("🏁 JOB END\n")


# ====== Scheduler（重點）=====
scheduler = BackgroundScheduler()
scheduler.add_job(run_job, "interval", minutes=10)  # 每10分鐘跑一次
scheduler.start()


# ====== API ======
@app.route("/")
def home():
    return "OK"


@app.route("/run")
def manual_run():
    run_job()
    return "Triggered"


# ====== Render 啟動用 ======
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
