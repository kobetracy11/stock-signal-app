from concurrent.futures import ThreadPoolExecutor, TimeoutError
from signals.technical import get_technical_score
from signals.sentiment import get_sentiment_score
from signals.congressional import get_congressional_score
from signals.insider import get_insider_score
from signals.news import get_news_score

# Score breakdown (total = 100):
# Technical signals:    25 pts  (volume spike, momentum, RSI)
# Social sentiment:     30 pts  (Reddit + Stocktwits)
# Congressional trades: 20 pts  (Quiver Quant / SEC)
# Insider buying:       15 pts  (SEC EDGAR Form 4)
# News sentiment:       10 pts  (Finnhub / Yahoo RSS)

DEFAULTS = {
    "technical":     {"score": 0, "signals": ["Technical data unavailable"], "price": None},
    "sentiment":     {"score": 0, "signals": ["Social data unavailable"]},
    "congressional": {"score": 0, "signals": ["Congressional data unavailable"]},
    "insider":       {"score": 0, "signals": ["Insider data unavailable"]},
    "news":          {"score": 0, "signals": ["News data unavailable"]},
}

def safe_fetch(fn, ticker, key, timeout=8):
    """Run a signal fetch with a hard timeout and fallback."""
    try:
        with ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(fn, ticker)
            return future.result(timeout=timeout)
    except Exception:
        return DEFAULTS[key].copy()

def get_composite_score(ticker: str) -> dict:
    ticker = ticker.upper().strip()

    tech        = safe_fetch(get_technical_score,     ticker, "technical")
    sentiment   = safe_fetch(get_sentiment_score,     ticker, "sentiment")
    congress    = safe_fetch(get_congressional_score, ticker, "congressional")
    insider     = safe_fetch(get_insider_score,       ticker, "insider")
    news        = safe_fetch(get_news_score,          ticker, "news")

    total = min(100, max(0,
        tech.get("score", 0) +
        sentiment.get("score", 0) +
        congress.get("score", 0) +
        insider.get("score", 0) +
        news.get("score", 0)
    ))

    all_signals = []
    for block in [tech, sentiment, congress, insider, news]:
        all_signals.extend(block.get("signals", []))

    if total >= 75:   grade, grade_color = "Strong",    "#00c805"
    elif total >= 55: grade, grade_color = "Moderate",  "#f5c518"
    elif total >= 35: grade, grade_color = "Weak",      "#ff6b35"
    else:             grade, grade_color = "No Signal", "#666666"

    return {
        "ticker": ticker,
        "score": total,
        "grade": grade,
        "grade_color": grade_color,
        "price": tech.get("price"),
        "breakdown": {
            "technical":     {"score": tech.get("score", 0),       "max": 25},
            "sentiment":     {"score": sentiment.get("score", 0),   "max": 30},
            "congressional": {"score": congress.get("score", 0),    "max": 20},
            "insider":       {"score": insider.get("score", 0),     "max": 15},
            "news":          {"score": news.get("score", 0),        "max": 10},
        },
        "signals": all_signals
    }
