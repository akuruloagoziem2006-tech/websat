import time
import feedparser
import requests

FEEDS = [
    "https://hnrss.org/frontpage",
    "https://export.arxiv.org/rss/cs.AI",
    "https://export.arxiv.org/rss/cs.LG",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.technologyreview.com/feed/",
]
HEADERS = {"User-Agent": "WebSat/1.0 (personal project; contact: akuruloagoziem2006@gmail.com)"}

def _fetch_one(url, attempts=3):
    for attempt in range(attempts):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            return feedparser.parse(r.content)
        except Exception as e:
            print(f"feed attempt {attempt + 1} failed: {url}: {e}", flush=True)
            time.sleep(3)
    return None

def fetch_headlines(limit: int = 10):
    items = []
    for url in FEEDS:
        feed = _fetch_one(url)
        if feed is None or not feed.entries:
            print(f"feed skipped: {url}", flush=True)
            continue
        for entry in feed.entries[:limit]:
            items.append((entry.get("title", "").strip(), entry.get("link", "")))
    return items[: limit * 2]
