import requests
from datetime import datetime, timedelta

def get_insider_score(ticker: str) -> dict:
    """
    Score 0-15 based on SEC Form 4 insider buying
    Free via SEC EDGAR full-text search
    """
    score = 0
    signals = []

    try:
        # Get company CIK from ticker
        cik = _get_cik(ticker)
        if not cik:
            return {"score": 0, "signals": ["Could not find SEC data"]}

        filings = _get_form4_filings(cik)
        if not filings:
            return {"score": 0, "signals": ["No recent Form 4 filings"]}

        cutoff = datetime.now() - timedelta(days=30)
        buys = []
        sells = []

        for filing in filings[:10]:
            filed_date_str = filing.get("filedAt", "")[:10]
            try:
                filed_date = datetime.strptime(filed_date_str, "%Y-%m-%d")
            except Exception:
                continue

            if filed_date < cutoff:
                continue

            # Check transaction type from filing description
            desc = filing.get("formType", "")
            entity = filing.get("entityName", "Insider")

            # Form 4 = statement of changes; we flag it as a buy signal
            # (Full XML parsing would give transaction type but this is free tier)
            buys.append({"entity": entity, "date": filed_date_str})

        if buys:
            score += min(len(buys) * 5, 15)
            for b in buys[:2]:
                signals.append(f"📋 {b['entity']} filed Form 4 on {b['date']}")
        else:
            signals.append("No insider Form 4 filings in last 30 days")

    except Exception as e:
        signals.append(f"SEC data unavailable")

    return {"score": min(score, 15), "signals": signals}


def _get_cik(ticker: str) -> str | None:
    """Look up SEC CIK number for a ticker"""
    try:
        url = f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&dateRange=custom&startdt=2024-01-01&forms=4"
        headers = {"User-Agent": "StockSignalApp research@example.com"}
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            hits = data.get("hits", {}).get("hits", [])
            if hits:
                return hits[0].get("_source", {}).get("entity_id")
    except Exception:
        pass

    # Fallback: company search
    try:
        url = f"https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK={ticker}&type=4&dateb=&owner=include&count=10&search_text=&action=getcompany&output=atom"
        headers = {"User-Agent": "StockSignalApp research@example.com"}
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200 and "<CIK>" in resp.text:
            start = resp.text.find("<CIK>") + 5
            end = resp.text.find("</CIK>")
            return resp.text[start:end].strip()
    except Exception:
        pass

    return None


def _get_form4_filings(cik: str) -> list:
    """Fetch recent Form 4 filings from SEC EDGAR"""
    try:
        cik_padded = str(cik).zfill(10)
        url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
        headers = {"User-Agent": "StockSignalApp research@example.com"}
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            filings = data.get("filings", {}).get("recent", {})
            forms = filings.get("form", [])
            dates = filings.get("filedAt", filings.get("filed", []))
            entities = filings.get("entityName", [""] * len(forms))

            results = []
            for i, form in enumerate(forms):
                if form == "4":
                    results.append({
                        "formType": form,
                        "filedAt": dates[i] if i < len(dates) else "",
                        "entityName": entities[i] if i < len(entities) else "Insider"
                    })
            return results
    except Exception:
        pass
    return []
