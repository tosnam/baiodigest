# Plan: BioDigest 단계별 개발 계획

## Context
CLAUDE.md에 기술 스택, 구조, 파이프라인이 정의된 상태. 빈 디렉토리에서 시작하여 데이터 흐름 순서(수집→필터링→요약→생성→배포)에 따라 단계별로 구현한다. 각 단계는 독립적으로 검증 가능해야 한다.

---

## Phase 1: 프로젝트 초기화
**목표**: uv 프로젝트 셋업, 디렉토리 구조, 의존성 정의

- `uv init --lib` 실행, `pyproject.toml` 구성
- 의존성: `httpx`, `jinja2`, `tenacity`, `pydantic` (또는 dataclass)
- dev 의존성: `pytest`, `pytest-asyncio`
- `src/baiodigest/` 하위 패키지 디렉토리 생성 (fetchers, filters, summarizer, generator)
- `templates/`, `static/`, `data/`, `docs/`, `tests/`, `tests/fixtures/` 디렉토리 생성
- `.gitignore` 작성
- `src/baiodigest/config.py` 생성 — 모든 설정값을 한 곳에 집중
  - Ollama 엔드포인트, 모델명, 타임아웃
  - confidence 임계값 (기본 0.6)
  - 키워드 목록 (INCLUDE_KEYWORDS, EXCLUDE_KEYWORDS)
  - bioRxiv 대상 카테고리 목록
  - PubMed 검색 쿼리 기본값

**검증**: `uv sync` 성공, `uv run python -c "import baiodigest"` 정상

---

## Phase 2: 데이터 모델
**목표**: 파이프라인 전체에서 사용할 데이터 구조 정의

- `src/baiodigest/models.py`
  - `Paper`: title, abstract, authors, affiliations, doi, source (pubmed/biorxiv), source_type (preprint/published), journal, url, category, date, mesh_terms
  - `FilterResult`: relevant, confidence, category, reason, matched_keywords
  - `Summary`: background, method, result, significance (각 항목 2문장 이하)
  - `DigestEntry`: Paper + FilterResult + Summary
  - `DailyDigest`: date, entries list, stats (수집/필터/최종 건수), schema_version
- JSON 직렬화/역직렬화 메서드 (data/ 저장용)

**검증**: `uv run pytest tests/test_models.py` — 모델 생성, JSON round-trip 테스트

---

## Phase 3: 논문 수집기 (Fetchers)
**목표**: PubMed, bioRxiv에서 논문 메타데이터 수집

### 3-1. bioRxiv 클라이언트
- `src/baiodigest/fetchers/biorxiv.py`
- `GET https://api.biorxiv.org/details/biorxiv/{start}/{end}/{cursor}`
- cursor 페이지네이션, category 필드로 관련 분야 1차 필터
- 대상 카테고리: molecular biology, biochemistry, bioinformatics, synthetic biology, bioengineering, systems biology
- httpx + tenacity 재시도
- → `list[Paper]` 반환 (source_type="preprint")

**검증**: 실제 bioRxiv API 호출, 어제 날짜 기준 논문 수집 확인 + `tests/fixtures/biorxiv_sample.json`으로 파서 단위 테스트

### 3-2. PubMed 클라이언트
- `src/baiodigest/fetchers/pubmed.py`
- esearch (검색어+날짜범위) → efetch (상세정보) 패턴
- XML 파싱으로 title, abstract, authors, affiliations, DOI, MeSH Terms 추출
- 검색 쿼리: 단백질 공학, 대사공학, 생물정보학, AI+효소 관련 MeSH/키워드 조합
- rate limit 준수 (3 req/sec)
- → `list[Paper]` 반환 (source_type="published")

**검증**: 실제 PubMed API 호출, 어제 날짜 기준 논문 수집 확인 + `tests/fixtures/pubmed_sample.xml`으로 파서 단위 테스트

### 3-3. 중복제거
- `src/baiodigest/fetchers/__init__.py`에 merge 함수
- DOI 기반 1차 중복제거 + title 정규화 해시 보조키

**검증**: 동일 DOI / 유사 제목 논문이 1건으로 병합되는지 테스트

---

## Phase 4: 필터링
**목표**: 2단계 필터링으로 관련 논문 선별

### 4-1. 키워드 규칙 필터
- `src/baiodigest/filters/relevance.py`
- INCLUDE_KEYWORDS, EXCLUDE_KEYWORDS 상수 정의
- 제목+초록에서 매칭, 포함 2개 이상 시 통과
- 매칭된 키워드 리스트를 FilterResult.matched_keywords에 저장

