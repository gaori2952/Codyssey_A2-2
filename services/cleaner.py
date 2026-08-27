import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from bs4 import BeautifulSoup

from database.db import get_raw_news, save_clean_news

CATEGORIES = {
    "AI": ["ai", "artificial intelligence", "인공지능", "machine learning", "chatgpt", "gpt"],
    "반도체": ["semiconductor", "chip", "nvidia", "intel", "반도체"],
    "클라우드": ["cloud", "aws", "azure", "gcp", "클라우드"],
    "보안": ["security", "cyber", "hack", "privacy", "보안"],
    "소프트웨어": ["software", "python", "linux", "app", "소프트웨어"],
}


def clean_text(value: str | None) -> str:
    value = value or ""
    text = BeautifulSoup(value, "html.parser").get_text(" ", strip=True) if "<" in value else value
    return re.sub(r"\s+", " ", text).strip()


def normalize_date(value: str | None) -> str:
    if not value:
        return ""
    try:
        parsed = parsedate_to_datetime(value)
        return parsed.date().isoformat()
    except (TypeError, ValueError, OverflowError):
        match = re.search(r"(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})", value)
        if match:
            return f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
        return value[:10]


def classify(title: str, content: str) -> str:
    text = f"{title} {content}".lower()
    for category, keywords in CATEGORIES.items():
        if any(keyword.lower() in text for keyword in keywords):
            return category
    return "기타"


def clean_item(raw: dict) -> dict | None:
    title = clean_text(raw["title"])
    url = clean_text(raw["url"])
    if not title or not url or not re.match(r"https?://", url):
        return None
    content = clean_text(raw.get("content"))
    now = datetime.now(timezone.utc).isoformat()
    return {
        "raw_id": raw["id"], "title": title, "content": content,
        "url": url, "published_at": normalize_date(raw.get("published_at")),
        "source": clean_text(raw.get("source")), "category": classify(title, content),
        "created_at": now, "updated_at": now,
    }


def clean_all() -> int:
    cleaned = 0
    for raw in get_raw_news():
        item = clean_item(raw)
        if item is None:
            continue
        save_clean_news(item)
        cleaned += 1
    return cleaned
