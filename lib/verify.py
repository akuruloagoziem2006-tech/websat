from db import due_predictions, later_headlines, record_verdict
from model import verify

def verify_due():
    checked = 0
    for pid, trend, forecast, created, end in due_predictions():
        rows = later_headlines(created, end)
        if not rows:
            continue
        text = "\n".join(f"- {title}" for (title,) in rows)
        try:
            verdict, evidence = verify(f"{trend}: {forecast}", text)
        except Exception:
            continue
        status = "inconclusive" if verdict == "insufficient" else verdict
        record_verdict(pid, status, evidence)
        checked += 1
    return checked
