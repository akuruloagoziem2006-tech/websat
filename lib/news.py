import feedparser
import requests

FEEDS = [
    "https://hnrss.org/frontpage",
    "https://export.arxiv.org/rss/cs.AI",
]
HEADERS = {"User-Agent": "WebSat/1.0 (personal project; contact: akuruloagoziem2006@gmail.com)"}

def fetch_headlines(limit: int = 10):
    items = []
    for url in FEEDS:
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            feed = feedparser.parse(r.content)
        except Exception as e:
            print(f"feed failed: {url}: {e}", flush=True)
            continue
        if not feed.entries:
            print(f"feed empty: {url}", flush=True)
        for entry in feed.entries[:limit]:
            items.append((entry.get("title", "").strip(), entry.get("link", "")))
    return items[: limit * 2]
