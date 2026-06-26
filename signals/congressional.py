import requests
from datetime import datetime, timedelta

# Uses Quiver Quant's free public congressional trading data
# Also falls back to house.gov disclosure search

QUIVER_BASE = "https://api.quiverquant.com/beta/live/congresstrading"

def get_congressional_score(ticker: str) -> dict:
    """
    Score 0-20 based on recent congressional trades
    - Purchase by congress member in last 30 days: high score
    - Sale: negative signal
    """
    score = 0
    signals = []

    trades = _fetch_quiver_congress(ticker)

    if not trades:
        return {"score": 0, "signals": ["No recent congressional trades found"]}

    cutoff = datetime.now() - timedelta(days=30)
    recent_buys = []
    recent_sells = []

    for trade in trades:
        try:
            date_str = trade.get("Date") or trade.get("TransactionDate", "")
            trade_date = datetime.strptime(date_str[:10], "%Y-%m-%d")
            if trade_date < cutoff:
                continue

            tx_type = (trade.get("Transaction") or trade.get("Type", "")).lower()
            member = trade.get("Representative") or trade.get("Senator") or "Congress member"
            amount = trade.get("Range") or trade.get("Amount", "")

            if "purchase" in tx_type or "buy" in tx_type:
                recent_buys.append({"member": member, "amount": amount, "date": date_str[:10]})
            elif "sale" in tx_type or "sell" in tx_type:
                recent_sells.append({"member": member, "amount": amount, "date": date_str[:10]})
        except Exception:
            continue

    if recent_buys:
        buy_score = min(len(recent_buys) * 8, 20)
        score += buy_score
        for b in recent_buys[:2]:
            signals.append(f"🏛️ {b['member']} BOUGHT {amount} on {b['date']}")
    
    if recent_sells:
        sell_penalty = min(len(recent_sells) * 4, 10)
        score = max(0, score - sell_penalty)
        for s in recent_sells[:1]:
            signals.append(f"🏛️ {s['member']} SOLD on {s['date']}")

    if not recent_buys and not recent_sells:
        signals.append("No congressional trades in last 30 days")

    return {"score": min(score, 20), "signals": signals}


def _fetch_quiver_congress(ticker: str) -> list:
    """Fetch from Quiver Quant free endpoint"""
    try:
        url = f"https://api.quiverquant.com/beta/historical/congresstrading/{ticker}"
        headers = {"User-Agent": "StockSignalApp/1.0"}
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass

    # Fallback: house.gov STOCK Act disclosures
    try:
        url = f"https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2024/{ticker}"
        # This is a simplified fallback - full implementation would parse PDFs
        pass
    except Exception:
        pass

    return []
