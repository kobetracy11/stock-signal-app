import os
import requests
from datetime import datetime, timedelta

def get_news_score(ticker: str) -> dict:
    """
    Score 0-10 based on recent news sentiment
    Uses Finnhub free tier (60 calls/min)
    """
    score = 0
    signals = []

    api_key = os.getenv("FINNHUB_API_KEY", "")
    if not api_key:
        # Fallback to Yahoo Finance RSS news if no Finnhub key
        return _yahoo_news_score(ticker)

    try:
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={week_ago}&to={today}&token={api_key}"
        resp = requests.get(url, timeout=5)

        if resp.status_code == 200:
            articles = resp.json()
            if not articles:
                signals.append("No recent news")
                return {"score": 0, "signals": signals}

            positive_words = ["surge", "jump", "rally", "beat", "record", "growth", "profit", "upgrade",
                              "breakthrough", "partnership", "contract", "approval", "launch", "acquire"]
            negative_words = ["drop", "fall", "miss", "loss", "decline", "downgrade", "lawsuit",
                              "investigation", "recall", "delay", "cut", "bankruptcy", "warning"]

            pos = 0
            neg = 0
            for article in articles[:20]:
                headline = (article.get("headline", "") + " " + article.get("summary", "")).lower()
                for w in positive_words:
                    if w in headline:
                        pos += 1
                        break
                for w in negative_words:
                    if w in headline:
                        neg += 1
                        break

            total = pos + neg
            if total > 0:
                pos_pct = (pos / total) * 100
                if pos_pct >= 70:
                    score = 10
                    signals.append(f"📰 News: {pos_pct:.0f}% positive ({len(articles)} articles)")
                elif pos_pct >= 55:
                    score = 6
                    signals.append(f"📰 News: mostly positive ({len(articles)} articles)")
                elif pos_pct < 35:
                    score = 0
                    signals.append(f"📰 News: mostly negative ({len(articles)} articles)")
                else:
                    score = 3
                    signals.append(f"📰 News: mixed ({len(articles)} articles)")
            else:
                score = 3
                signals.append(f"📰 {len(articles)} recent articles (neutral)")

    except Exception as e:
        return _yahoo_news_score(ticker)

    return {"score": min(score, 10), "signals": signals}


def _yahoo_news_score(ticker: str) -> dict:
    """Fallback: scrape Yahoo Finance RSS for news headlines"""
    score = 0
    signals = []
    try:
        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
        resp = requests.get(url, timeout=5, headers={"User-Agent": "StockSignalApp/1.0"})
        if resp.status_code == 200:
            content = resp.text
            # Count items in RSS feed
            count = content.count("<item>")
            if count > 0:
                score = min(count, 10)
                signals.append(f"📰 {count} recent news articles found")
            else:
                signals.append("No recent news")
        else:
            signals.append("News feed unavailable")
    except Exception:
        signals.append("News feed unavailable")

    return {"score": min(score, 10), "signals": signals}
