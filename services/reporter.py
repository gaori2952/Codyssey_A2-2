from pathlib import Path
import json

import matplotlib.pyplot as plt
from matplotlib import font_manager

from database.db import get_connection


def format_comparison_value(value) -> str:
    if isinstance(value, dict):
        return "\n".join(f"- **{key}**: {format_comparison_value(item)}" for key, item in value.items())
    if isinstance(value, list):
        return "\n".join(f"- {format_comparison_value(item)}" for item in value)
    return str(value or "-")


def markdown_cell(value) -> str:
    text = format_comparison_value(value).replace("|", "\\|")
    return text.replace("\n", "<br>")


def comparison_table(value) -> list[str]:
    if isinstance(value, dict):
        if set(value).issubset({"관점 차이", "종합 시사점"}):
            return ["| 비교 항목 | 내용 |", "|---|---|"] + [f"| {key} | {markdown_cell(item)} |" for key, item in value.items()]
        keys = list(value.keys())
        if keys and all(isinstance(item, dict) for item in value.values()):
            columns = sorted({key for item in value.values() for key in item})
            lines = ["| 뉴스 소스 | " + " | ".join(columns) + " |", "|---|" + "---|" * len(columns)]
            for source, item in value.items():
                lines.append("| " + source + " | " + " | ".join(markdown_cell(item.get(column, "-")) for column in columns) + " |")
            return lines
        return ["| 비교 항목 | 내용 |", "|---|---|"] + [f"| {key} | {markdown_cell(item)} |" for key, item in value.items()]
    if isinstance(value, list):
        return ["| 번호 | 내용 |", "|---:|---|"] + [f"| {number} | {markdown_cell(item)} |" for number, item in enumerate(value, 1)]
    return ["| 내용 |", "|---|", f"| {markdown_cell(value)} |"]


def short_trend(text: str) -> list[str]:
    sentences = [part.strip() for part in str(text or "").replace("。", ".").split(".") if part.strip()]
    return [f"- {sentence}." for sentence in sentences[:5]] or ["- 아직 저장된 AI 분석 결과가 없습니다."]


def source_summary(rows, maximum: int = 5):
    rows = list(rows)
    if len(rows) <= maximum:
        return rows
    top = rows[:maximum]
    other_count = sum(row[1] for row in rows[maximum:])
    return top + [("기타", other_count)]


def comparison_cell(value, source: str, axis: str) -> str:
    def clean_label(text: str) -> str:
        return text.replace(f"{source} 주요 키워드:", "", 1).replace(f"{source}:", "", 1).replace(f"{source}는 ", "", 1).replace(f"{source}의 ", "", 1).strip(" -")

    if isinstance(value, dict):
        if source in value:
            return markdown_cell(value[source])
        if source == "CNBC" and "as_presented_by_CNBC" in value:
            return markdown_cell(value["as_presented_by_CNBC"])
        if source == "Politico" and "as_presented_by_Politico" in value:
            return markdown_cell(value["as_presented_by_Politico"])
        return markdown_cell(value)
    if isinstance(value, list):
        source_items = []
        for item in value:
            item_text = str(item)
            other_source = "Politico" if source == "CNBC" else "CNBC"
            if source in item_text and other_source not in item_text:
                source_items.append(clean_label(item_text))
            elif axis == "expression_differences" and source == "CNBC" and "CNBC" not in item_text and "Politico" not in item_text:
                source_items.append(item_text)
        if source_items:
            return markdown_cell(source_items)
        return "-"
    if isinstance(value, str) and axis != "common_facts":
        lines = [line.strip(" -") for line in value.splitlines() if line.strip()]
        other_source = "Politico" if source == "CNBC" else "CNBC"
        source_lines = [line for line in lines if source in line and other_source not in line]
        if source_lines:
            return markdown_cell([clean_label(line) for line in source_lines])
        if lines and not any(name in value for name in ("CNBC", "Politico")):
            return markdown_cell(lines)
        return "-"
    return markdown_cell(value)


def unified_comparison_table(comparison_data, sources: list[str], common_text: str) -> list[str]:
    first = sources[0] if sources else "소스 A"
    second = sources[1] if len(sources) > 1 else "소스 B"
    axes = [("소스별 강조점", "source_emphasis"), ("표현·제목 차이", "expression_differences"), ("핵심 키워드 차이", "keyword_differences"), ("관점·종합 시사점", "perspective_implications")]
    lines = ["<table>", "<thead>", f"<tr><th>비교축</th><th>{first}</th><th>{second}</th></tr>", "</thead>", "<tbody>", f"<tr><th>공통 사실</th><td colspan=\"2\">{common_text}</td></tr>"]
    for label, key in axes:
        value = comparison_data.get(key, "")
        if key == "perspective_implications" and "perspective_implications" not in comparison_data:
            value = {"관점 차이": comparison_data.get("perspective_differences", ""), "종합 시사점": comparison_data.get("implications", "")}
        first_cell = comparison_cell(value, first, key).replace("**", "")
        second_cell = comparison_cell(value, second, key).replace("**", "")
        lines.append(f"<tr><th>{label}</th><td>{first_cell}</td><td>{second_cell}</td></tr>")
    lines += ["</tbody>", "</table>"]
    return lines


