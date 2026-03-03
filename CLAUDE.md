# baioDigest - 생명과학 논문 다이제스트 서비스

PubMed에서 생명과학 논문을 매일 수집하고, 로컬 LLM(Ollama + Qwen3:8b)으로 한국어 요약을 생성하여 GitHub Pages에 정적 사이트로 배포하는 자동화 서비스.

## 관심 분야
- **주제**: 단백질 공학, 대사공학, 생물정보학, AI 기반 효소 개량
- **산업**: 식품, 화학, 의약 분야의 산업적 활용 가치가 있는 연구
- **목적**: 최신 기술 트렌드 파악

## 기술 스택

| 영역 | 기술 | 비고 |
|------|------|------|
| 언어 | Python 3.14 | uv로 패키지 관리 |
| 논문 소스 | PubMed E-utilities | queries.toml로 5개 불리언 쿼리 관리 |
| 요약 엔진 | Ollama (localhost:11434) + qwen3:8b | `/no_think` 플래그로 빠른 판정 |
| 사이트 생성 | Jinja2 템플릿 → 정적 HTML | Hugo/Jekyll 대신 단일 스택 |
| 스타일링 | Pico CSS (CDN) | 시맨틱 HTML, 다크모드 자동 |
| 배포 | GitHub Pages (docs/) | 로컬 실행 후 git push |
| 스케줄링 | macOS launchd | 매일 07:00 |

## 프로젝트 구조

```
baiodigest/
├── CLAUDE.md
├── pyproject.toml
├── queries.toml             # PubMed 불리언 쿼리 정의 (5개)
├── src/baiodigest/
│   ├── main.py              # CLI 진입점, 파이프라인 오케스트레이터
│   ├── models.py            # Paper, DailyDigest 데이터 모델
│   ├── config.py            # SearchQuery dataclass, queries.toml 로드
│   ├── fetchers/
│   │   └── pubmed.py        # PubMed E-utilities 클라이언트
│   ├── filters/
│   │   ├── __init__.py      # 중복제거/병합 유틸리티
│   │   └── relevance.py     # 제외 키워드 필터 + LLM 관련성 판정
│   ├── summarizer/
│   │   └── ollama.py        # Ollama 요약 클라이언트
│   └── generator/
│       └── site.py          # Jinja2 정적 사이트 생성
├── templates/               # HTML 템플릿 (base, index, daily, archive)
├── static/                  # CSS, favicon
├── data/                    # 일별 JSON 데이터 (git 추적, 백업 겸용)
├── docs/                    # GitHub Pages 배포 루트
└── tests/
```

## 데이터 파이프라인

```
PubMed (5개 정밀 쿼리) → 수집 → 중복제거(PMID → DOI → title hash) → 제외 키워드 필터 → LLM 관련성 판정 → LLM 요약 → HTML 생성 → git push
```

### 필터링 (2단계)
- **0단계 (API 수준)**: queries.toml의 불리언 쿼리가 PubMed API esearch 시점에 범위를 한정 — 관련 없는 논문 대부분 제거
1. **제외 키워드 필터 (exclude-only)** (비용 0): clinical trial, case report 등 임상/역학 논문 제목+초록 매칭으로 제외, 수백편 → 50편 이하
2. **LLM 관련성 판정** (Qwen3): JSON 응답으로 relevant/confidence/category 반환, → 20편 이하

### 요약
- Qwen3:8b로 한국어 요약 
- 요약은 배경, 방법, 결과, 의미로 구분하여 각 항목별 2문장 이하로 할 것
- 전문 용어는 영어 병기: 열안정성(thermostability)
- 논문당 타임아웃 120초, 실패 시 초록 앞 3문장 폴백

## HTML 구성
- 저널명 + **[Preprint]** 또는 **[Published]** 라벨(subtitle)
- 논문제목(title) - 원문링크 연결
- 저자 리스트 중 마지막 교신저자 소속기관(subtitle) — 없으면 제1저자 소속, 소속 정보 자체가 없으면 생략
- 배경(본문)
- 방법(본문)
- 결과(본문)
- 의미(본문)
- 매칭된 검색 쿼리 이름 리스트(각주)
- LLM 관련성 판정 근거(각주)

## CLI 명령어

```bash
uv sync                                          # 의존성 설치
uv run python -m baiodigest.main                 # 전체 파이프라인
uv run python -m baiodigest.main --fetch-only    # 수집만
uv run python -m baiodigest.main --generate-only # HTML 생성만
uv run python -m baiodigest.main --date 2026-03-01  # 특정 날짜
uv run python -m baiodigest.main --force         # 기존 데이터 덮어쓰기
uv run pytest                                    # 테스트
```

## 코딩 컨벤션
- Type hints 필수, dataclass 기반 모델
- 외부 API 호출에 재시도 로직 (tenacity)
- 개별 논문 처리 실패는 로깅 후 스킵 (파이프라인 전체가 죽지 않도록)
- Ollama 프롬프트는 별도 상수로 분리하여 튜닝 용이하게
- 멱등성 보장: 같은 날짜 재실행 시 기존 데이터 스킵

## API 참고

**PubMed E-utilities**
- esearch → efetch 패턴, `retmode=xml`
- API 키 없이 3 req/sec, 키 등록 시 10 req/sec
- https://www.ncbi.nlm.nih.gov/books/NBK25497/

**Ollama**
- `POST http://localhost:11434/api/generate`
- 모델: qwen3:8b, `/no_think` 플래그로 thinking 비활성화

## queries.toml — 검색 쿼리 관리

TOML 포맷으로 PubMed 불리언 쿼리를 정의한다. `config.py`의 `_load_pubmed_queries()`가 로드 시 유효성을 검증한다.

```toml
[[queries]]
name = "protein_engineering"          # 쿼리 이름 (HTML 각주에 표시)
terms = "(protein engineering[MeSH] OR directed evolution[Title/Abstract]) AND enzyme[Title/Abstract]"
pubmed_filter = "journal article[pt]" # 추가 PubMed 필터 (선택)
```

- `name`: 필수. 영문 snake_case. HTML 각주의 "매칭된 검색 쿼리 이름"으로 표시.
- `terms`: 필수. PubMed 불리언 쿼리 문자열.
- `pubmed_filter`: 선택. 발표 유형 등 추가 필터.
- `config.py`의 `SearchQuery` dataclass로 파싱되며, `name`/`terms` 누락 시 `ValueError` 발생.

## 수집 날짜 로직

`main.py`의 `_pubmed_query_date(digest_date)`는 `digest_date - 1일`을 반환한다.
즉, 다이제스트 생성일(D) 기준 전일(D-1)의 PubMed 출판일 논문을 검색한다.
예: 2026-03-03에 실행 → 2026-03-02 출판 논문 수집.

## 배포
- GitHub Pages: Settings > Pages > Source: Deploy from branch > /docs
- macOS launchd (~/Library/LaunchAgents/com.baiodigest.daily.plist)로 매일 05:00 실행
- 시작 시 마지막 수집 날짜 확인, 누락 날짜 소급 수집 (최대 5일)

## 향후 개선
- RSS/Atom 피드 생성 (Feedly/Inoreader 구독용)
- 주간 하이라이트 Top 5 자동 생성
- lunr.js 기반 클라이언트 사이드 검색
- 임베딩 기반 유사도 필터링 (키워드 한계 보완)
