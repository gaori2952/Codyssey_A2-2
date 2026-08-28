# CLI 기반 AI 뉴스 데이터 파이프라인

여러 뉴스 출처의 기사를 RSS와 웹 크롤링으로 수집하고, 동일 이슈를 자동으로 그룹화한 뒤 출처별 관점 차이를 AI로 비교 분석하는 Python CLI 기반 뉴스 데이터 파이프라인입니다. 수집부터 정제, 요약, 인사이트 분석, 시각화, 리포트, Export까지 하나의 흐름으로 수행합니다.

이 프로젝트의 주요 특화 기능은 다음과 같습니다.

- RSS와 웹 크롤링 결과를 하나의 파이프라인으로 통합
- 원본(`raw_news`)과 정제(`clean_news`) 데이터를 분리해 재처리 가능
- URL 중복과 내용이 유사한 동일 이슈를 구분
- `issue_id` 기반 동일 이슈 그룹화
- 출처별 강조점, 표현, 키워드, 관점 차이 비교
- 요약 완료율과 필수·날짜 필드 완성률을 포함한 품질 리포트 제공
- Markdown 리포트와 카테고리·날짜·소스별 차트 생성
- CSV, Excel, JSONL 형식 Export 지원

## 1. 주요 기능

- **뉴스 수집**: RSS, 웹 크롤링, REST API, 복수 뉴스 소스 설정
- **데이터 정제**: HTML 제거, 공백·날짜 정규화, 제목·URL 검증, 카테고리 분류
- **AI 뉴스 요약**: 기사 기반 3문장 이내 요약 및 요약 상태 저장
- **AI 인사이트 분석**: 주요 트렌드, 핵심 키워드, 공통 이슈, 시사점
- **동일 이슈 비교**: `issue_id` 기반 그룹화 및 소스별 강조점·표현 차이 비교
- **시각화 및 리포트**: 카테고리·날짜·소스별 차트와 Markdown 리포트
- **데이터 Export**: CSV, Excel, JSONL

## 2. 역할 분담

| 팀원 | 역할 |
|---|---|
| 이가온 | 공통 PRD 통합, 전체 뉴스 데이터 파이프라인 구현, 동일 이슈 그룹화·언론사별 비교 분석 기능 구현, 리포트·Export 기능 확장, GitHub 저장소 및 문서화 등 모든 제출 문서 제작 및 코드 구현 |
| 이승환 | 특정 분야 뉴스 자동 수집·분석 방식 제안, 반도체 기술 변화 분석 및 브리핑 기능 확장 아이디어 제안 |
| 이태규 | 데이터 수집·정제·시각화 개선안 제안, 크롤링 fallback·데이터 검증·로깅 개선안 제안, 멀티 OS 한글 폰트 처리 개선안 제안 |
| 한민수 | 뉴스 수집 자동화 파이프라인 방향 제안, RSS·AI 요약·외부 데이터 저장 및 스케줄러 연동 아이디어 제안 |

팀원별 PRD와 개선 의견을 비교하고, 공통 프로젝트에 적용할 수 있는 기능을 중심으로 현재 파이프라인에 반영했습니다.

## 3. 데이터 파이프라인

```text
RSS / Crawl
	↓
   fetch
	↓
  raw_news
	↓
    clean
	↓
 clean_news
	↓
동일 이슈 그룹화
	↓
 summarize
	↓
analyze / compare
	↓
report / export
```

권장 실행 순서:

```text
fetch → clean → summarize → analyze → report → export
```

`analyze`는 요약 완료 뉴스(`summary_status = summarized`)를 대상으로 하므로, AI 분석 전에 `clean`과 `summarize`를 실행해야 합니다.

## 4. 프로젝트 구조

