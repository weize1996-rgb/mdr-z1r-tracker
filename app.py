from flask import Flask
from main import run

@app.route("/")
def home():
    print("🔥🔥🔥 ROUTE HIT 🔥🔥🔥")
    run()
    return "OK"
