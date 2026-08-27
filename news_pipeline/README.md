# CLI 기반 AI 뉴스 데이터 파이프라인

RSS와 웹 크롤링으로 IT 뉴스를 모으고, SQLite에 저장한 뒤 정제, AI 요약, AI 분석, 리포트, CSV/Excel 내보내기를 수행하는 초보자용 Python CLI 프로젝트입니다.

문서:

- [초기 PRD](docs/PRD.md)
- [현재 구현 변경점 브리핑](docs/CHANGE_BRIEF.md)

## 데이터 흐름

`fetch -> raw_news -> clean -> clean_news -> summarize/analyze -> report/export`

원본(`raw_news`)과 정제 데이터(`clean_news`)를 나누면 수집한 원본을 보존하면서 정제 규칙을 다시 적용할 수 있습니다.

## 폴더 구조

```text
main.py                 CLI 진입점
config.json             RSS/크롤링 URL과 실행 설정
collectors/             RSS 및 웹 수집기
services/               정제, AI, 분석, 리포트, export
database/                SQLite 저장소
utils/                  로깅
 data/news.db            영구 SQLite DB
 logs/app.log            실행 로그
 outputs/                차트, Markdown, CSV/Excel 결과
```

## 설치

PowerShell에서 프로젝트 폴더로 이동합니다.

```powershell
cd C:\Users\Kaon\Desktop\news_pipeline
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

가상환경 활성화가 어려우면 아래처럼 가상환경 Python을 직접 사용할 수 있습니다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## API Key 설정

PowerShell에서 현재 창에만 적용하려면 다음을 실행합니다. 실제 키는 파일에 저장하거나 Git에 올리지 마세요.

```powershell
$env:CODYSSEY_API_KEY = "여기에_복사한_virtual-key"
```

Codyssey API의 `https://copa.codyssey.kr/v1/chat/completions` 주소와 `gpt-5-mini` 모델을 사용합니다.

키가 없으면 `summarize`와 `analyze`는 오류를 로그에 남기고 종료되며, 수집/정제/리포트/export 기능은 사용할 수 있습니다.

## CLI 사용 예시

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
py main.py export --format csv --status summarized
```

`fetch --source rss`는 RSS가 제공하는 구조화된 제목, 링크, 날짜, 요약을 사용합니다. `crawl`은 HTML을 직접 요청해 링크와 제목을 찾아오므로 사이트 구조가 바뀌면 `collectors/crawler.py`의 선택자를 수정해야 합니다. 요청 timeout, User-Agent, 짧은 지연, HTTP 오류 처리를 적용했습니다.

`clean`은 공백과 HTML을 정리하고 URL/제목/날짜를 검사하며 키워드로 AI, 반도체, 클라우드, 보안, 소프트웨어, 기타로 분류합니다. 원본 행은 삭제하지 않습니다. URL 중복 정책은 `config.json`의 `duplicate_policy`에서 `skip` 또는 `upsert`로 바꿀 수 있습니다.

`config.json`의 `rss_sources`와 `crawl_sources`에 여러 소스를 등록할 수 있습니다. 현재 RSS는 OpenAI/AI 모델이라는 공통 주제를 두 검색어로 수집하므로 같은 사건을 다룬 여러 매체의 기사가 모일 가능성이 높습니다. RSS 항목의 실제 발행 매체명을 `source`로 저장합니다. 같은 URL은 중복 뉴스로 처리하지만, URL이 다른 기사는 삭제하지 않습니다. 정제 후 제목과 키워드가 비슷한 기사는 `issue_id`로 같은 이슈에 연결합니다. 새 기사를 수집한 뒤 `clean`을 다시 실행해야 그룹화됩니다. `analyze --issue 3`은 특정 이슈를 비교하고, `analyze --compare`는 서로 다른 소스가 2개 이상인 이슈를 모두 비교합니다.

`report`는 `outputs/charts/category_count.png`, `outputs/charts/daily_news_count.png`, `outputs/reports/report.md`를 만듭니다. Windows에서 Malgun Gothic을 찾으면 사용하고, 없으면 matplotlib 기본 폰트를 사용합니다. `export` 결과는 `outputs/exports/`에 저장됩니다.

## 오류 처리와 로그

주요 진행 상황과 오류는 콘솔 및 `logs/app.log`에 `[INFO]`, `[WARNING]`, `[ERROR]` 형식으로 기록합니다. 네트워크 오류는 해당 수집 실행에서 안내하고, AI 호출 오류는 해당 뉴스만 건너뜁니다.

## Windows 작업 스케줄러

작업 스케줄러에서 기본 작업을 만든 뒤 프로그램에 프로젝트의 `.venv\Scripts\python.exe`를, 인수에 `main.py fetch --source rss --limit 10`을, 시작 위치에 프로젝트 폴더를 지정합니다. 정제와 리포트는 별도 작업으로 `main.py clean`, `main.py report`를 순서대로 등록하면 됩니다.
