from signals.technical import get_technical_score
from signals.sentiment import get_sentiment_score
from signals.congressional import get_congressional_score
from signals.insider import get_insider_score
from signals.news import get_news_score

# Score breakdown (total = 100):
# Technical signals:    25 pts  (volume spike, momentum, RSI)
# Social sentiment:     30 pts  (Reddit + Stocktwits — weighted high for small caps)
# Congressional trades: 20 pts  (STOCK Act filings)
# Insider buying:       15 pts  (SEC Form 4)
# News sentiment:       10 pts  (Finnhub / Yahoo RSS)

def get_composite_score(ticker: str) -> dict:
    """
    Returns a full signal breakdown and composite score 0-100
    """
    ticker = ticker.upper().strip()

    results = {}

    # Fetch all signals
    tech = get_technical_score(ticker)
    results["technical"] = tech

    sentiment = get_sentiment_score(ticker)
    results["sentiment"] = sentiment

    congress = get_congressional_score(ticker)
    results["congressional"] = congress

    insider = get_insider_score(ticker)
    results["insider"] = insider

    news = get_news_score(ticker)
    results["news"] = news

    # Composite score
    total = (
        tech.get("score", 0) +
        sentiment.get("score", 0) +
        congress.get("score", 0) +
        insider.get("score", 0) +
        news.get("score", 0)
    )
    total = min(100, max(0, total))

    # Collect all signal messages
    all_signals = []
    all_signals.extend(tech.get("signals", []))
    all_signals.extend(sentiment.get("signals", []))
    all_signals.extend(congress.get("signals", []))
    all_signals.extend(insider.get("signals", []))
    all_signals.extend(news.get("signals", []))

    # Grade label
    if total >= 75:
        grade = "Strong"
        grade_color = "#22c55e"
    elif total >= 55:
        grade = "Moderate"
        grade_color = "#f59e0b"
    elif total >= 35:
        grade = "Weak"
        grade_color = "#f97316"
    else:
        grade = "No signal"
        grade_color = "#6b7280"

    return {
        "ticker": ticker,
        "score": total,
        "grade": grade,
        "grade_color": grade_color,
        "price": tech.get("price"),
        "breakdown": {
            "technical": {"score": tech.get("score", 0), "max": 25},
            "sentiment": {"score": sentiment.get("score", 0), "max": 30},
            "congressional": {"score": congress.get("score", 0), "max": 20},
            "insider": {"score": insider.get("score", 0), "max": 15},
            "news": {"score": news.get("score", 0), "max": 10},
        },
        "signals": all_signals
    }