**검증**: 키워드 포함/미포함 논문 샘플로 필터 정확도 확인

### 4-2. LLM 관련성 판정
- `src/baiodigest/filters/relevance.py`에 추가
- Ollama API 호출 (Phase 5의 ollama.py 클라이언트 재사용)
- 프롬프트: 산업적 활용 가치 판정, JSON 응답 (relevant/confidence/category/reason)
- `/no_think` 플래그, confidence 0.6 미만 제외
- **JSON 폴백 체인**: 파싱 실패 → 재시도 1회 → 재실패 시 `relevant=True`(fail-open)으로 처리하여 관련 논문 누락 방지
- → FilterResult 반환

**검증**: 키워드 통과 논문 5편으로 LLM 판정 실행, JSON 파싱 정상 확인 / 의도적으로 깨진 JSON 응답 mock으로 폴백 체인 동작 확인

---

## Phase 5: Ollama 요약 클라이언트
**목표**: 논문 초록을 구조화된 한국어 요약으로 변환

- `src/baiodigest/summarizer/ollama.py`
- `POST http://localhost:11434/api/generate` (model: qwen3:8b)
- 요약 프롬프트: 배경/방법/결과/의미 4섹션, 각 2문장 이하, 영어 병기
- 관련성 판정 프롬프트: JSON 응답 요청 (Phase 4에서 호출)
- 프롬프트 상수는 `src/baiodigest/summarizer/prompts.py`에 분리
- 타임아웃 120초, 실패 시 초록 앞 3문장 폴백
- Ollama 미실행 시 연결 에러 로깅

**검증**: 논문 1편으로 요약 생성, 4섹션 구조 확인, 한국어+영어 병기 확인

---

## Phase 6: 정적 사이트 생성
**목표**: Jinja2 템플릿으로 HTML 페이지 생성

### 6-1. 템플릿 작성
- `templates/base.html`: Pico CSS CDN, 공통 레이아웃
- `templates/index.html`: 최신 다이제스트 표시 (또는 최신 날짜로 리다이렉트)
- `templates/daily.html`: 일별 다이제스트 — 카테고리별 그룹핑, 논문 카드
- `templates/archive.html`: 날짜별 아카이브 목록

### 6-2. 사이트 생성기
- `src/baiodigest/generator/site.py`
- data/*.json 읽기 → Jinja2 렌더링 → docs/에 HTML 출력
- 논문 카드 HTML 구성: 저널명+[Preprint/Published], 제목(원문링크), 교신저자 소속(fallback 포함), 배경/방법/결과/의미, 키워드, 판정 근거
- `static/` → `docs/`에 복사

**검증**: data/에 샘플 JSON 넣고 `--generate-only` 실행, 브라우저에서 docs/index.html 확인

---

## Phase 7: 파이프라인 오케스트레이터
**목표**: CLI 진입점으로 전체 파이프라인 통합

- `src/baiodigest/main.py`
- argparse: `--fetch-only`, `--generate-only`, `--date YYYY-MM-DD`
- 기본 실행: 수집 → 중복제거 → 키워드 필터 → LLM 판정 → LLM 요약 → JSON 저장 → HTML 생성
- 멱등성: data/{date}.json 존재 시 스킵 (--force로 재실행 가능)
- 누락 날짜 소급: 마지막 수집일 ~ 오늘, 최대 5일
- 개별 논문 실패 시 로깅 후 스킵
- 실행 결과 요약 출력 (수집 N편, 필터 통과 N편, 요약 완료 N편)

**검증**: `uv run python -m baiodigest.main --date 2026-03-01` 실행, data/에 JSON 생성, docs/에 HTML 생성, 브라우저 확인

---

## Phase 8: 배포 및 자동화
**목표**: GitHub Pages 배포, launchd 스케줄링

- git init, GitHub 리포 생성, 첫 커밋/푸시
- GitHub Pages 설정 (Settings > Pages > /docs)
- `~/Library/LaunchAgents/com.baiodigest.daily.plist` 작성
  - 매일 05:00, 파이프라인 실행 + git add/commit/push
  - 로그: logs/daily.log, logs/daily-error.log
- `launchctl load` 등록

**검증**: GitHub Pages URL에서 사이트 접속 확인, launchd 수동 트리거로 자동화 동작 확인
