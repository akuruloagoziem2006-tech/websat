from news import fetch_headlines
from db import record_headlines
from pipeline import run_analysis
from verify import verify_due

def daily_cycle(max_headlines=15):
    items = fetch_headlines()
    record_headlines(items)
    titles = [title for title, _ in items][:max_headlines]
    if not titles:
        return {"status": "no headlines fetched"}
    analysis_id, _ = run_analysis(titles)
    return {"analysis_id": analysis_id, "verified": verify_due()}
