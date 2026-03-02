# Plan: 검색 쿼리 정밀화 및 쿼리 파일 분리

## Context
현재 PubMed 검색이 범용 키워드로 되어 있어, 사용자가 의도한 주제(효소/단백질 공학+AI, 대사공학+AI, 조상서열재구성, 발현 최적화, 오믹스+AI 등)와 어긋나는 논문이 대부분임.

사용자가 PubMed에서 실제 사용 중인 5개 불리언 쿼리 조합을 제공함. 이를 기반으로 수집 전략을 재설계. 검색 소스는 PubMed 단일로 변경.

## 핵심 변경

### 1. 쿼리를 `queries.toml`로 분리 관리 (신규 파일)
Python 3.12+ stdlib의 `tomllib`으로 파싱, 추가 의존성 없음.

```toml
# queries.toml
[[queries]]
name = "enzyme/protein engineering + AI"
terms = """("enzyme engineering" OR "protein engineering") AND ("bioinformatics" OR "machine learning" OR "deep learning" OR "artificial intelligence")"""

[[queries]]
name = "metabolic engineering + AI"
terms = """("metabolic engineering") AND ("bioinformatics" OR "machine learning" OR "deep learning" OR "artificial intelligence")"""

[[queries]]
name = "ancestral sequence reconstruction"
terms = '''"ancestral sequence reconstruction"'''

[[queries]]
name = "expression optimization"
terms = """("expression optimization" OR "rbs engineering" OR "promoter engineering")"""

[[queries]]
name = "omics + AI (top journals)"
terms = """("omics" OR "genome" OR "transcriptome" OR "proteome" OR "metabolome" OR "epigenome") AND ("bioinformatics" OR "machine learning" OR "deep learning" OR "artificial intelligence")"""
pubmed_filter = "(Nature[Journal] OR Science[Journal] OR Cell[Journal])"
```

- `terms`: PubMed 불리언 쿼리
- `pubmed_filter`: 추가 필터 (저널 제한 등, 선택사항)
- **로딩 시 검증**: `queries` 배열 최소 1개, 각 항목 `name`+`terms` 필수, 빈 문자열 금지. 실패 시 `ValueError`로 fail-fast.

### 2. PubMed 수집을 다중 쿼리 + 페이징으로 변경
현재 단일 쿼리 `retmax=200` 고정 → 5개 쿼리를 각각 실행하되, `esearch`의 `count` 값으로 페이징.

- 쿼리별: `{terms} AND {pubmed_filter(있으면)} AND ({date_range})`
- `retmax=200` 유지, `count > retmax`이면 `retstart` 루프로 전체 수집
- 기존 3 req/sec throttling 유지
- 쿼리 간 PMID 중복은 dedup 로직이 처리

### 3. bioRxiv 수집 제거
- `src/baiodigest/fetchers/biorxiv.py` 삭제
- `fetchers/__init__.py`에서 biorxiv import 및 호출 제거
- config.py에서 `biorxiv_base_url`, `biorxiv_categories` 제거

### 4. dedup 우선순위 재정의
PubMed 단일 소스에서 다중 쿼리 실행 시, PMID가 가장 신뢰할 수 있는 식별자.

`dedup_key()` 우선순위 변경:
1. `source_id` (PMID) — PubMed 단일 소스이므로 1순위
2. DOI
3. 정규화 title hash (폴백)

### 5. 키워드 필터 단계 간소화
정밀 쿼리가 API 수준에서 키워드 필터링을 대신하므로:
- **기존 include_keywords 기반 2개 매칭 규칙 제거**
- **exclude_keywords(clinical trial, case report 등)는 유지** — 빠른 거부 필터로 여전히 유용
- 파이프라인: 쿼리 기반 수집 → exclude 필터 → LLM 관련성 판정 → 요약

### 6. 통계 키 리네이밍
필터 변경에 맞춰 stats 키 변경:
- `keyword_passed` → `exclude_passed` (의미: exclude 키워드에 걸리지 않고 통과한 수)
- 로그 메시지도 동일하게 변경

## 수정 대상 파일

| 파일 | 변경 내용 |
|------|-----------|
| `queries.toml` (신규) | 5개 쿼리 조합 정의 |
| `src/baiodigest/config.py` | queries.toml 로딩+검증, `include_keywords`/`biorxiv_*`/`pubmed_query` 제거, `SearchQuery` dataclass 추가 |
| `src/baiodigest/fetchers/biorxiv.py` | **삭제** |
| `src/baiodigest/fetchers/pubmed.py` | 다중 쿼리 실행 + count 기반 페이징 |
| `src/baiodigest/fetchers/__init__.py` | biorxiv 참조 제거, `dedup_key()` PMID 우선순위 추가 |
| `src/baiodigest/filters/relevance.py` | `keyword_filter` → exclude-only로 간소화 |
| `src/baiodigest/main.py` | 쿼리 로딩 + 새 fetch 흐름 반영, bioRxiv 참조 제거, stats 키 변경 |
| `tests/test_filters.py` | exclude-only 필터 테스트 |
| `tests/test_fetchers.py` | biorxiv 테스트 제거 |
| `tests/fixtures/biorxiv_sample.json` | **삭제** |

## 신규/변경 테스트

| 테스트 파일 | 시나리오 |
|------------|----------|
| `tests/test_config.py` | queries.toml 정상 로딩, 파일 누락 시 ValueError, 필수 키 누락 시 ValueError, 빈 쿼리 배열 시 ValueError |
| `tests/test_fetchers.py` | 다중 쿼리 ID 병합 (mock esearch), PMID 중복 제거 검증, count 기반 페이징 루프 (mock) |
| `tests/test_filters.py` | exclude 키워드 매칭 시 거부, exclude 미매칭 시 통과 (include 없이), include_keywords 로직 제거 확인 |

## 파이프라인 변경 전후

**Before:**
```
PubMed (단일 범용 쿼리) ──┐
                           ├→ Dedup → 키워드 필터 (2개 매칭) → LLM 판정 → 요약
bioRxiv (카테고리만) ─────┘
```

**After:**
```
PubMed (5개 정밀 쿼리, 페이징) → Dedup (PMID 우선) → Exclude 필터 → LLM 판정 → 요약
```

## 검증
1. `uv run pytest` — 기존 + 신규 테스트 통과
2. `uv run python -m baiodigest.main --date 2026-03-02 --force` — 재실행하여 결과 비교
3. data/2026-03-02.json의 논문 목록이 사용자 의도 주제와 일치하는지 확인
