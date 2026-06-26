import yfinance as yf
import numpy as np

def get_technical_score(ticker: str) -> dict:
    """
    Score 0-25 based on:
    - Volume spike vs 20-day avg (0-10)
    - Price momentum / breakout (0-10)
    - RSI positioning (0-5)
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="30d")

        if hist.empty or len(hist) < 5:
            return {"score": 0, "details": "No data available", "signals": []}

        signals = []
        score = 0

        # Volume spike (0-10)
        avg_vol = hist["Volume"].iloc[:-1].mean()
        today_vol = hist["Volume"].iloc[-1]
        vol_ratio = today_vol / avg_vol if avg_vol > 0 else 1

        if vol_ratio >= 3:
            vol_score = 10
            signals.append(f"🔥 Volume {vol_ratio:.1f}x avg")
        elif vol_ratio >= 2:
            vol_score = 7
            signals.append(f"📈 Volume {vol_ratio:.1f}x avg")
        elif vol_ratio >= 1.5:
            vol_score = 4
            signals.append(f"Volume {vol_ratio:.1f}x avg")
        else:
            vol_score = 1
            signals.append(f"Volume normal ({vol_ratio:.1f}x)")
        score += vol_score

        # Price momentum - % change over last 5 days (0-10)
        if len(hist) >= 5:
            price_5d_ago = hist["Close"].iloc[-5]
            price_now = hist["Close"].iloc[-1]
            pct_change = ((price_now - price_5d_ago) / price_5d_ago) * 100

            if pct_change >= 20:
                mom_score = 10
                signals.append(f"🚀 +{pct_change:.1f}% in 5 days")
            elif pct_change >= 10:
                mom_score = 7
                signals.append(f"⬆️ +{pct_change:.1f}% in 5 days")
            elif pct_change >= 5:
                mom_score = 4
                signals.append(f"+{pct_change:.1f}% in 5 days")
            elif pct_change < 0:
                mom_score = 0
                signals.append(f"⬇️ {pct_change:.1f}% in 5 days")
            else:
                mom_score = 2
                signals.append(f"+{pct_change:.1f}% in 5 days")
            score += mom_score

        # RSI (0-5) — sweet spot is 40-65 for entry
        if len(hist) >= 14:
            delta = hist["Close"].diff()
            gain = delta.clip(lower=0).rolling(14).mean()
            loss = (-delta.clip(upper=0)).rolling(14).mean()
            rs = gain / loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
            rsi_val = rsi.iloc[-1]

            if 40 <= rsi_val <= 65:
                rsi_score = 5
                signals.append(f"RSI {rsi_val:.0f} (good entry zone)")
            elif 30 <= rsi_val < 40:
                rsi_score = 3
                signals.append(f"RSI {rsi_val:.0f} (oversold, bounce potential)")
            elif 65 < rsi_val <= 75:
                rsi_score = 2
                signals.append(f"RSI {rsi_val:.0f} (getting hot)")
            elif rsi_val > 75:
                rsi_score = 0
                signals.append(f"RSI {rsi_val:.0f} (overbought)")
            else:
                rsi_score = 1
                signals.append(f"RSI {rsi_val:.0f}")
            score += rsi_score

        current_price = round(hist["Close"].iloc[-1], 4)

        return {
            "score": min(score, 25),
            "price": current_price,
            "details": f"Price ${current_price}",
            "signals": signals
        }

    except Exception as e:
        return {"score": 0, "details": f"Error: {str(e)}", "signals": []}
