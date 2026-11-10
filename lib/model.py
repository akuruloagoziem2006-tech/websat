import json
import os
import re
import time
import requests

API_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
# Tried in order. Each model has separate capacity, so a busy one often succeeds on the next.
MODELS = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.1-flash-lite"]
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
    last_error = None
    for cycle in range(2):
        for model in MODELS:
            try:
                r = requests.post(
                    API_URL,
                    headers={"Authorization": f"Bearer {key}"},
                    json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens},
                    timeout=60,
                )
            except requests.exceptions.Timeout as e:
                last_error = e
                continue
            if r.status_code in RETRY_CODES:
                last_error = requests.HTTPError(f"{model} returned {r.status_code}")
                continue
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        time.sleep(20)
    raise last_error

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
