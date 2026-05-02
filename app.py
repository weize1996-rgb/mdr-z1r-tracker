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

# ===== LINE =====
def send_line(msg):
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messages": [{"type": "text", "text": msg}]
    }

    res = requests.post(url, headers=headers, json=data)
    print("📨 LINE:", res.status_code, res.text)

# ===== 模擬爬蟲（之後可換真的）=====
def fetch_all():
    return [
        {
            "id": "sony-z1r",
            "title": "Sony MDR-Z1R",
            "price": 29000,
            "url": "https://example.com"
        }
    ]

# ===== 邏輯 =====
DROP_RATIO = 0.95  # 降5%

def should_notify(item):
    key = f"item:{item['id']}"

    last_price = r.get(f"{key}:price")

    # 🆕 新商品（沒紀錄）
    if not last_price:
        print("🆕 新商品")
        return True, "new"

    last_price = int(last_price)

    # 📉 降價
    if item["price"] < last_price * DROP_RATIO:
        print("📉 有降價")
        return True, "drop"

    print("💤 無變化")
    return False, None


def mark_item(item):
    key = f"item:{item['id']}"
    r.set(f"{key}:price", item["price"])


# ===== 主任務 =====
def job():
    print("🔥 JOB START")

    try:
        items = fetch_all()

        for item in items:
            print("👉", item["title"], item["price"])

            notify, reason = should_notify(item)

            if notify:
                if reason == "new":
                    tag = "🆕 新上架"
                elif reason == "drop":
                    tag = "📉 降價"
                else:
                    tag = ""

                msg = f"""{tag}
💰 {item['price']}
📝 {item['title']}
🔗 {item['url']}"""

                send_line(msg)
                mark_item(item)
                print("✅ 已發送")
            else:
                print("❌ 略過")

    except Exception as e:
        print("❌ JOB ERROR:", e)

    print("🏁 JOB END\n")


# ===== Scheduler =====
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

# 手動測試
@app.route("/test")
def test():
    send_line("🚀 測試通知")
    return "sent"

# 清空 Redis（重置狀態）
@app.route("/reset")
def reset():
    r.flushall()
    return "redis cleared"


# ===== 啟動 =====
if __name__ == "__main__":
    start_scheduler()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
