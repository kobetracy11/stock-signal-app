import yfinance as yf
import numpy as np
import warnings
warnings.filterwarnings("ignore")

def get_technical_score(ticker: str) -> dict:
    try:
        stock = yf.Ticker(ticker)

        # Use auto_adjust=False to avoid issues, and catch empty data
        hist = stock.history(period="30d", auto_adjust=True, timeout=8)

        if hist is None or hist.empty or len(hist) < 3:
            return {"score": 0, "price": None, "signals": [f"${ticker}: no price data"]}

        signals = []
        score = 0

        current_price = round(float(hist["Close"].iloc[-1]), 4)

        # Volume spike (0-10)
        try:
            avg_vol = float(hist["Volume"].iloc[:-1].mean())
            today_vol = float(hist["Volume"].iloc[-1])
            vol_ratio = today_vol / avg_vol if avg_vol > 0 else 1.0
            if vol_ratio >= 3:
                score += 10; signals.append(f"🔥 Volume {vol_ratio:.1f}x average")
            elif vol_ratio >= 2:
                score += 7;  signals.append(f"📈 Volume {vol_ratio:.1f}x average")
            elif vol_ratio >= 1.5:
                score += 4;  signals.append(f"Volume {vol_ratio:.1f}x average")
            else:
                score += 1;  signals.append(f"Volume normal ({vol_ratio:.1f}x)")
        except Exception:
            signals.append("Volume data unavailable")

        # 5-day momentum (0-10)
        try:
            if len(hist) >= 5:
                p5 = float(hist["Close"].iloc[-5])
                pnow = float(hist["Close"].iloc[-1])
                chg = ((pnow - p5) / p5) * 100 if p5 > 0 else 0
                if chg >= 20:
                    score += 10; signals.append(f"🚀 +{chg:.1f}% in 5 days")
                elif chg >= 10:
                    score += 7;  signals.append(f"⬆️ +{chg:.1f}% in 5 days")
                elif chg >= 5:
                    score += 4;  signals.append(f"+{chg:.1f}% in 5 days")
                elif chg < 0:
                    score += 0;  signals.append(f"⬇️ {chg:.1f}% in 5 days")
                else:
                    score += 2;  signals.append(f"+{chg:.1f}% in 5 days")
        except Exception:
            signals.append("Momentum data unavailable")

        # RSI (0-5)
        try:
            if len(hist) >= 14:
                delta = hist["Close"].diff()
                gain = delta.clip(lower=0).rolling(14).mean()
                loss = (-delta.clip(upper=0)).rolling(14).mean()
                rs = gain / loss.replace(0, np.nan)
                rsi_val = float((100 - (100 / (1 + rs))).iloc[-1])
                if np.isnan(rsi_val):
                    signals.append("RSI unavailable")
                elif 40 <= rsi_val <= 65:
                    score += 5; signals.append(f"RSI {rsi_val:.0f} — good entry zone")
                elif 30 <= rsi_val < 40:
                    score += 3; signals.append(f"RSI {rsi_val:.0f} — oversold")
                elif 65 < rsi_val <= 75:
                    score += 2; signals.append(f"RSI {rsi_val:.0f} — getting hot")
                elif rsi_val > 75:
                    score += 0; signals.append(f"RSI {rsi_val:.0f} — overbought")
                else:
                    score += 1; signals.append(f"RSI {rsi_val:.0f}")
        except Exception:
            signals.append("RSI unavailable")

        return {"score": min(score, 25), "price": current_price, "signals": signals}

    except Exception as e:
        return {"score": 0, "price": None, "signals": [f"Technical error: {str(e)[:80]}"]}
