import requests, os

TOKEN = os.getenv("LINE_TOKEN")
USER = os.getenv("USER_ID")

def send_line(msg):
    requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "to": USER,
            "messages":[{"type":"text","text":msg}]
        }
    )