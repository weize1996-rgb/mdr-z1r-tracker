import os
import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# ===== LINE 發送 =====
def send_line(msg):
    token = os.getenv("LINE_CHANNEL_TOKEN")
    user_id = os.getenv("LINE_USER_ID")

    print(f"👉 準備送 LINE")
    print(f"TOKEN: {token}")
    print(f"USER_ID: {user_id}")

    if not token or not user_id:
        print("❌ LINE ENV 沒設定，跳過發送")
        return

    url = "https://api.line.me/v2/bot/message/push"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    data = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": msg
            }
        ]
    }

    try:
        r = requests.post(url, headers=headers, json=data)
        print("LINE response:", r.status_code, r.text)
    except Exception as e:
        print("❌ LINE 發送失敗:", e)


# ===== 模擬爬蟲 =====
def get_price():
    print("⚠️ 使用 fallback")
    return {
        "title": "Sony MDR-Z1R (fallback)",
        "price": 40000,
        "url": "https://shopee.tw"
    }


# ===== 任務 =====
last_price = None

def job():
    global last_price

    print("\n🔥 JOB START")

    item = get_price()
    price = item["price"]

    print("🏆 最低價:", item)

    if last_price is None or price < last_price:
        print("✅ 新低價")
        msg = f"{item['title']}\n💰 {price}\n{item['url']}"
        send_line(msg)
        last_price = price
    else:
        print("💤 價格沒變")

    print("🏁 JOB END\n")


# ===== scheduler =====
scheduler = BackgroundScheduler()
scheduler.add_job(job, "interval", minutes=5)
scheduler.start()


# ===== 路由 =====
@app.route("/")
def home():
    return "OK"


@app.route("/test")
def test():
    job()
    return "OK"
