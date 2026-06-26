import os
import requests

def get_sentiment_score(ticker: str) -> dict:
    """
    Score 0-30 based on:
    - Reddit mention count & sentiment (0-20)
    - Stocktwits mention volume (0-10)
    Weighted heavily for small/mid cap where social drives price
    """
    score = 0
    signals = []

    # --- Reddit (via Pushshift-style free search) ---
    reddit_score = _get_reddit_score(ticker)
    score += reddit_score["score"]
    signals.extend(reddit_score["signals"])

    # --- Stocktwits ---
    st_score = _get_stocktwits_score(ticker)
    score += st_score["score"]
    signals.extend(st_score["signals"])

    return {
        "score": min(score, 30),
        "signals": signals
    }


def _get_reddit_score(ticker: str) -> dict:
    """Search Reddit via free JSON endpoint - no API key needed"""
    score = 0
    signals = []
    subreddits = ["wallstreetbets", "pennystocks", "stocks", "investing", "smallstreetbets", "RobinHoodPennyStocks"]

    mention_count = 0
    bullish_count = 0
    bearish_count = 0

    bullish_words = ["moon", "buy", "long", "calls", "squeeze", "breakout", "bullish", "rocket", "🚀", "yolo", "run", "pump"]
    bearish_words = ["puts", "short", "sell", "dump", "bearish", "crash", "overvalued", "avoid"]

    headers = {"User-Agent": "StockSignalApp/1.0"}

    for sub in subreddits[:3]:  # Limit to avoid rate limiting
        try:
            url = f"https://www.reddit.com/r/{sub}/search.json?q={ticker}&sort=new&limit=15&t=day&restrict_sr=1"
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                posts = data.get("data", {}).get("children", [])
                for post in posts:
                    pd = post.get("data", {})
                    title = (pd.get("title", "") + " " + pd.get("selftext", "")).lower()
                    # Only count if ticker is actually mentioned
                    if ticker.lower() in title or f"${ticker.lower()}" in title:
                        mention_count += 1
                        upvotes = pd.get("ups", 0)
                        for w in bullish_words:
                            if w in title:
                                bullish_count += 1
                                break
                        for w in bearish_words:
                            if w in title:
                                bearish_count += 1
                                break
        except Exception:
            continue

    if mention_count >= 10:
        score += 12
        signals.append(f"🔥 {mention_count} Reddit mentions today")
    elif mention_count >= 5:
        score += 8
        signals.append(f"📢 {mention_count} Reddit mentions today")
    elif mention_count >= 2:
        score += 4
        signals.append(f"{mention_count} Reddit mentions today")
    elif mention_count == 1:
        score += 2
        signals.append("1 Reddit mention today")

    if mention_count > 0:
        if bullish_count > bearish_count:
            score += min(8, bullish_count * 2)
            signals.append(f"Sentiment: {bullish_count} bullish / {bearish_count} bearish posts")
        elif bearish_count > bullish_count:
            signals.append(f"Sentiment: mostly bearish ({bearish_count} posts)")

    return {"score": min(score, 20), "signals": signals}


def _get_stocktwits_score(ticker: str) -> dict:
    """Stocktwits public API - no key needed"""
    score = 0
    signals = []

    try:
        url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            messages = data.get("messages", [])
            symbol_data = data.get("symbol", {})

            # Watchlist count is a good proxy for interest
            watchlist = symbol_data.get("watchlist_count", 0)

            bull = sum(1 for m in messages if m.get("entities", {}).get("sentiment", {}) and
                       m["entities"]["sentiment"].get("basic") == "Bullish")
            bear = sum(1 for m in messages if m.get("entities", {}).get("sentiment", {}) and
                       m["entities"]["sentiment"].get("basic") == "Bearish")

            total_sentiment = bull + bear
            if total_sentiment > 0:
                bull_pct = (bull / total_sentiment) * 100
                if bull_pct >= 70:
                    score += 6
                    signals.append(f"StockTwits: {bull_pct:.0f}% bullish 🐂")
                elif bull_pct >= 55:
                    score += 4
                    signals.append(f"StockTwits: {bull_pct:.0f}% bullish")
                elif bull_pct < 35:
                    score += 0
                    signals.append(f"StockTwits: {bull_pct:.0f}% bullish (bearish lean)")
                else:
                    score += 2
                    signals.append(f"StockTwits: mixed sentiment")

            if watchlist > 50000:
                score += 4
                signals.append(f"👀 {watchlist:,} watching on StockTwits")
            elif watchlist > 10000:
                score += 2
                signals.append(f"{watchlist:,} watching on StockTwits")

    except Exception as e:
        signals.append("StockTwits: unavailable")

    return {"score": min(score, 10), "signals": signals}