```text
news_pipeline/
├── main.py
├── verify_jsonl_export.py
├── config.json
├── requirements.txt
├── README.md
├── .gitignore
├── collectors/                     # RSS·웹·REST API 수집 모듈
│   ├── __init__.py
│   ├── rss_collector.py
│   ├── api_collector.py
│   └── crawler.py
├── services/                       # 정제, AI, 이슈 비교, 리포트, Export 모듈
│   ├── __init__.py
│   ├── cleaner.py
│   ├── ai_service.py
│   ├── analyzer.py
│   ├── comparator.py
│   ├── issue_grouper.py
│   ├── reporter.py
│   └── exporter.py
├── database/                       # SQLite 초기화와 데이터 저장·조회
│   ├── __init__.py
│   └── db.py
├── utils/                          # 공통 유틸리티 모듈
│   ├── __init__.py
│   └── logger.py
├── docs/                            # 요구사항과 평가 문서
│   ├── PRD.md
│   └── EVALUATION.md
├── data/                            # SQLite 데이터베이스 저장 폴더
│   └── .gitkeep
├── logs/                            # 실행 로그 저장 폴더
│   └── .gitkeep
├── outputs/                         # 리포트, 차트, Export 결과 저장 폴더
│   ├── charts/
│   ├── reports/
│   └── exports/
└── .venv/                           # 로컬 가상환경 폴더
```

## 5. 설치 및 설정

### 5.1 가상환경 및 의존성 설치

