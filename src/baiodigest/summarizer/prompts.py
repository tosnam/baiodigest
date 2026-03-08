from __future__ import annotations

SUMMARY_PROMPT_TEMPLATE = """당신은 생명과학 논문 다이제스트 에디터다.
아래 논문의 초록을 읽고 반드시 JSON으로만 답변하라.

요구사항:
- 한국어로 작성
- 전문 용어는 영어 병기 (예: 열안정성(thermostability))
- 각 항목은 2문장 이하
- 키: background, method, result, significance

제목:
{title}

초록:
{abstract}
"""

RELEVANCE_PROMPT_TEMPLATE = """당신은 생명과학 논문 큐레이터다.
아래 논문이 식품/화학/의약 산업에서 활용 가치가 있는지 판단하고 JSON으로만 답변하라.

요구사항:
- 키: relevant(boolean), confidence(0~1 float), category(string), reason(string)
- category는 protein_engineering, metabolic_engineering, bioinformatics, ai_enzyme, other 중 하나
- reason은 한국어 2문장 이하

제목:
{title}

초록:
{abstract}
"""

NEWSLETTER_PROMPT_TEMPLATE = """You are editing a science newsletter digest.
Read the newsletter issue below and respond with JSON only.

Requirements:
- Write in Korean
- Cover every main article detected in the newsletter
- Do not omit any primary story, even when multiple sections exist
- Preserve section context when possible
- Write 1-2 sentences per article briefing
- Keys: overview(string), covered_item_titles(array of strings), article_briefings(array of objects)
- `covered_item_titles` must list every main article title you actually covered
- `article_briefings` must include one object per main article
- Each article briefing object must contain: title(string), url(string), briefing_ko(string)

Newsletter:
{newsletter_name}

Issue title:
{title}

Detected main articles:
{item_lines}

Issue body:
{body}
"""


def build_summary_prompt(title: str, abstract: str) -> str:
    return SUMMARY_PROMPT_TEMPLATE.format(title=title.strip(), abstract=abstract.strip())


def build_relevance_prompt(title: str, abstract: str) -> str:
    return RELEVANCE_PROMPT_TEMPLATE.format(title=title.strip(), abstract=abstract.strip())


def build_newsletter_summary_prompt(newsletter_name: str, title: str, item_lines: str, body: str) -> str:
    return NEWSLETTER_PROMPT_TEMPLATE.format(
        newsletter_name=newsletter_name.strip(),
        title=title.strip(),
        item_lines=item_lines.strip(),
        body=body.strip(),
    )
