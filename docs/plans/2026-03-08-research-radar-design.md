# Research Radar Design

**Date:** 2026-03-08

## Goal

제한된 관심 키워드로 수집한 바이오 논문을 산업 R&D 실무자가 더 빨리 탐색하고 해석할 수 있도록, 서비스의 중심을 `요약 나열`에서 `탐색 가능한 연구 레이더`로 전환한다.

## Context

- 현재 서비스는 PubMed 수집, LLM 관련성 판정, 한국어 구조화 요약, 정적 웹/이메일 배포까지 완료되어 있다.
- 데이터 소스는 사용자의 제한된 관심 키워드에 묶여 있으므로, 일반 뉴스 서비스처럼 매일 풍부한 트렌드를 기대하기 어렵다.
- 따라서 억지로 `오늘의 트렌드`를 고정 노출하면 반복적이거나 정보량이 낮은 신호를 매일 새것처럼 보이게 만들 위험이 있다.
- 사용자의 핵심 목적은 두 가지다.
  - 최신 기술과 주제 흐름을 파악하기
  - 그중 읽을 만한 논문을 빠르게 고르기

## Chosen Direction

일간과 주간의 역할을 분리한다.

- `일간 다이제스트`는 `오늘 읽을 논문을 고르는 화면`이다.
- `주간 트렌드 요약`은 `최근 흐름과 변화 신호를 해석하는 화면`이다.
- 모든 논문은 유지한다.
- 실무 활용도가 낮아 보이는 기초연구나 방법론 논문도 숨기지 않는다.
- 대신 각 논문이 어떤 성격의 기여를 하는지 구조화해서 보여준다.

## Product Structure

### Daily Digest

일간 페이지는 그날 수집된 논문을 빠르게 선별하기 위한 탐색 인터페이스를 제공한다.

- 상단 요약
  - 총 논문 수
  - 기술 주제 분포
  - 문제 유형 분포
  - 연구 성격 분포
- 논문 카드
  - 제목
  - `why_it_matters`: 왜 읽을 만한가
  - 기술 주제 태그
  - 문제 유형 태그
  - 연구 성격
  - 실무 근접도
  - 기존 4섹션 요약
  - 이해 보조 3문장
- 탐색 도구
  - 기술 주제별 묶음
  - 문제 유형별 묶음
  - 연구 성격별 필터
  - 실무 근접도별 필터

### Weekly Trend Summary

주간 페이지는 `항상 트렌드가 있다`고 가정하지 않는다. 변화가 감지될 때만 강조한다.

- 이번 주 새로 강해진 기술 주제
- 반복 등장한 문제 유형
- 새롭게 등장한 접근 방식이나 방법론
- 각 신호를 대표하는 논문 묶음
- 뚜렷한 변화가 없을 때는 정직한 상태 메시지 제공
  - 예: `이번 주는 기존 핵심 주제의 연속선상 연구가 중심`

## Information Principles

- `숨김`보다 `구분`이 우선이다.
- `일간`은 선별을 돕고, `주간`은 해석을 돕는다.
- 트렌드는 장식이 아니라 조건부 신호다.
- 탐색을 위해서는 더 많은 텍스트보다 더 좋은 구조가 중요하다.

## Structured Fields

현재 `FilterResult`와 `Summary`만으로는 탐색 기능을 만들기 어렵다. 각 논문에 아래 구조화 필드를 추가한다.

- `topic_tags`
  - 예: `ai_protein_design`, `enzyme_stability`, `host_engineering`, `metabolic_pathway`
- `problem_tags`
  - 예: `stability`, `yield`, `selectivity`, `productivity`, `cost_reduction`
- `research_type`
  - `basic`, `method`, `applied`
- `practical_distance`
  - `direct`, `mid_term`, `foundational`
- `why_it_matters`
  - 이 논문을 왜 봐야 하는지 1문장
- `novelty_note`
  - 무엇이 새로운가
- `application_note`
  - 어디에 적용 가능한가
- `caution_note`
  - 해석 시 주의할 점은 무엇인가

## Taxonomy v1

초기 taxonomy는 작은 고정 집합으로 시작한다.

### Topic Tags

- `ai_protein_design`
- `enzyme_stability`
- `enzyme_activity`
- `host_engineering`
- `metabolic_pathway`
- `bioprocess_optimization`
- `screening_platform`
- `structural_bioinformatics`
- `other`

### Problem Tags

- `stability`
- `yield`
- `selectivity`
- `productivity`
- `cost_reduction`
- `screening_speed`
- `general_insight`

## Generation Model

### Daily Generation

- 파이프라인은 기존처럼 하루 단위 JSON을 생성한다.
- 단, 각 `DigestEntry`는 탐색용 구조화 필드를 함께 가진다.
- 사이트 생성기는 일간 페이지에서
  - 태그별 집계
  - 주제별 그룹
  - 필터 UI용 데이터
  - 구조화 카드 레이아웃
  를 렌더링한다.

### Weekly Generation

- 사이트 생성 시 기존 일간 JSON을 집계해 최근 7일 단위 주간 컨텍스트를 계산한다.
- 변화 감지는 복잡한 모델 대신 단순 빈도 비교로 시작한다.
  - 이번 주 주제 빈도
  - 최근 2~4주 기준선 빈도
  - 새로 등장했는지 여부
- 주간 페이지는 `/weekly/YYYY-WW.html` 형태의 정적 페이지로 생성한다.
- 홈은 최신 일간 다이제스트와 최신 주간 요약으로 진입점을 분리해 보여준다.

## Rendering Scope

- `index.html`
  - 최신 일간 다이제스트
  - 최신 주간 요약 링크 또는 요약 카드
- `daily/<date>.html`
  - 탐색형 카드/그룹/필터
- `weekly/<year-week>.html`
  - 변화 감지형 주간 요약
- `archive.html`
  - 월별 아카이브 구조는 유지
  - 필요 시 주간 진입 링크는 별도 섹션으로만 추가

## Error Handling

- LLM이 새 구조화 필드를 일부 누락해도 기존 일간 다이제스트 생성은 계속되어야 한다.
- 태그 분류 실패 시 `other` 또는 보수적인 기본값으로 대체한다.
- 주간 신호가 충분하지 않으면 빈 트렌드 차트를 만들지 않고 설명형 상태 메시지를 렌더링한다.
- 기존 JSON과의 호환성을 유지해 과거 다이제스트도 읽히게 해야 한다.

## MVP Scope

- 모델에 탐색용 필드 추가
- LLM 프롬프트와 파서 확장
- 일간 페이지에 태그/한 줄 판단/이해 보조 문장 추가
- 기술 주제와 문제 유형 중심의 그룹/필터 렌더링
- 주간 요약 페이지 1종 추가
- 단순 빈도 비교 기반 변화 감지

## Out of Scope

- 계정 기능
- 개인별 관심 목록 저장
- 팀 협업 기능
- 복잡한 추천 모델
- 강한 의미를 부여하는 정밀 점수화
- 변화가 없는데도 매일 강제로 만드는 트렌드 카드

## Success Criteria

- 산업 R&D 실무자가 일간 페이지에서 `왜 읽을지`를 더 빨리 판단할 수 있다.
- 기초연구/방법론/응용연구가 섞여 있어도 각 논문의 성격이 명확히 드러난다.
- 주간 페이지는 억지 인사이트 없이 실제 변화 신호만 요약한다.
- 기존 정적 사이트 배포 방식과 자동 파이프라인은 유지된다.
