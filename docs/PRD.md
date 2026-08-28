# CLI 기반 AI 뉴스 데이터 파이프라인 PRD

- 문서 버전: 1.0
- 작성일: 2026-08-27
- 대상 사용자: Python 초보자, Codyssey 과제 수행자
- 제품 형태: Python CLI 프로그램

## 1. 제품 개요

인터넷에서 IT/Technology 뉴스를 RSS와 웹 크롤링으로 수집한다. 수집한 원본을 SQLite에 보존하고, 정제·분류·AI 요약·트렌드 분석·리포트·파일 export까지 한 번에 수행할 수 있는 학습용 데이터 파이프라인을 제공한다.

핵심 흐름:

```text
뉴스 수집 -> Raw 저장 -> 정제 -> Clean 저장 -> AI 요약 -> 분석 -> 리포트/export
```

## 2. 목표와 범위

### 목표

- 명령줄에서 모든 기능을 실행한다.
- 기능별 Python 모듈을 분리해 초보자가 읽고 수정하기 쉽게 한다.
- 원본 데이터와 정제 데이터를 분리한다.
- 같은 URL 중복과 서로 다른 기사의 동일 이슈를 구분한다.
- API Key를 코드에 저장하지 않는다.
- 네트워크, AI, DB 오류가 발생해도 가능한 작업은 계속한다.

### 범위에 포함하지 않는 것

- 웹 UI 또는 웹 서버
- 복잡한 머신러닝 모델
- 벡터 DB, 임베딩, 외부 검색 엔진
- 대규모 비동기 수집 시스템
- 자동으로 API Key를 발급하거나 관리하는 기능

## 3. 사용자 시나리오

1. 사용자는 `fetch`로 RSS 또는 웹 뉴스를 수집한다.
2. 프로그램은 URL 중복을 검사하고 원본을 `raw_news`에 저장한다.
3. 사용자는 `clean`으로 HTML, 공백, 날짜, 필수 필드를 정리한다.
4. 프로그램은 제목과 본문 키워드로 카테고리를 분류하고 `clean_news`에 저장한다.
5. 사용자는 API Key를 환경변수로 설정한 뒤 미요약 뉴스를 요약한다.
6. 사용자는 전체 트렌드 또는 특정 이슈의 소스별 비교 분석을 실행한다.
7. 사용자는 Markdown 리포트, 차트, CSV, Excel, JSONL 결과를 확인한다.

## 4. 기능 요구사항

### 4.1 CLI

`argparse` 서브커맨드를 사용한다.

