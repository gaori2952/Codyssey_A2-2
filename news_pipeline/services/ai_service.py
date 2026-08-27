import os
import json

import requests

from utils.logger import get_logger

logger = get_logger()
API_URL = "https://copa.codyssey.kr/v1/chat/completions"
MODEL = "gpt-5-mini"
PROMPT_RULES = "주어진 뉴스의 핵심 내용을 3문장 이내로 요약한다. 기사에 없는 내용을 추측하지 않는다. 사실 중심으로 간결하게 작성한다."


def _api_key() -> str | None:
    api_key = os.getenv("CODYSSEY_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("CODYSSEY_API_KEY가 설정되지 않았습니다.")
        return None
    return api_key


def _request_chat(messages: list[dict]) -> dict | None:
    api_key = _api_key()
    if api_key is None:
        return None
    try:
        api_key.encode("ascii")
    except UnicodeEncodeError:
        logger.error("API Key에 한글 또는 허용되지 않는 문자가 들어 있습니다. 실제 virtual-key만 입력하세요.")
        return None
    payload = {"model": MODEL, "messages": messages}
    try:
        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=60,
        )
        if not response.ok:
            logger.error("Codyssey API 요청 실패 (%s): %s", response.status_code, response.text[:1000])
            return None
        return response.json()
    except (requests.RequestException, UnicodeEncodeError) as error:
        logger.error("Codyssey API 요청 실패: %s", error)
        return None


def summarize_news(title: str, content: str) -> str | None:
    result = _request_chat([
        {"role": "system", "content": PROMPT_RULES},
        {"role": "user", "content": f"제목: {title}\n본문: {content}"},
    ])
    if not result:
        return None
    try:
        return result["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as error:
        logger.error("AI 요약 응답 형식이 올바르지 않습니다: %s", error)
        return None


def analyze_news(items: list[dict]) -> dict | None:
    source = "\n\n".join(f"제목: {item['title']}\n요약: {item.get('summary', '')}" for item in items)
    instruction = "다음 뉴스들을 분석해 JSON 객체로 답하세요. 키는 trend, keywords, issues, implications이며 값은 한국어 문자열입니다."
    result = _request_chat([
        {"role": "system", "content": instruction},
        {"role": "user", "content": source},
    ])
    if not result:
        return None
    try:
        content = result["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(content)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
        logger.error("AI 분석 응답 형식이 올바르지 않습니다: %s", error)
        return None


def compare_news(items: list[dict]) -> dict | None:
    articles = "\n\n".join(
        f"뉴스 소스: {item.get('source', '')}\n제목: {item.get('title', '')}\n요약: {item.get('summary', '')}\n게시 날짜: {item.get('published_at', '')}"
        for item in items
    )
    instruction = """동일 이슈를 다룬 뉴스 기사들을 다음 5개 축으로 비교 분석해 JSON 객체로 답하세요. 키는 common_facts, source_emphasis, expression_differences, keyword_differences, perspective_implications입니다. 모든 분석 내용은 반드시 자연스러운 한국어로 작성하세요. 소스명과 고유명사, 필요한 원문 키워드는 그대로 두어도 됩니다. 각 값은 짧은 문장이나 항목 목록으로 작성하세요. 기사에 없는 내용을 추측하지 말고, 어느 소스가 옳거나 틀린지 판단하지 마세요."""
    result = _request_chat([
        {"role": "system", "content": instruction},
        {"role": "user", "content": articles},
    ])
    if not result:
        return None
    try:
        content = result["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(content)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
        logger.error("AI 비교 응답 형식이 올바르지 않습니다: %s", error)
        return None
