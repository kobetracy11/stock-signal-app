import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from scorer import get_composite_score

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

PINNED_FILE = "pinned.json"
cache = {}
CACHE_TTL = 300  # 5 minutes

# Active small/mid cap tickers (verified trading as of 2026)
DEFAULT_TICKERS = [
    "GME", "AMC", "SPCE", "NKLA", "TLRY",
    "MARA", "RIOT", "CLSK", "CIFR", "WULF"
]

def load_pinned():
    try:
        with open(PINNED_FILE) as f:
            return json.load(f).get("pinned", [])
    except Exception:
        return []

def save_pinned(tickers):
    try:
        with open(PINNED_FILE, "w") as f:
            json.dump({"pinned": tickers}, f)
    except Exception:
        pass

def get_cached_score(ticker):
    now = datetime.now().timestamp()
    if ticker in cache:
        entry = cache[ticker]
        if now - entry["timestamp"] < CACHE_TTL:
            return entry["data"]
    data = get_composite_score(ticker)
    cache[ticker] = {"data": data, "timestamp": now}
    return data

def score_ticker(ticker, pinned):
    try:
        data = get_cached_score(ticker)
        data["pinned"] = ticker in pinned
        return data
    except Exception:
        return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/score/<ticker>")
def score(ticker):
    try:
        ticker = ticker.upper().strip()
        data = get_cached_score(ticker)
        pinned = load_pinned()
        data["pinned"] = ticker in pinned
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/pin", methods=["POST"])
def pin():
    ticker = request.json.get("ticker", "").upper()
    pinned = load_pinned()
    if ticker not in pinned:
        pinned.append(ticker)
        save_pinned(pinned)
    return jsonify({"pinned": pinned})

@app.route("/api/unpin", methods=["POST"])
def unpin():
    ticker = request.json.get("ticker", "").upper()
    pinned = load_pinned()
    if ticker in pinned:
        pinned.remove(ticker)
        save_pinned(pinned)
    return jsonify({"pinned": pinned})

@app.route("/api/pinned")
def get_pinned():
    pinned = load_pinned()
    results = []
    for ticker in pinned:
        data = get_cached_score(ticker)
        data["pinned"] = True
        results.append(data)
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return jsonify(results)

@app.route("/api/watchlist")
def watchlist():
    pinned = load_pinned()
    all_tickers = list(dict.fromkeys(pinned + DEFAULT_TICKERS))[:10]

    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(score_ticker, t, pinned): t for t in all_tickers}
        for future in as_completed(futures, timeout=30):
            try:
                result = future.result()
                if result and result.get("price"):  # Only show if we got price data
                    results.append(result)
            except Exception:
                continue

    results.sort(key=lambda x: (x.get("pinned", False), x.get("score", 0)), reverse=True)
    return jsonify(results)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
