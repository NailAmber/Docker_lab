from flask import Flask, jsonify
import os


app = Flask(__name__)

@app.get("/")
def index():
    return jsonify(status="ok", message="Hello from Flask in Docker!", env=os.getenv("APP_ENV", "dev"))

@app.get("/healthz")
def healthz():
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

