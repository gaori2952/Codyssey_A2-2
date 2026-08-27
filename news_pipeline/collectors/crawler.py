import time
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup


def collect_crawl(url: str, limit: int = 10, timeout: int = 10, delay: float = 1, source_name: str = "Web crawl") -> list[dict]:
    headers = {"User-Agent": "news-pipeline/1.0 (educational project)"}
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    news = []
    collected_at = datetime.now(timezone.utc).isoformat()

    for link in soup.select("a.storylink, span.titleline > a")[:limit]:
        title = link.get_text(" ", strip=True)
        href = link.get("href", "").strip()
        if not title or not href:
            continue
        if href.startswith("/"):
            href = "https://news.ycombinator.com" + href
        news.append({
            "title": title,
            "content": title,
            "url": href,
            "published_at": "",
            "source": source_name,
            "collection_method": "crawl",
            "collected_at": collected_at,
        })
        time.sleep(delay)
    return news