```powershell
cd C:\Users\Kaon\Desktop\news_pipeline
py -m venv .venv
\.venv\Scripts\Activate.ps1
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

## 6. 실행 방법

모든 명령은 프로젝트 가상환경의 Python으로 실행하는 것을 권장합니다.

### 6.1 뉴스 수집

```powershell
.\.venv\Scripts\python.exe main.py fetch --source rss --limit 10
.\.venv\Scripts\python.exe main.py fetch --source crawl --limit 10
```

REST API 소스도 `config.json`에 등록하면 선택적으로 수집할 수 있습니다.

```powershell
.\.venv\Scripts\python.exe main.py fetch --source api --limit 10
```

RSS, Crawl, API는 `config.json`에 등록된 여러 소스를 순서대로 처리합니다. 수집 데이터는 URL을 기준으로 중복 처리한 뒤 `raw_news`에 저장합니다.

API 소스 설정 예시는 다음과 같습니다.

```json
{
	"name": "Example API",
	"url": "https://example.com/api/news",
	"items_path": "items",
	"field_map": {
		"title": "title",
		"content": "description",
		"url": "url",
		"published_at": "published_at"
	}
}
```

### 6.2 데이터 정제

```powershell
.\.venv\Scripts\python.exe main.py clean
```

`clean`은 제목·URL 검증, HTML 및 연속 공백 제거, 날짜 정규화, 카테고리 분류, `clean_news` 저장, 동일 이슈 그룹화를 수행합니다. 정제에 실패한 행은 건너뛰며 `raw_news`는 삭제하지 않습니다.

### 6.3 AI 뉴스 요약

```powershell
.\.venv\Scripts\python.exe main.py summarize --unsummarized --limit 10
.\.venv\Scripts\python.exe main.py summarize --all
.\.venv\Scripts\python.exe main.py summarize --id 3
```

`--unsummarized`는 `summary_status = 'unsummarized'`인 뉴스만 대상으로 하고, 성공한 결과는 `clean_news.summary`와 `summary_status = 'summarized'`로 저장합니다. API 오류가 발생한 기사는 건너뛰고 로그를 남깁니다.

### 6.4 AI 인사이트 분석

```powershell
.\.venv\Scripts\python.exe main.py analyze
.\.venv\Scripts\python.exe main.py analyze --category AI
.\.venv\Scripts\python.exe main.py analyze --date-from 2026-08-01 --date-to 2026-08-31
```

분석 대상은 요약 완료 뉴스이며, 결과의 `trend`, `keywords`, `issues`, `implications`를 `analyses`에 저장하고 콘솔에 출력합니다.

### 6.5 동일 이슈 뉴스 비교

```powershell
.\.venv\Scripts\python.exe main.py analyze --issue 3
.\.venv\Scripts\python.exe main.py analyze --compare
```

서로 다른 소스의 기사가 2개 이상 연결된 이슈만 비교합니다. 결과는 콘솔, `analyses`, `outputs/reports/comparison_issue_<id>.md`, `outputs/reports/comparison_issue_<id>.txt`에 저장합니다.

### 6.6 리포트 및 Export

```powershell
.\.venv\Scripts\python.exe main.py report
.\.venv\Scripts\python.exe main.py export --format csv
.\.venv\Scripts\python.exe main.py export --format excel
.\.venv\Scripts\python.exe main.py export --format jsonl
.\.venv\Scripts\python.exe main.py export --format csv --status summarized
```

`report`는 리포트와 PNG 차트를 생성하고, CSV·Excel·JSONL은 각각 `export` 명령으로 생성합니다.

## 7. 핵심 설계

### 7.1 Raw / Clean 데이터 분리

- `raw_news`: 수집 직후 원본 기사 저장
- `clean_news`: 정제, 분류, 요약, 이슈 연결 결과 저장
- `analyses`: AI 트렌드 분석과 동일 이슈 비교 결과 저장

원본과 처리 결과를 분리해 재정제와 재분석이 가능하도록 구성했습니다. URL 중복은 `duplicate_policy`에 따라 `skip` 또는 `upsert`로 처리하고, 다른 URL의 유사 뉴스는 `issue_id`로 연결합니다.

### 7.2 데이터 정제 및 카테고리

`services/cleaner.py`에서 제목·URL 검증, HTML·공백 제거, 날짜 정규화, 결측값 처리, 키워드 기반 분류를 수행합니다. 카테고리는 AI, 반도체, 클라우드, 보안, 소프트웨어, 기타입니다.

### 7.3 RSS와 Crawl

RSS는 구조화된 메타데이터를 빠르게 수집하고, Crawl은 웹 페이지의 본문과 날짜를 보완합니다. Crawl은 User-Agent, timeout, 요청 간 delay를 적용하며 본문 추출 실패 시 제목을 fallback으로 사용합니다.

### 7.4 AI 프롬프트

요약은 핵심 내용 3문장 이내, 사실 중심, 추측 금지를 원칙으로 합니다. 인사이트 분석은 `trend`, `keywords`, `issues`, `implications` 구조를 사용하고, 동일 이슈 비교는 `common_facts`, `source_emphasis`, `expression_differences`, `keyword_differences`, `perspective_implications` 구조를 사용합니다.

## 8. 시각화 및 결과물

`report` 명령은 다음 리포트와 차트를 생성합니다.

```text
outputs/charts/category_count.png
outputs/charts/daily_news_count.png
outputs/charts/source_count.png
outputs/reports/report.md
```

`export` 명령은 다음 파일을 생성합니다.

```text
outputs/exports/news.csv
outputs/exports/news.xlsx
outputs/exports/news.jsonl
```

`data/news.db`는 CLI 실행 중 사용하는 SQLite 데이터베이스이고, `logs/app.log`는 실행 로그 파일입니다.

리포트에는 Raw/Clean 뉴스 수, 요약 완료율, 필수·날짜 필드 완성률, 소스·카테고리 통계, 이슈 수, AI 분석, 동일 이슈 비교 결과가 포함됩니다.

한글 차트는 설치된 폰트 중 `Malgun Gothic`, `AppleGothic`, `Apple SD Gothic Neo`, `NanumGothic`, `NanumBarunGothic`, `Noto Sans CJK KR`, `Noto Sans KR` 순서로 fallback을 적용합니다.

## 9. 문서 및 평가

- [docs/PRD.md](docs/PRD.md): 프로젝트 기능 요구사항과 데이터 파이프라인 설계
- [docs/EVALUATION.md](docs/EVALUATION.md): 프롬프트 설계, 실험 계획, RSS/Crawl 불일치 검증, AI 비용 최적화

## 10. 검증 및 오류 처리

주요 진행 상황과 오류는 콘솔 및 `logs/app.log`에 기록합니다. RSS/Crawl 수집과 AI 호출은 실패 시 오류를 기록하고 해당 작업을 종료하며, 요약 처리에서는 실패한 기사 다음 작업을 계속합니다. API Key가 없으면 AI 요청을 수행하지 않습니다.

JSONL Export를 비파괴 방식으로 확인하려면 다음을 실행합니다.

```powershell
.\.venv\Scripts\python.exe verify_jsonl_export.py
```

API Key, 데이터베이스 원본, 로그에는 민감정보가 포함될 수 있으므로 GitHub에 업로드하지 않습니다.

## 11. 기술 스택

- Python 3.10+
- argparse
- SQLite
- feedparser
- requests / BeautifulSoup
- pandas / openpyxl
- matplotlib
- Codyssey API
- Git / GitHub
