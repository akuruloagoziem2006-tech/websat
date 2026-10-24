import json
import os
import re
import time
import requests

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
MODEL = "gemini-3.8-flash"
RETRY_CODES = {429, 503}

ANALYSIS_PROMPT = """You are analyzing recent technology and AI headlines.
Return ONLY a JSON object with no markdown, in this shape:
{"summary": "2 to 4 sentences on the main trends",
 "predictions": [{"trend": "short name", "forecast": "one specific claim that later headlines could confirm or contradict", "confidence": "low, medium or high", "check_days": 30}]}
Give 2 to 4 predictions. check_days must be between 7 and 90.

Headlines:
"""

VERIFY_PROMPT = """You are checking a forecast against headlines published after it was made.
Be strict: answer "confirmed" only if a headline directly supports the specific claim, "contradicted" only if a headline directly refutes it, otherwise "insufficient".
Return ONLY a JSON object with no markdown, in this shape:
{"verdict": "confirmed, contradicted or insufficient", "evidence": "one sentence naming the most relevant headline, or saying none applies"}

"""

def _call(prompt, max_tokens=1500):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    for attempt in range(3):
        r = requests.post(
            GEMINI_URL,
            headers={"Authorization": f"Bearer {key}"},
            json={"model": MODEL, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens},
            timeout=90,
        )
        if r.status_code not in RETRY_CODES:
            break
        time.sleep(10 * (attempt + 1))
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def _parse_json(text):
    text = re.sub(r"```(?:json)?", "", text).strip()
    return json.loads(text[text.find("{"): text.rfind("}") + 1])

def analyze(headlines):
    data = _parse_json(_call(ANALYSIS_PROMPT + "\n".join(f"- {h}" for h in headlines)))
    summary = str(data.get("summary", "")).strip()
    preds = []
    for p in data.get("predictions", [])[:4]:
        preds.append({
            "trend": str(p.get("trend", "")),
            "forecast": str(p.get("forecast", "")),
            "confidence": str(p.get("confidence", "low")),
            "check_days": min(90, max(7, int(p.get("check_days", 30)))),
        })
    lines = [summary, ""] + [f"- {p['trend']} ({p['confidence']}): {p['forecast']}" for p in preds]
    return "\n".join(lines), preds

def verify(forecast, later_headlines):
    prompt = VERIFY_PROMPT + f"Forecast: {forecast}\n\nHeadlines:\n{later_headlines}"
    data = _parse_json(_call(prompt, max_tokens=400))
    verdict = data.get("verdict", "insufficient")
    if verdict not in {"confirmed", "contradicted"}:
        verdict = "insufficient"
    return verdict, str(data.get("evidence", ""))
