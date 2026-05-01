from flask import Flask
from main import run

app = Flask(__name__)

@app.route("/")
def home():
    run()   # 🔥 這行是關鍵
    return "OK"
