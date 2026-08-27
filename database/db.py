import sqlite3
import json
from pathlib import Path

DB_PATH = Path("data") / "news.db"


def load_config() -> dict:
    config_path = Path("config.json")
    if not config_path.exists():
        return {"duplicate_policy": "skip"}
    return json.loads(config_path.read_text(encoding="utf-8"))


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS raw_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                url TEXT NOT NULL UNIQUE,
                published_at TEXT,
                source TEXT,
                collection_method TEXT,
                collected_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS clean_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_id INTEGER NOT NULL UNIQUE,
                title TEXT NOT NULL,
                content TEXT,
                url TEXT NOT NULL UNIQUE,
                published_at TEXT,
                source TEXT,
                category TEXT,
                summary TEXT,
                summary_status TEXT DEFAULT 'unsummarized',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                issue_id INTEGER,
                FOREIGN KEY(raw_id) REFERENCES raw_news(id)
            );
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_from TEXT,
                date_to TEXT,
                category TEXT,
                trend TEXT,
                keywords TEXT,
                issues TEXT,
                implications TEXT,
                analysis_type TEXT DEFAULT 'trend',
                issue_id INTEGER,
                comparison_result TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_title TEXT NOT NULL,
                category TEXT,
                created_at TEXT NOT NULL
            );
            """
        )
        clean_columns = {row[1] for row in connection.execute("PRAGMA table_info(clean_news)")}
        if "issue_id" not in clean_columns:
            connection.execute("ALTER TABLE clean_news ADD COLUMN issue_id INTEGER")
        analysis_columns = {row[1] for row in connection.execute("PRAGMA table_info(analyses)")}
        for column, definition in (("analysis_type", "TEXT DEFAULT 'trend'"), ("issue_id", "INTEGER"), ("comparison_result", "TEXT")):
            if column not in analysis_columns:
                connection.execute(f"ALTER TABLE analyses ADD COLUMN {column} {definition}")


def save_raw_news(items: list[dict]) -> int:
    policy = load_config().get("duplicate_policy", "skip")
    saved = 0
    with get_connection() as connection:
        for item in items:
            if policy == "upsert":
                connection.execute(
                    """INSERT INTO raw_news (title, content, url, published_at, source, collection_method, collected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(url) DO UPDATE SET title=excluded.title, content=excluded.content,
                    published_at=excluded.published_at, source=excluded.source,
                    collection_method=excluded.collection_method, collected_at=excluded.collected_at""",
                    tuple(item[key] for key in ("title", "content", "url", "published_at", "source", "collection_method", "collected_at")),
                )
                saved += 1
            else:
                cursor = connection.execute(
                    "INSERT OR IGNORE INTO raw_news (title, content, url, published_at, source, collection_method, collected_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    tuple(item[key] for key in ("title", "content", "url", "published_at", "source", "collection_method", "collected_at")),
                )
                saved += cursor.rowcount
    return saved


def get_raw_news() -> list[dict]:
    with get_connection() as connection:
        return [dict(row) for row in connection.execute("SELECT * FROM raw_news ORDER BY id")]


def save_clean_news(item: dict) -> None:
    with get_connection() as connection:
        connection.execute(
            """INSERT INTO clean_news (raw_id, title, content, url, published_at, source, category, created_at, updated_at, issue_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(raw_id) DO UPDATE SET title=excluded.title, content=excluded.content,
            url=excluded.url, published_at=excluded.published_at, source=excluded.source,
            category=excluded.category, updated_at=excluded.updated_at""",
            tuple(item[key] for key in ("raw_id", "title", "content", "url", "published_at", "source", "category", "created_at", "updated_at")) + (item.get("issue_id"),),
        )


def create_issue(issue_title: str, category: str) -> int:
    with get_connection() as connection:
        cursor = connection.execute("INSERT INTO issues (issue_title, category, created_at) VALUES (?, ?, datetime('now'))", (issue_title, category))
        return cursor.lastrowid


def update_issue_id(news_id: int, issue_id: int) -> None:
    with get_connection() as connection:
        connection.execute("UPDATE clean_news SET issue_id = ?, updated_at = datetime('now') WHERE id = ?", (issue_id, news_id))


def get_clean_news(filters=None) -> list[dict]:
    query = "SELECT * FROM clean_news"
    params = []
    if filters:
        query += " WHERE " + " AND ".join(filters[0])
        params = filters[1]
    query += " ORDER BY id"
    with get_connection() as connection:
        return [dict(row) for row in connection.execute(query, params)]


def get_comparable_issues() -> list[dict]:
    with get_connection() as connection:
        return [dict(row) for row in connection.execute("SELECT issue_id, COUNT(*) article_count, COUNT(DISTINCT source) source_count FROM clean_news WHERE issue_id IS NOT NULL GROUP BY issue_id HAVING source_count >= 2")]


def save_comparison(issue_id: int, result: dict, comparison_text: str) -> None:
    def as_text(value) -> str:
        if isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)
        return str(value or "")

    with get_connection() as connection:
        connection.execute("INSERT INTO analyses (category, trend, keywords, issues, implications, analysis_type, issue_id, comparison_result, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))", ("동일 이슈 비교", as_text(result.get("common_facts")), as_text(result.get("source_emphasis")), as_text(result.get("expression_differences")), as_text(result.get("implications")), "comparison", issue_id, comparison_text))


def get_summary_targets(news_id=None, unsummarized=False, limit=10) -> list[dict]:
    conditions, params = [], []
    if news_id is not None:
        conditions.append("id = ?"); params.append(news_id)
    elif unsummarized:
        conditions.append("summary_status = 'unsummarized'")
    query = "SELECT * FROM clean_news"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id"
    if news_id is None and not unsummarized:
        pass
    else:
        query += " LIMIT ?"; params.append(limit)
    with get_connection() as connection:
        return [dict(row) for row in connection.execute(query, params)]


def save_summary(news_id: int, summary: str) -> None:
    with get_connection() as connection:
        connection.execute("UPDATE clean_news SET summary = ?, summary_status = 'summarized', updated_at = datetime('now') WHERE id = ?", (summary, news_id))
