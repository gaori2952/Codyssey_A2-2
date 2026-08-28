import time
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


def _extract_article(url: str, timeout: int, fallback_title: str) -> tuple[tuple[str, str], str]:
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "news-pipeline/1.0 (educational project)"},
            timeout=timeout,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.find("h1") or soup.find("title")
        content = " ".join(paragraph.get_text(" ", strip=True) for paragraph in soup.select("article p, main p, p"))
        published = soup.find("meta", attrs={"property": "article:published_time"}) or soup.find("time")
        published_at = ""
        if published:
            published_at = published.get("content") or published.get("datetime") or published.get_text(" ", strip=True)
        return (title.get_text(" ", strip=True) if title else fallback_title, content or fallback_title), published_at
    except requests.RequestException:
        return (fallback_title, fallback_title), ""


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
        href = urljoin(url, href)
        (_, content), published_at = _extract_article(href, timeout, title)
        news.append({
            "title": title,
            "content": content,
            "url": href,
            "published_at": published_at,
            "source": source_name,
            "collection_method": "crawl",
            "collected_at": collected_at,
        })
        time.sleep(delay)
    return news
