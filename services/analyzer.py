import json
from datetime import datetime, timezone

from database.db import get_connection
from services.ai_service import analyze_news


def run_analysis(category=None, date_from=None, date_to=None) -> dict | None:
    conditions, params = ["summary_status = 'summarized'"], []
    if category:
        conditions.append("category = ?"); params.append(category)
    if date_from:
        conditions.append("published_at >= ?"); params.append(date_from)
    if date_to:
        conditions.append("published_at <= ?"); params.append(date_to)
    with get_connection() as connection:
        items = [dict(row) for row in connection.execute(f"SELECT * FROM clean_news WHERE {' AND '.join(conditions)} ORDER BY id", params)]
    if not items:
        print("분석할 요약 뉴스가 없습니다. 먼저 clean과 summarize를 실행하세요.")
        return None
    result = analyze_news(items)
    if result is None:
        return None
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as connection:
        connection.execute("INSERT INTO analyses (date_from, date_to, category, trend, keywords, issues, implications, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (date_from, date_to, category or "전체", result.get("trend", ""), json.dumps(result.get("keywords", ""), ensure_ascii=False), result.get("issues", ""), result.get("implications", ""), now))
    print("\n[AI 분석 결과]")
    for key, label in [("trend", "주요 트렌드"), ("keywords", "핵심 키워드"), ("issues", "공통 이슈"), ("implications", "시사점")]:
        print(f"{label}: {result.get(key, '')}")
    return result
