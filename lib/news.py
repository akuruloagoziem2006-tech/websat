import feedparser

FEEDS = [
    "https://hnrss.org/frontpage",
    "http://export.arxiv.org/rss/cs.AI",
]

def fetch_headlines(limit: int = 10):
    items = []
    for url in FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:limit]:
            items.append((entry.get("title", "").strip(), entry.get("link", "")))
    return items[:limit * 2]
