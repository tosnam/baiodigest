# PLAN_01.md 전문가 검토 피드백

## 총평
- 방향성(사용자 실사용 쿼리 반영, PubMed 중심 수집)은 타당합니다.
- 다만 현재 문서는 **실행 결정에 필요한 세부 사양(쿼리 로더 검증, 다중 쿼리 페이징, dedup 키 전략, 통계/테스트 갱신)**이 부족해 그대로 구현하면 누락/회귀 가능성이 높습니다.

## 주요 리스크 (심각도 순)

1. **Critical - PubMed 결과 누락 가능성(페이징 미정의)**
   - 계획은 다중 쿼리 실행만 정의되어 있고 `esearch` 페이징(`retstart`) 전략이 없습니다.
   - 현재 코드도 `retmax=200` 고정이라, 쿼리별 결과가 200건을 넘으면 누락됩니다.
   - 참고: `tasks/PLAN_01.md` 40-45행, `src/baiodigest/fetchers/pubmed.py` 186-193행

2. **High - `queries.toml` 로딩 실패 시 동작 정책 부재**
   - 파일 누락/파싱 오류/빈 쿼리/필수 키 누락 시 fail-fast 여부가 정해지지 않았습니다.
   - 운영 시 launchd에서 조용히 빈 결과를 만들 가능성이 있어 위험합니다.
   - 참고: `tasks/PLAN_01.md` 10-12, 62행

3. **High - 다중 쿼리 dedup 기준이 불충분**
   - 계획은 “기존 dedup 재사용”인데 현재 dedup는 DOI+제목 해시 중심입니다.
   - PubMed 다중 쿼리에서는 PMID(`source_id`) 기준 dedup를 1순위로 두는 것이 안전합니다.
   - 참고: `tasks/PLAN_01.md` 44행, `src/baiodigest/fetchers/__init__.py`

4. **High - 필터 변경 후 통계/의미 불일치 가능성**
   - 기존 파이프라인은 `keyword_passed` 통계를 사용합니다.
   - include 제거 후에도 키 이름/의미를 그대로 두면 모니터링 지표가 왜곡됩니다.
   - 참고: `tasks/PLAN_01.md` 51-56행, `src/baiodigest/main.py` 121-124행

5. **Medium - 쿼리별 기여도 추적 누락**
   - 다중 쿼리로 바꾸면 어떤 쿼리가 어떤 논문을 수집했는지 기록이 필요합니다.
   - 없으면 품질 튜닝(불필요 쿼리 제거/개선)이 어려워집니다.
   - 참고: `tasks/PLAN_01.md` 40-45행

6. **Medium - 회귀 테스트 범위가 축소 중심(삭제 위주)**
   - biorxiv 테스트 제거는 맞지만, 대체로 필요한 신규 테스트(쿼리 로더/컴파일/다중 쿼리 병합/페이징)가 명시되지 않았습니다.
   - 참고: `tasks/PLAN_01.md` 68-70, 86-89행

## 보완 권장사항

1. **쿼리 스키마 명시 및 검증 추가**
   - `SearchQuery` 필드: `name(str)`, `terms(str)`, `pubmed_filter(str|None)`.
   - 로딩 시 검증 규칙:
     - `queries` 배열 최소 1개
     - 각 항목 `name`, `terms` 필수
     - 공백/빈 문자열 금지
   - 오류 시 `ValueError`로 즉시 실패(fail-fast) + 명확한 로그.

2. **PubMed 다중 쿼리 + 페이징 사양 확정**
   - 쿼리별 `esearch`를 `retstart` 루프로 끝까지 수집.
   - `retmax`는 200 유지 가능하나 `count` 기반 반복 필수.
   - API 호출량 증가를 고려해 현재 3 req/sec throttling 유지.

3. **dedup 우선순위 재정의**
   - 1순위: `source=pubmed` + `source_id(PMID)`
   - 2순위: DOI
   - 3순위: 정규화 title hash

4. **필터/통계 네이밍 정리**
   - `keyword_passed` → `exclude_passed` 또는 `prefilter_passed`로 변경.
   - 기존 UI의 “키워드” 노출은 비어질 수 있으므로 문구 정합성 점검 필요.

5. **품질 관측성 추가**
   - 일별 stats에 `query_hit_counts`(쿼리별 hit 수), `unique_after_dedup` 저장 권장.

## 테스트 보강 (필수)

1. `tests/test_config.py`
   - `queries.toml` 정상/누락/파싱오류/필수키 누락 케이스

2. `tests/test_pubmed.py`
   - 다중 쿼리 ID 병합 + 페이징 루프 테스트(mock)

3. `tests/test_fetchers.py`
   - PMID 중복이 쿼리 간 병합되는지 검증

4. `tests/test_filters.py`
   - include 제거 후 exclude만으로 차단되는지 검증

## 최종 의견
- 본 계획은 방향은 맞지만, 현재 상태로는 구현 상세가 부족합니다.
- 특히 **페이징, 쿼리 로더 검증, PMID dedup, 통계 필드 재정의** 4가지는 구현 전에 계획에 명시적으로 추가하는 것을 권장합니다.
