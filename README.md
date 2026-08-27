# CLI 기반 AI 뉴스 데이터 파이프라인

RSS와 웹 크롤링으로 IT 뉴스를 수집하고, SQLite에 저장한 뒤 정제·분류·AI 요약·분석·리포트·Export까지 수행하는 Python CLI 프로젝트입니다.

## 1. 프로젝트 소개

이 프로젝트는 원본 기사와 정제된 기사 데이터를 분리해 보관하면서, 동일 이슈를 비교하고 통합 리포트를 생성하는 흐름을 학습용으로 구성한 뉴스 데이터 파이프라인입니다.

핵심 목표:

- RSS와 웹 크롤링을 모두 활용해 뉴스 수집
- 원본(raw_news)과 정제(clean_news) 데이터를 분리 보관
- 중복 기사와 동일 이슈를 구분해 비교 가능하게 구성
- AI 요약 및 소스별 비교 분석 수행
- Markdown, 차트, CSV, Excel, JSONL 결과물 생성

## 2. 주요 기능

- fetch: RSS 또는 웹 크롤링으로 뉴스 수집
- clean: HTML/공백/날짜 정리, 분류, 중복 처리
- summarize: AI 요약 생성
- analyze: 트렌드 분석, 특정 카테고리/기간/이슈 분석
- report: 통계 리포트와 차트 생성
- export: CSV, Excel, JSONL 파일 내보내기

## 3. 데이터 파이프라인 흐름

```text
fetch -> raw_news -> clean -> clean_news -> summarize -> analyze -> report -> export
```

핵심 원칙:

- 원본 데이터는 유지하고 정제 데이터를 별도로 저장
- 같은 URL은 중복으로 처리하고, 다른 URL의 유사 기사는 issue_id로 연결
- 정제 과정에서 날짜, 제목, URL, 카테고리를 표준화
- AI 분석은 사실 중심으로 제한하고 구조화된 JSON 형식으로 추출

## 4. 전체 프로젝트 구조

```text
news_pipeline/
├── main.py
├── config.json
├── requirements.txt
├── README.md
├── .gitignore
├── collectors/
│   ├── __init__.py
│   ├── rss_collector.py
│   └── crawler.py
├── services/
│   ├── __init__.py
│   ├── cleaner.py
│   ├── ai_service.py
│   ├── analyzer.py
│   ├── comparator.py
│   ├── issue_grouper.py
│   ├── reporter.py
│   └── exporter.py
├── database/
│   ├── __init__.py
│   └── db.py
├── utils/
│   ├── __init__.py
│   └── logger.py
├── docs/
│   ├── PRD.md
│   └── EVALUATION.md
├── data/
│   └── .gitkeep
├── logs/
│   └── .gitkeep
├── outputs/
│   ├── charts/
│   ├── reports/
│   └── exports/
└── .venv/
```

## 5. 설치 및 실행 방법

### 5.1 가상환경 생성 및 의존성 설치

```powershell
cd C:\Users\Kaon\Desktop\news_pipeline
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

가상환경이 없으면 아래처럼 직접 실행할 수 있습니다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 5.2 API Key 설정

```powershell
$env:CODYSSEY_API_KEY = "여기에_복사한_virtual-key"
```

Codyssey API를 사용할 때는 CODYSSEY_API_KEY 또는 OPENAI_API_KEY 환경변수를 사용합니다.

## 6. CLI 명령어

```powershell
py main.py fetch --source rss --limit 10
py main.py fetch --source crawl --limit 10
py main.py clean
py main.py summarize --unsummarized --limit 10
py main.py summarize --all
py main.py summarize --id 3
py main.py analyze
py main.py analyze --category AI
py main.py analyze --date-from 2026-08-01 --date-to 2026-08-31
py main.py analyze --issue 3
py main.py analyze --compare
py main.py report
py main.py export --format csv
py main.py export --format excel
py main.py export --format jsonl
py main.py export --format csv --status summarized
```

## 7. 핵심 설계

### raw/clean 데이터 분리

- raw_news: 수집 직후 원본 데이터 저장
- clean_news: HTML 제거, 공백 정리, 날짜 정규화, 카테고리 분류 이후 결과 저장

이 구조는 다음 이유에서 중요합니다.

- 원본 데이터를 보존해 재정제, 재분석 가능
- 정제 규칙을 바꿔도 기존 데이터 유지
- 동일 이슈 비교와 출처별 분석을 분리해서 수행 가능

### 정제 규칙

clean 단계는 다음을 수행합니다.

- HTML 태그 제거
- 연속 공백 정리
- URL/제목/날짜 검증
- 타임존 포함 날짜를 ISO 날짜 형식으로 표준화
- 키워드 기반으로 AI, 반도체, 클라우드, 보안, 소프트웨어, 기타로 분류

### RSS와 Crawl

RSS와 Crawl은 각각 장단점이 있습니다.

- RSS: 빠르고 구조화된 메타데이터가 많음. 다만 본문 부족 가능성
- Crawl: 실제 본문 확보 가능. 다만 사이트 구조 변화에 취약

### 중복 정책: skip/upsert

config.json의 duplicate_policy는 다음 둘 중 하나를 선택합니다.

- skip: 같은 URL이 있으면 추가하지 않음
- upsert: 같은 URL이 있으면 최신 데이터로 갱신

### 실행 순서와 의존성

```text
fetch -> raw_news -> clean -> clean_news -> summarize -> analyze -> report -> export
```

권장 실행 순서:

1. fetch
2. clean
3. summarize
4. analyze
5. report
6. export

## 8. 결과물

프로젝트는 다음 결과물을 생성합니다.

- SQLite DB: data/news.db
- 로그: logs/app.log
- 리포트: outputs/reports/report.md
- 차트: outputs/charts/category_count.png, outputs/charts/daily_news_count.png
- export 파일: outputs/exports/news.csv, news.xlsx, news.jsonl

## 9. 상세 문서

- [docs/PRD.md](docs/PRD.md): 초기 제품 요구사항 문서
- [docs/EVALUATION.md](docs/EVALUATION.md): 프롬프트 설계와 평가 실험 정리

## 10. 오류 처리와 로그

주요 진행 상황과 오류는 콘솔 및 logs/app.log에 [INFO], [WARNING], [ERROR] 형식으로 기록합니다.

- 네트워크 오류는 해당 수집 실행에 안내
- AI 호출 실패는 해당 기사만 건너뜀
- summarize/analyze는 API Key가 없으면 로그를 남기고 종료

## 11. 참고

이 프로젝트는 기존 기능을 유지하면서, 수집·정제·AI 분석·리포트·Export 구조를 학습용으로 이해하기 쉽게 구성한 CLI 파이프라인입니다.
