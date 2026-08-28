from datetime import datetime, timezone

import requests


def _items_from_payload(payload, items_path: str = "") -> list[dict]:
    value = payload
    for key in filter(None, items_path.split(".")):
        if not isinstance(value, dict):
            return []
        value = value.get(key, [])
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def collect_api(
    url: str,
    limit: int = 10,
    timeout: int = 10,
    source_name: str = "API",
    headers: dict | None = None,
    items_path: str = "",
    field_map: dict | None = None,
) -> list[dict]:
    request_headers = {"User-Agent": "news-pipeline/1.0 (educational project)"}
    request_headers.update(headers or {})
    response = requests.get(url, headers=request_headers, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    mapping = field_map or {}
    collected_at = datetime.now(timezone.utc).isoformat()
    news = []
    for item in _items_from_payload(payload, items_path)[:limit]:
        title = str(item.get(mapping.get("title", "title"), "")).strip()
        news_url = str(item.get(mapping.get("url", "url"), "")).strip()
        if not title or not news_url:
            continue
        news.append({
            "title": title,
            "content": str(item.get(mapping.get("content", "content"), item.get("description", "")) or ""),
            "url": news_url,
            "published_at": str(item.get(mapping.get("published_at", "published_at"), "") or ""),
            "source": source_name,
            "collection_method": "api",
            "collected_at": collected_at,
        })
    return news