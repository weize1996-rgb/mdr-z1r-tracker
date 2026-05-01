from flask import Flask
from main import run

app = Flask(__name__)

@app.route("/")
def home():
    run()
    return "OK"