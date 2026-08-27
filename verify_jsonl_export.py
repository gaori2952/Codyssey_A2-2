import json

from database.db import get_connection
from services.exporter import export_news

conn = get_connection()
conn.execute("DELETE FROM clean_news")
conn.execute(
    "INSERT INTO clean_news (raw_id, title, content, url, published_at, source, category, summary, summary_status, created_at, updated_at, issue_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
    (1, "AI 뉴스", "본문", "https://example.com/1", "2026-08-27", "test", "AI", "요약", "summarized", "2026-08-27T00:00:00+00:00", "2026-08-27T00:00:00+00:00", 1),
)
conn.commit()

path = export_news("jsonl")
content = path.read_text(encoding="utf-8").splitlines()[0]
obj = json.loads(content)
assert path.name == "news.jsonl"
assert obj["title"] == "AI 뉴스"
print(f"ok: {path}")
print(content)
