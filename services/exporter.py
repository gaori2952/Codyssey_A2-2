import json
from pathlib import Path

import pandas as pd

from database.db import get_connection


def export_news(file_format: str, status: str | None = None) -> Path:
    query = "SELECT * FROM clean_news"
    params = []
    if status:
        query += " WHERE summary_status = ?"
        params.append(status)
    with get_connection() as connection:
        frame = pd.read_sql_query(query, connection, params=params)
    output_dir = Path("outputs/exports")
    output_dir.mkdir(parents=True, exist_ok=True)

    if file_format == "csv":
        path = output_dir / "news.csv"
        frame.to_csv(path, index=False, encoding="utf-8-sig")
    elif file_format == "jsonl":
        path = output_dir / "news.jsonl"
        with path.open("w", encoding="utf-8") as handle:
            for record in frame.to_dict(orient="records"):
                handle.write(json.dumps(record, ensure_ascii=False, default=str))
                handle.write("\n")
    else:
        path = output_dir / "news.xlsx"
        frame.to_excel(path, index=False)
    print(f"내보내기 완료: {path}")
    return path