def _setup_font() -> None:
    candidates = [
        "Malgun Gothic",
        "AppleGothic",
        "Apple SD Gothic Neo",
        "NanumGothic",
        "NanumBarunGothic",
        "Noto Sans CJK KR",
        "Noto Sans KR",
    ]
    available = {font.name for font in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            plt.rcParams["font.family"] = name
            break
    plt.rcParams["axes.unicode_minus"] = False


def _save_bar_chart(rows, title: str, path: str, color: str) -> None:
    labels = [row[0] or "미상" for row in rows]
    values = [row[1] for row in rows]
    figure, axis = plt.subplots(figsize=(9, 5.5))
    figure.patch.set_facecolor("#f7f9fc")
    axis.set_facecolor("#f7f9fc")
    if values:
        bars = axis.barh(labels[::-1], values[::-1], color=color, height=0.62)
        axis.bar_label(bars, labels=[f"{value}건" for value in values[::-1]], padding=5, fontsize=9)
        axis.set_xlim(0, max(values) * 1.2)
    else:
        axis.text(0.5, 0.5, "표시할 데이터가 없습니다", ha="center", va="center", transform=axis.transAxes)
    axis.set_title(title, loc="left", fontsize=16, fontweight="bold", pad=18, color="#172033")
    axis.set_xlabel("기사 수", color="#566174")
    axis.grid(axis="x", color="#dfe5ee", linewidth=0.8)
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.tick_params(axis="y", length=0, colors="#344054")
    axis.tick_params(axis="x", colors="#667085")
    figure.tight_layout()
    figure.savefig(path, dpi=160, facecolor=figure.get_facecolor())
    plt.close(figure)


def _save_line_chart(rows, path: str) -> None:
    labels = [row[0] for row in rows]
    values = [row[1] for row in rows]
    figure, axis = plt.subplots(figsize=(9, 5.5))
    figure.patch.set_facecolor("#f7f9fc")
    axis.set_facecolor("#f7f9fc")
    if values:
        axis.plot(labels, values, color="#e76f51", marker="o", linewidth=2.5, markersize=7)
        for label, value in zip(labels, values):
            axis.annotate(f"{value}건", (label, value), textcoords="offset points", xytext=(0, 9), ha="center", fontsize=9, color="#b54708")
        axis.tick_params(axis="x", rotation=45)
    else:
        axis.text(0.5, 0.5, "표시할 데이터가 없습니다", ha="center", va="center", transform=axis.transAxes)
    axis.set_title("일자별 뉴스 수집 추이", loc="left", fontsize=16, fontweight="bold", pad=18, color="#172033")
    axis.set_ylabel("기사 수", color="#566174")
    axis.grid(color="#dfe5ee", linewidth=0.8)
    axis.spines[["top", "right"]].set_visible(False)
    axis.tick_params(colors="#667085")
    figure.tight_layout()
    figure.savefig(path, dpi=160, facecolor=figure.get_facecolor())
    plt.close(figure)


def create_report() -> None:
    Path("outputs/charts").mkdir(parents=True, exist_ok=True)
    Path("outputs/reports").mkdir(parents=True, exist_ok=True)
    with get_connection() as connection:
        raw_count = connection.execute("SELECT COUNT(*) FROM raw_news").fetchone()[0]
        clean_count = connection.execute("SELECT COUNT(*) FROM clean_news").fetchone()[0]
        summarized = connection.execute("SELECT COUNT(*) FROM clean_news WHERE summary_status = 'summarized'").fetchone()[0]
        required = connection.execute("SELECT COUNT(*) FROM clean_news WHERE title <> '' AND url <> ''").fetchone()[0]
        dated = connection.execute("SELECT COUNT(*) FROM clean_news WHERE published_at <> ''").fetchone()[0]
        source_count = connection.execute("SELECT COUNT(DISTINCT source) FROM clean_news").fetchone()[0]
        issue_count = connection.execute("SELECT COUNT(*) FROM issues").fetchone()[0]
        comparable_count = connection.execute("SELECT COUNT(*) FROM (SELECT issue_id FROM clean_news WHERE issue_id IS NOT NULL GROUP BY issue_id HAVING COUNT(DISTINCT source) >= 2)").fetchone()[0]
        categories = connection.execute("SELECT category, COUNT(*) count FROM clean_news GROUP BY category ORDER BY count DESC LIMIT 5").fetchall()
        sources = connection.execute("SELECT source, COUNT(*) count FROM clean_news GROUP BY source ORDER BY count DESC").fetchall()
        daily = connection.execute("SELECT published_at, COUNT(*) count FROM clean_news WHERE published_at <> '' GROUP BY published_at ORDER BY published_at").fetchall()
        analysis = connection.execute("SELECT * FROM analyses WHERE analysis_type = 'trend' OR analysis_type IS NULL ORDER BY id DESC LIMIT 1").fetchone()
        comparison = connection.execute("SELECT a.*, i.issue_title FROM analyses a LEFT JOIN issues i ON i.id = a.issue_id WHERE a.analysis_type = 'comparison' ORDER BY a.id DESC LIMIT 1").fetchone()
        comparison_sources = []
        comparison_items = []
        if comparison:
            comparison_sources = [row[0] for row in connection.execute("SELECT DISTINCT source FROM clean_news WHERE issue_id = ? ORDER BY source", (comparison["issue_id"],))]
            comparison_items = [dict(row) for row in connection.execute("SELECT title, source, published_at FROM clean_news WHERE issue_id = ? ORDER BY id", (comparison["issue_id"],))]
    _setup_font()
    _save_bar_chart(categories, "카테고리별 뉴스 수", "outputs/charts/category_count.png", "#2a9d8f")
    _save_line_chart(daily, "outputs/charts/daily_news_count.png")
    _save_bar_chart(source_summary(sources), "뉴스 소스별 기사 수", "outputs/charts/source_count.png", "#457b9d")
    completion = summarized / clean_count * 100 if clean_count else 0
    required_completion = required / clean_count * 100 if clean_count else 0
    completeness = dated / clean_count * 100 if clean_count else 0
    lines = [
        "# 뉴스 파이프라인 리포트", "",
        "> 수집부터 정제, 요약, 분석까지의 실행 결과를 한눈에 확인하는 리포트입니다.", "",
        "## 핵심 지표", "",
        "| 지표 | 결과 |", "|---|---:|",
        f"| Raw 뉴스 | {raw_count}건 |", f"| Clean 뉴스 | {clean_count}건 |",
        f"| 요약 완료 | {summarized}건 |", f"| 요약 완료율 | {completion:.1f}% |",
        f"| 필수 필드 완성률 | {required_completion:.1f}% |",
        f"| 날짜 필드 완성률 | {completeness:.1f}% |", f"| 뉴스 소스 | {source_count}개 |",
        f"| 생성된 이슈 | {issue_count}개 |", f"| 비교 가능한 이슈 | {comparable_count}개 |", "",
        "## 시각화", "",
        "### 카테고리별 뉴스 수", "", "![카테고리별 뉴스 수](../charts/category_count.png)", "",
        "### 일자별 뉴스 수집 추이", "", "![일자별 뉴스 수집 추이](../charts/daily_news_count.png)", "",
        "### 뉴스 소스별 기사 수", "", "![뉴스 소스별 기사 수](../charts/source_count.png)", "",
        "## 카테고리 TOP 5", "", "| 카테고리 | 기사 수 |", "|---|---:|",
    ]
    lines += [f"| {row[0]} | {row[1]}건 |" for row in categories]
    lines += ["", "## 뉴스 소스 통계", "", "| 뉴스 소스 | 기사 수 |", "|---|---:|"]
    lines += [f"| {row[0]} | {row[1]}건 |" for row in source_summary(sources)]
    lines += ["", "## AI 트렌드 분석"]
    if analysis:
        lines += ["", "### 주요 트렌드"] + short_trend(analysis["trend"])
        lines += ["", "### 핵심 키워드", format_comparison_value(analysis["keywords"]), "", "### 공통 이슈"] + short_trend(analysis["issues"])
        lines += ["", "### 시사점"] + short_trend(analysis["implications"])
    else:
        lines.append("\n아직 저장된 AI 분석 결과가 없습니다.")
    lines += ["", "## 동일 이슈 뉴스 비교"]
    if comparison:
        lines += [f"### {comparison['issue_title']}", "", "참여 뉴스 소스"]
        lines += [f"- {source}" for source in comparison_sources]
        try:
            comparison_data = json.loads(comparison["comparison_result"])
        except (TypeError, json.JSONDecodeError):
            comparison_data = {"common_facts": comparison["comparison_result"]}
        comparison_axes = [("common_facts", "공통 사실"), ("source_emphasis", "뉴스 소스별 강조점"), ("expression_differences", "표현·제목 차이"), ("keyword_differences", "핵심 키워드 차이"), ("perspective_implications", "관점·종합 시사점")]
        if "perspective_implications" not in comparison_data:
            comparison_data["perspective_implications"] = {"관점 차이": comparison_data.get("perspective_differences", ""), "종합 시사점": comparison_data.get("implications", "")}
        topic = comparison["issue_title"].rsplit(" - ", 1)[0]
        if "Hugging Face" in topic and "AI agent" in topic:
            topic = "허깅페이스 AI 에이전트 해킹 사건 관련 보도"
        dates = ", ".join(f"{item['source']}: {item['published_at'] or '날짜 없음'}" for item in comparison_items)
        common_text = f"- 주제: {topic}<br>- 보도 시점: {dates or '기사에 기록된 날짜 없음'}"
        lines += ["", "### 한눈에 보는 소스별 비교", ""] + unified_comparison_table(comparison_data, comparison_sources, common_text)
    else:
        lines.append("- 아직 저장된 동일 이슈 비교 결과가 없습니다.")
    Path("outputs/reports/report.md").write_text("\n".join(lines), encoding="utf-8")
    print("리포트와 차트를 생성했습니다.")
