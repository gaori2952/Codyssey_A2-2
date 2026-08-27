import argparse

from database.db import initialize_database


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CLI 기반 AI 뉴스 데이터 파이프라인")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser("fetch", help="RSS 또는 웹에서 뉴스를 수집합니다")
    fetch_parser.add_argument("--source", choices=["rss", "crawl"], required=True)
    fetch_parser.add_argument("--limit", type=int, default=10)

    subparsers.add_parser("clean", help="원본 뉴스를 정제합니다")
    summarize_parser = subparsers.add_parser("summarize", help="뉴스를 요약합니다")
    summarize_parser.add_argument("--all", action="store_true")
    summarize_parser.add_argument("--id", type=int)
    summarize_parser.add_argument("--unsummarized", action="store_true")
    summarize_parser.add_argument("--limit", type=int, default=10)

    analyze_parser = subparsers.add_parser("analyze", help="뉴스 인사이트를 분석합니다")
    analyze_parser.add_argument("--category")
    analyze_parser.add_argument("--date-from")
    analyze_parser.add_argument("--date-to")
    analyze_parser.add_argument("--issue", type=int)
    analyze_parser.add_argument("--compare", action="store_true")

    subparsers.add_parser("report", help="통계 리포트와 차트를 생성합니다")
    export_parser = subparsers.add_parser("export", help="정제 뉴스를 파일로 저장합니다")
    export_parser.add_argument("--format", choices=["csv", "excel", "jsonl"], required=True)
    export_parser.add_argument("--status", choices=["summarized"])
    return parser


def main() -> None:
    initialize_database()
    args = build_parser().parse_args()
    from database.db import get_summary_targets, load_config, save_raw_news, save_summary
    from utils.logger import get_logger

    logger = get_logger()
    config = load_config()
    if args.command == "fetch":
        from collectors.crawler import collect_crawl
        from collectors.rss_collector import collect_rss

        logger.info("뉴스 수집 시작")
        try:
            news_config = config["news"]
            if args.source == "rss":
                sources = news_config.get("rss_sources", [{"name": "RSS", "url": news_config.get("rss_url")}])
                items = []
                for source in sources:
                    if source.get("url"):
                        items.extend(collect_rss(source["url"], args.limit, source["name"]))
            else:
                sources = news_config.get("crawl_sources", [{"name": "Web crawl", "url": news_config.get("crawl_url")}])
                items = []
                for source in sources:
                    if source.get("url"):
                        items.extend(collect_crawl(source["url"], args.limit, config.get("request_timeout", 10), config.get("crawl_delay", 1), source["name"]))
            saved = save_raw_news(items)
            logger.info("%s 뉴스 %d건 수집, 신규 저장 %d건", args.source.upper(), len(items), saved)
        except Exception as error:
            logger.error("뉴스 수집 실패: %s", error)
    elif args.command == "clean":
        from services.cleaner import clean_all
        from services.issue_grouper import group_issues

        count = clean_all()
        grouped = group_issues()
        logger.info("뉴스 정제 완료: %d건, 동일 이슈 연결: %d건", count, grouped)
    elif args.command == "summarize":
        from services.ai_service import summarize_news

        targets = get_summary_targets(args.id, args.unsummarized or not args.all, args.limit)
        if not targets:
            print("요약할 뉴스가 없습니다. 먼저 clean을 실행하세요.")
        for item in targets:
            summary = summarize_news(item["title"], item["content"])
            if summary:
                save_summary(item["id"], summary)
                print(f"요약 완료: {item['id']} - {item['title']}")
    elif args.command == "analyze":
        from services.analyzer import run_analysis

        if args.issue or args.compare:
            from services.comparator import compare_issue, compare_all_issues

            if args.issue:
                compare_issue(args.issue)
            else:
                compare_all_issues()
        else:
            run_analysis(args.category, args.date_from, args.date_to)
    elif args.command == "report":
        from services.reporter import create_report

        create_report()
    elif args.command == "export":
        from services.exporter import export_news

        export_news(args.format, args.status)


if __name__ == "__main__":
    main()
