from datetime import datetime, timezone

import feedparser


def collect_rss(rss_url: str, limit: int = 10, source_name: str = "RSS") -> list[dict]:
    feed = feedparser.parse(rss_url)
    if getattr(feed, "bozo", False) and not feed.entries:
        raise RuntimeError("RSS 피드를 읽을 수 없습니다.")

    news = []
    collected_at = datetime.now(timezone.utc).isoformat()
    for entry in feed.entries[:limit]:
        title = entry.get("title", "").strip()
        url = entry.get("link", "").strip()
        if not title or not url:
            continue
        content = entry.get("summary", entry.get("description", ""))
        published_at = entry.get("published", entry.get("updated", ""))
        entry_source = entry.get("source", {}).get("title", "")
        news.append({
            "title": title,
            "content": content,
            "url": url,
            "published_at": published_at,
            "source": entry_source or source_name,
            "collection_method": "rss",
            "collected_at": collected_at,
        })
    return news
