from __future__ import annotations

SUMMARY_PROMPT_TEMPLATE = """당신은 생명과학 논문 다이제스트 에디터다.
아래 논문의 초록을 읽고 반드시 JSON으로만 답변하라.

요구사항:
- 한국어로 작성
- 전문 용어는 영어 병기 (예: 열안정성(thermostability))
- 각 항목은 2문장 이하
- 키: background, method, result, significance, why_it_matters, novelty_note, application_note, caution_note

제목:
{title}

초록:
{abstract}
"""

RELEVANCE_PROMPT_TEMPLATE = """당신은 생명과학 논문 큐레이터다.
아래 논문이 식품/화학/의약 산업에서 활용 가치가 있는지 판단하고 JSON으로만 답변하라.

요구사항:
- 키: relevant(boolean), confidence(0~1 float), category(string), reason(string), topic_tags(array), problem_tags(array), research_type(string), practical_distance(string)
- category는 protein_engineering, metabolic_engineering, bioinformatics, ai_enzyme, other 중 하나
- reason은 한국어 2문장 이하
- topic_tags는 ai_protein_design, enzyme_stability, enzyme_activity, host_engineering, metabolic_pathway, bioprocess_optimization, screening_platform, structural_bioinformatics, other 중 하나 이상
- problem_tags는 stability, yield, selectivity, productivity, cost_reduction, screening_speed, general_insight 중 하나 이상
- research_type은 basic, method, applied 중 하나
- practical_distance는 direct, mid_term, foundational 중 하나

제목:
{title}

초록:
{abstract}
"""


def build_summary_prompt(title: str, abstract: str) -> str:
    return SUMMARY_PROMPT_TEMPLATE.format(title=title.strip(), abstract=abstract.strip())


def build_relevance_prompt(title: str, abstract: str) -> str:
    return RELEVANCE_PROMPT_TEMPLATE.format(title=title.strip(), abstract=abstract.strip())
