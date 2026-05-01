def send_line(msg):
    print("🔥 sending LINE:", msg)

    import requests, os
    TOKEN = os.getenv("LINE_TOKEN")
    USER = os.getenv("USER_ID")

    r = requests.post(
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

    print("LINE status:", r.status_code, r.text)
