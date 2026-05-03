import os
import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# ====== ENV ======
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

print("🔥 ENV CHECK")
print("LINE_CHANNEL_ACCESS_TOKEN =", "OK" if LINE_CHANNEL_ACCESS_TOKEN else None)
print("LINE_USER_ID =", LINE_USER_ID)


# ====== LINE 發送 ======
def send_line(msg):
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("❌ LINE env missing，跳過發送")
        return

    url = "https://api.line.me/v2/bot/message/push"

    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": msg}]
    }

    r = requests.post(url, headers=headers, json=data)

    print("📨 LINE status:", r.status_code)
    print("📨 LINE response:", r.text)


# ====== 爬蟲（先用 fallback） ======
def get_price():
    print("⚠️ 使用 fallback")
    return {
        "title": "Sony MDR-Z1R",
        "price": 40000,
        "url": "https://shopee.tw"
    }


last_price = None


# ====== 任務 ======
def job():
    global last_price

    print("\n🔥 JOB START")

    item = get_price()

    if not item:
        print("❌ 沒抓到資料")
        return

    price = item["price"]

    print("🏆 最低價:", price)

    if last_price is None or price < last_price:
        print("👉 準備送 LINE")

        send_line(f"🎧 {item['title']}\n💰 {price}\n{item['url']}")

        last_price = price
        print("✅ 已通知")
    else:
        print("💤 價格沒變")

    print("🏁 JOB END\n")


# ====== Scheduler ======
scheduler = BackgroundScheduler()
scheduler.add_job(job, "interval", minutes=1)
scheduler.start()

print("⏰ Scheduler started")


# ====== Route ======
@app.route("/")
def home():
    return "OK"


@app.route("/test")
def test():
    job()
    return "OK"
