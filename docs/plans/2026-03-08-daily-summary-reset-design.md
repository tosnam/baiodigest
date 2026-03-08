# Daily Summary Reset Design

**Date:** 2026-03-08

## Goal

`research-radar` 변경을 모두 폐기하고, 기존 일간 논문 요약 페이지를 복원한 뒤 논문 카드 안에 읽기 중심의 추가 섹션만 세로 흐름으로 붙인다.

## Context

- 연구 레이더 변경은 일간/주간 탐색 구조, 태그 메타데이터, 주간 페이지, 추가 산출물까지 넓게 퍼져 있다.
- 이번 요구는 그 방향 전체를 유지하는 것이 아니라, 기존 다이제스트 경험으로 되돌린 뒤 논문 상세 카드의 본문 구성만 조금 확장하는 것이다.
- 사용자는 카드형 메타 UI, 주제 그룹, 주간 신호를 원하지 않는다.
- 대신 논문을 읽을 때 `왜 읽을 만한가`, `활용`, `주의`를 기존 요약 블록과 같은 읽기 톤으로 더 보고 싶어 한다.

## Chosen Direction

기준 상태는 `2ea19dc` 머지 이전의 `main`, 즉 `8a368bd` 시점으로 잡는다.

- `research-radar` 구현으로 추가된 모델/생성기/주간 페이지/스타일/산출물은 모두 복원한다.
- 복원 후에는 `daily.html` 중심의 최소 변경만 다시 적용한다.
- 새로운 추가 섹션은 요약 카드 안에서 세로 순서로 이어지는 본문 블록으로만 렌더링한다.

## Restore Scope

### Restore to Pre-Radar State

- `src/baiodigest/models.py`
- `src/baiodigest/filters/relevance.py`
- `src/baiodigest/summarizer/ollama.py`
- `src/baiodigest/summarizer/prompts.py`
- `src/baiodigest/generator/site.py`
- `templates/index.html`
- `templates/daily.html`
- `static/style.css`
- `tests/test_models.py`
- `tests/test_filters.py`
- `tests/test_main.py`
- `tests/test_site_generation.py`
- `docs/index.html`
- `docs/daily/*`
- `docs/static/style.css`
- `docs/weekly/*`

### Keep As-Is

- 기존 아카이브 캘린더 기능
- 기존 이메일 알림 기능
- 설계/계획 문서
- 기타 unrelated 변경

## Daily Card Structure After Restore

논문 카드는 아래 순서로 블록을 렌더링한다.

1. `왜 읽을 만한가`
2. `배경`
3. `방법`
4. `결과`
5. `의미`
6. `활용`
7. `주의`

핵심 원칙:

- `왜 읽을 만한가`는 별도 생성 문장이 아니라 기존 `filter_result.reason`을 본문 블록으로 승격해 사용한다.
- `무엇이 새롭나`는 제거한다. 현재 의미와 중복되기 때문이다.
- `활용`은 `summary.application_note`를 사용한다.
- `주의`는 `summary.caution_note`를 사용한다.
- `활용` 또는 `주의`가 비어 있으면 빈 문자열 대신 짧은 기본 문장을 사용해 레이아웃 붕괴를 피한다.

## Notes Footer Simplification

논문 카드 하단 notes는 축소한다.

- 유지
  - `키워드`
  - `confidence`
- 제거
  - `판정 근거`

이유는 `판정 근거` 문장이 이제 `왜 읽을 만한가` 섹션에 이미 올라오기 때문이다.

## Data Model Decision

연구 레이더용 구조화 메타데이터는 제거한다.

- `topic_tags`
- `problem_tags`
- `research_type`
- `practical_distance`

다만 `application_note`와 `caution_note`는 이번 페이지 구성에 필요하므로 `Summary`에는 유지한다.
`why_it_matters`와 `novelty_note`는 제거한다.

즉 최종 모델은 아래처럼 단순화된다.

- `FilterResult`
  - `relevant`, `confidence`, `category`, `reason`, `matched_keywords`
- `Summary`
  - `background`, `method`, `result`, `significance`, `application_note`, `caution_note`

## Rendering Model

- 홈은 기존 최신 다이제스트 + 최근 기록 구조로 되돌린다.
- 주간 페이지 생성은 제거한다.
- 일간 페이지는 기존 `paper-card`와 `summary-block` 스타일을 재사용한다.
- 추가 섹션도 같은 계열 스타일의 세로 블록으로 렌더링한다.

## Testing Strategy

다음 시나리오를 자동 테스트로 고정한다.

- 연구 레이더용 홈/주간 출력이 더 이상 생성되지 않는지
- 일간 페이지가 새 순서의 세로 블록을 렌더링하는지
- `왜 읽을 만한가`가 `filter_result.reason`을 사용하고 footer에는 reason이 남지 않는지
- `활용`, `주의`가 `Summary` 필드로 렌더링되는지
- 과거 JSON처럼 `application_note`, `caution_note`가 없어도 기본 문장으로 렌더링되는지

## Success Criteria

- `research-radar` 관련 페이지 구조와 데이터 모델이 제거된다.
- 일간 페이지는 다시 단순한 읽기 흐름으로 돌아간다.
- 논문 카드에 `왜 읽을 만한가`, `활용`, `주의`가 추가되지만 시각 구조는 기존 요약 카드와 일관된다.
- footer에는 `confidence`만 남고 reason 중복 노출이 없다.