```text
py main.py fetch --source rss --limit 10
py main.py fetch --source crawl --limit 10
py main.py fetch --source api --limit 10
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

### 4.2 뉴스 수집

- RSS 수집은 `feedparser`를 사용한다.
- 웹 수집은 `requests`와 `BeautifulSoup`를 사용한다.
- API 수집은 `requests`를 사용하며 `config.json`의 `api_sources`에 등록한 REST API를 선택적으로 호출한다.
- 제목, 본문 또는 요약, URL, 게시일, 실제 소스명, 수집 방식, 수집 시각을 저장한다.
- 크롤링에는 timeout, User-Agent, 요청 지연, HTTP 오류 처리를 적용한다.
- URL과 주요 수집 설정은 `config.json`에서 관리한다.
- 여러 RSS/crawl 소스를 등록할 수 있어야 한다.

### 4.3 SQLite 저장

영구 저장 위치는 `data/news.db`다.

필수 테이블:

- `raw_news`: 삭제하지 않는 수집 원본
- `clean_news`: 정제·분류·요약 결과
- `issues`: 동일 이슈 그룹
- `analyses`: 트렌드 분석 및 소스 비교 분석

URL 중복 정책:

- `skip`: 이미 존재하는 URL을 저장하지 않는다.
- `upsert`: 같은 URL의 내용을 갱신한다.

기존 DB가 있으면 테이블을 삭제하지 않고 필요한 컬럼만 migration한다.

### 4.4 정제와 분류

- 제목과 URL이 없는 행을 제외한다.
- 앞뒤 공백과 연속 공백을 정리한다.
- HTML 태그를 제거한다.
- 날짜를 가능한 경우 `YYYY-MM-DD`로 통일한다.
- 결측값은 빈 문자열 등 안전한 기본값으로 처리한다.
- 키워드 기반으로 AI, 반도체, 클라우드, 보안, 소프트웨어, 기타로 분류한다.
- 원본 `raw_news`는 삭제하지 않는다.

### 4.5 AI 요약

- Codyssey Chat Completions API를 사용한다.
- API Key는 `CODYSSEY_API_KEY` 환경변수에서 읽는다.
- 기존 호환을 위해 `OPENAI_API_KEY`도 읽을 수 있다.
- 요약은 3문장 이내, 사실 중심, 추측 금지로 요청한다.
- 성공한 행은 `summary_status = summarized`로 저장한다.
- API 오류가 나면 해당 행을 건너뛰고 로그를 남긴다.

### 4.6 분석

전체 분석:

- 주요 트렌드
- 핵심 키워드
- 공통 이슈
- 시사점

동일 이슈 비교:

- 같은 `issue_id`이면서 서로 다른 소스의 기사가 2개 이상인 이슈만 비교한다.
- 공통 사실, 소스별 강조점, 표현·제목 차이, 핵심 키워드 차이, 관점·종합 시사점을 만든다.
- 어느 소스가 옳거나 틀린지 판정하지 않는다.
- 기사에 없는 내용을 추측하지 않는다.
- 결과는 콘솔과 Markdown/TXT 파일, `analyses` 테이블에 저장한다.

### 4.7 리포트와 시각화

`report`는 다음을 포함한다.

- Raw/Clean/요약 완료 수
- 요약 완료율, 날짜 필드 완성률 등 품질 지표 2개 이상
- 카테고리 TOP 5
- 뉴스 소스 수와 소스별 통계
- 생성된 이슈 수와 비교 가능한 이슈 수
- 최근 AI 트렌드
- 최근 동일 이슈 비교 결과

PNG 차트:

- `category_count.png`: 카테고리별 뉴스 수
- `daily_news_count.png`: 일자별 수집 추이
- `source_count.png`: 뉴스 소스별 기사 수

Windows에서는 `Malgun Gothic`을 우선 사용하며, 없으면 기본 폰트로 계속 실행한다.

### 4.8 Export

- 정제 뉴스를 CSV로 저장한다.
- 정제 뉴스를 Excel로 저장한다.
- `--status summarized`로 요약 완료 뉴스만 필터링한다.
- source, category, issue_id, summary, summary_status를 포함한다.

## 5. 데이터 모델

### raw_news

`id`, `title`, `content`, `url`, `published_at`, `source`, `collection_method`, `collected_at`

### clean_news

`id`, `raw_id`, `title`, `content`, `url`, `published_at`, `source`, `category`, `summary`, `summary_status`, `issue_id`, `created_at`, `updated_at`

### issues

`id`, `issue_title`, `category`, `created_at`

### analyses

`id`, `date_from`, `date_to`, `category`, `trend`, `keywords`, `issues`, `implications`, `analysis_type`, `issue_id`, `comparison_result`, `created_at`

## 6. 설정과 보안

`config.json`은 URL, timeout, delay, 중복 정책만 저장한다. API Key는 저장하지 않는다.

```json
{
  "duplicate_policy": "skip",
  "request_timeout": 10,
  "crawl_delay": 1
}
```

API Key는 PowerShell 환경변수로 설정한다.

```powershell
$env:CODYSSEY_API_KEY = "발급받은_virtual-key"
```

`.venv`, `.env`, `*.db`, 로그와 생성 결과는 Git에 올리지 않는다.

## 7. 오류 처리와 로그

- RSS 접근 실패: 오류 기록 후 프로그램 종료를 막는다.
- 크롤링 실패/timeout/HTTP 오류: 해당 수집 실행을 안내하고 종료를 막는다.
- 본문 누락: 제목 등 사용 가능한 필드로 계속 처리한다.
- AI 실패: 해당 기사만 건너뛴다.
- 비교 대상 부족: `[INFO] 비교 가능한 동일 이슈가 없습니다.`를 출력한다.
- 로그 위치: `logs/app.log`
- 로그 레벨: INFO, WARNING, ERROR

## 8. 완료 기준

- 모든 필수 서브커맨드가 `--help`에 표시된다.
- SQLite DB와 Raw/Clean 분리가 동작한다.
- 동일 URL 중복 정책이 동작한다.
- RSS 및 크롤링 수집이 동작한다.
- AI 요약과 트렌드 분석 결과가 저장된다.
- 서로 다른 소스의 동일 이슈 비교 결과가 저장된다.
- Markdown 리포트, 3개 PNG 차트, CSV, Excel이 생성된다.
- API Key가 코드나 설정 파일에 들어 있지 않다.
- 기존 DB 데이터가 migration 과정에서 삭제되지 않는다.
