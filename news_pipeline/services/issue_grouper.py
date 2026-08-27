import re
from collections import defaultdict
from datetime import datetime

from database.db import create_issue, get_clean_news, update_issue_id

STOPWORDS = {"the", "and", "for", "with", "from", "this", "that", "뉴스", "관련", "대한"}


def keywords(text: str) -> set[str]:
    words = re.findall(r"[가-힣A-Za-z0-9]{2,}", text.lower())
    return {word for word in words if word not in STOPWORDS}


def similar(first: dict, second: dict) -> bool:
    if first["category"] != second["category"]:
        return False
    first_words = keywords(f"{first['title']} {first.get('content', '')}")
    second_words = keywords(f"{second['title']} {second.get('content', '')}")
    if not first_words or not second_words:
        return False
    overlap = len(first_words & second_words) / len(first_words | second_words)
    same_day = first.get("published_at") and first.get("published_at") == second.get("published_at")
    return overlap >= 0.25 or (overlap >= 0.15 and same_day)


def group_issues() -> int:
    items = get_clean_news()
    existing_groups = defaultdict(list)
    for item in items:
        if item.get("issue_id") is not None:
            existing_groups[item["issue_id"]].append(item)
    groups: list[list[dict]] = []
    for item in items:
        if item.get("issue_id") is not None:
            continue
        matching_group = next((group for group in groups if similar(item, group[0])), None)
        if matching_group is None:
            for existing_group in existing_groups.values():
                if similar(item, existing_group[0]):
                    update_issue_id(item["id"], existing_group[0]["issue_id"])
                    matching_group = existing_group
                    break
        if matching_group is None:
            groups.append([item])
        else:
            matching_group.append(item)

    assigned = 0
    for group in groups:
        issue_id = create_issue(group[0]["title"], group[0]["category"])
        for item in group:
            update_issue_id(item["id"], issue_id)
            assigned += 1
    return assigned


def get_issue_articles(issue_id: int) -> list[dict]:
    return [item for item in get_clean_news() if item.get("issue_id") == issue_id]
