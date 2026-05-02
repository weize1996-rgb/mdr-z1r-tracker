from flask import Flask
from main import run

app = Flask(__name__)

@app.route("/")
def home():
    print("🔥 ROUTE HIT")
    try:
        run()
    except Exception as e:
        print("❌ ERROR:", e)
    return "OK"
