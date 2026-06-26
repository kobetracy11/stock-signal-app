# 📊 Stock Signal Dashboard

A mobile-friendly stock signal aggregator for small/mid cap and penny stocks. Combines congressional trades, social sentiment, insider buying, technical signals, and news into a single composite score out of 100.

## Signal Breakdown

| Signal | Max Score | Source |
|---|---|---|
| Technical (volume, momentum, RSI) | 25 | yfinance (free) |
| Social sentiment (Reddit + Stocktwits) | 30 | Reddit API + Stocktwits (free) |
| Congressional trades | 20 | Quiver Quant / SEC (free) |
| Insider buying | 15 | SEC EDGAR Form 4 (free) |
| News sentiment | 10 | Finnhub free tier / Yahoo RSS |

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/stock-signal-app.git
cd stock-signal-app
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
```bash
cp .env.example .env
```
Edit `.env` and fill in:
- `FINNHUB_API_KEY` — free at https://finnhub.io (60 calls/min free)
- `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` — free at https://www.reddit.com/prefs/apps
  - Create a "script" type app, use `http://localhost:5000` as redirect URI

### 4. Run locally
```bash
python app.py
```
Open http://localhost:5000 in your browser.

## Deploy to Render (free, access on phone)

1. Push this repo to GitHub
2. Go to https://render.com and sign up (free)
3. Click **New → Web Service**
4. Connect your GitHub repo
5. Render auto-detects `render.yaml` — just click **Deploy**
6. Add your env vars in Render's dashboard under **Environment**
7. Once deployed, open the URL on your phone — bookmark it to home screen

## Features

- 🔍 Search any ticker and get a full signal breakdown
- 📌 Pin stocks to keep them at the top
- 📊 Watchlist of popular small/mid cap tickers ranked by score
- Score grades: **Strong** (75+), **Moderate** (55+), **Weak** (35+), **No signal**
- 5-minute caching to avoid rate limits

## Pinning Stocks

Tap the 🔖 icon on any stock card to pin it. Pinned stocks:
- Always appear at the top of the watchlist
- Have their own **Pinned** tab
- Are saved to `pinned.json` (persists across restarts)

## Adding Custom Tickers to Watchlist

Edit `app.py` and add tickers to the `default_tickers` list in the `/api/watchlist` route.
