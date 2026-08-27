import json
from pathlib import Path

from database.db import get_comparable_issues, get_connection, save_comparison
from services.ai_service import compare_news


def compare_issue(issue_id: int) -> dict | None:
    with get_connection() as connection:
        items = [dict(row) for row in connection.execute("SELECT * FROM clean_news WHERE issue_id = ? ORDER BY id", (issue_id,))]
    sources = {item.get("source") for item in items}
    if len(items) < 2 or len(sources) < 2:
        print("[INFO] 비교 가능한 동일 이슈가 없습니다.")
        return None
    result = compare_news(items)
    if result is None:
        print("[ERROR] 뉴스 비교 AI 요청에 실패했습니다. logs/app.log에서 자세한 원인을 확인하세요.")
        return None
    save_comparison(issue_id, result, json.dumps(result, ensure_ascii=False))
    print_comparison(issue_id, items, result)
    save_comparison_files(issue_id, items, result)
    return result


def compare_all_issues() -> int:
    count = 0
    for issue in get_comparable_issues():
        if compare_issue(issue["issue_id"]):
            count += 1
    if count == 0:
        print("[INFO] 비교 가능한 동일 이슈가 없습니다.")
    return count


def print_comparison(issue_id: int, items: list[dict], result: dict) -> None:
    print(f"\n[동일 이슈 비교: issue_id={issue_id}]")
    print("참여 뉴스 소스: " + ", ".join(sorted({item.get("source", "") for item in items})))
    for axis, label in COMPARISON_AXES:
        print(f"\n[{axis}. {label}]")
        print(format_value(axis_value(result, axis)))


COMPARISON_AXES = [
    ("common_facts", "공통 사실"),
    ("source_emphasis", "소스별 강조점"),
    ("expression_differences", "표현·제목 차이"),
    ("keyword_differences", "핵심 키워드 차이"),
    ("perspective_implications", "관점·종합 시사점"),
]


def axis_value(result: dict, axis: str):
    if axis == "perspective_implications":
        if "perspective_implications" in result:
            return result[axis]
        return {"관점 차이": result.get("perspective_differences", ""), "종합 시사점": result.get("implications", "")}
    return result.get(axis, "")


def format_value(value) -> str:
    if isinstance(value, dict):
        return "\n".join(f"- **{key}**: {format_value(item)}" for key, item in value.items())
    if isinstance(value, list):
        return "\n".join(f"- {format_value(item)}" for item in value)
    return str(value or "-" )


def format_table(value) -> list[str]:
    def cell(item) -> str:
        return format_value(item).replace("|", "\\|").replace("\n", "<br>")

    if isinstance(value, dict):
        if value and all(isinstance(item, dict) for item in value.values()):
            columns = sorted({key for item in value.values() for key in item})
            rows = ["| 뉴스 소스 | " + " | ".join(columns) + " |", "|---|" + "---|" * len(columns)]
            rows += ["| " + source + " | " + " | ".join(cell(item.get(column, "-")) for column in columns) + " |" for source, item in value.items()]
            return rows
        return ["| 비교 항목 | 내용 |", "|---|---|"] + [f"| {key} | {cell(item)} |" for key, item in value.items()]
    if isinstance(value, list):
        return ["| 번호 | 내용 |", "|---:|---|"] + [f"| {number} | {cell(item)} |" for number, item in enumerate(value, 1)]
    return ["| 내용 |", "|---|", f"| {cell(value)} |"]


def save_comparison_files(issue_id: int, items: list[dict], result: dict) -> None:
    output_dir = Path("outputs/reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    title = items[0].get("title", f"issue_{issue_id}")
    sources = sorted({item.get("source", "") for item in items})
    markdown = [f"# 동일 이슈 뉴스 비교: {title}", "", "## 참여 뉴스 소스"]
    markdown += [f"- {source}" for source in sources]
    text = [f"동일 이슈 뉴스 비교: {title}", "", "참여 뉴스 소스", ", ".join(sources)]
    markdown += ["", "## 공통 사실", "", "- 기사 주제와 보도 시점은 양쪽 기사에서 공통으로 확인되는 내용입니다.", "", "## 한눈에 보는 소스별 비교", "", f"| 비교축 | {sources[0]} | {sources[1] if len(sources) > 1 else '소스 B'} |", "|---|---|---|"]
    for axis, label in COMPARISON_AXES:
        if axis == "common_facts":
            continue
        value = axis_value(result, axis)
        first = value.get(sources[0], value) if isinstance(value, dict) else value
        second = value.get(sources[1], value) if isinstance(value, dict) and len(sources) > 1 else value
        first_cell = format_value(first).replace("|", "\\|").replace("\n", "<br>")
        second_cell = format_value(second).replace("|", "\\|").replace("\n", "<br>")
        markdown.append(f"| {label} | {first_cell} | {second_cell} |")
        text += ["", f"{number}. {label}", format_value(value)]
    (output_dir / f"comparison_issue_{issue_id}.md").write_text("\n".join(markdown), encoding="utf-8")
    (output_dir / f"comparison_issue_{issue_id}.txt").write_text("\n".join(text), encoding="utf-8")
    print(f"비교 결과 저장: outputs/reports/comparison_issue_{issue_id}.md")
