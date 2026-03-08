# baioDigest

PubMed에서 생명과학 논문을 매일 자동 수집하고, 로컬 LLM으로 한국어 요약을 생성하여 정적 사이트로 배포하는 파이프라인.

## Overview

```
PubMed (5개 정밀 쿼리) → 수집 → 중복제거 → 제외 키워드 필터 → LLM 관련성 판정 → LLM 요약 → HTML 생성 → GitHub Pages
```

**관심 분야**: 단백질 공학, 대사공학, 생물정보학, AI 기반 효소 개량
**산업 초점**: 식품, 화학, 의약 분야의 산업적 활용 가치가 있는 연구

## Tech Stack

- **Python 3.12+** / uv
- **PubMed E-utilities** (queries.toml로 5개 불리언 쿼리 관리)
- **Ollama** + qwen3:8b (로컬 LLM 요약)
- **Jinja2** + Pico CSS (정적 사이트 생성)
- **GitHub Pages** (호스팅)
- **macOS launchd** (일일 스케줄링)

## Quick Start

```bash
# 의존성 설치
uv sync

# Ollama 모델 확인
ollama list  # qwen3:8b 필요

# 전체 파이프라인 실행 (오늘 날짜)
uv run python -m baiodigest.main

# 특정 날짜 다이제스트 알림 메일 발송
uv run python -m baiodigest.notify --date 2026-03-08

# 특정 날짜 실행
uv run python -m baiodigest.main --date 2026-03-01

# 기존 데이터 덮어쓰기
uv run python -m baiodigest.main --force

# 수집만 (LLM 요약 없이)
uv run python -m baiodigest.main --fetch-only

# 기존 데이터로 HTML만 재생성
uv run python -m baiodigest.main --generate-only

# 테스트
uv run pytest
```

## How It Works

1. **수집**: PubMed API에서 다이제스트 생성일 기준 전일(D-1) 논문 메타데이터 수집 (5개 쿼리)
2. **중복제거**: PMID → DOI → title hash 순서로 중복 제거
3. **제외 키워드 필터**: clinical trial, case report 등 임상/역학 논문 제외 (수백편 → ~50편)
4. **LLM 판정**: Qwen3:8b로 산업적 관련성 판정 (~50편 → ~20편)
5. **LLM 요약**: 배경/방법/결과/의미 4섹션 한국어 구조화 요약
6. **사이트 생성**: Jinja2 템플릿으로 정적 HTML 생성 → `docs/`
7. **배포 알림**: 자동 실행 시 GitHub push 성공 뒤 Gmail SMTP로 등록 수신자에게 알림 메일 발송

## Project Structure

```
src/baiodigest/
├── main.py           # CLI 진입점, 파이프라인 오케스트레이터
├── notify.py         # 배포 완료 후 이메일 알림 CLI
├── config.py         # 설정값 집중 관리
├── models.py         # 데이터 모델 (Paper, Summary, DailyDigest)
├── fetchers/         # PubMed E-utilities 클라이언트
├── filters/          # 2단계 필터링 (키워드 → LLM)
├── summarizer/       # Ollama 요약 클라이언트 + 프롬프트
├── notifications/    # Gmail SMTP 알림 발송
└── generator/        # Jinja2 정적 사이트 생성
```

## Email Notifications

자동 알림은 Gmail SMTP 앱 비밀번호를 사용한다.

1. `recipients.toml.example`을 참고해 루트에 `recipients.toml` 생성
2. 실행 환경에 아래 변수 설정

```bash
export BAIODIGEST_SITE_URL="https://<user>.github.io/baiodigest"
export BAIODIGEST_SMTP_USERNAME="your-gmail@gmail.com"
export BAIODIGEST_SMTP_APP_PASSWORD="your-app-password"
```

선택 설정:

```bash
export BAIODIGEST_SMTP_FROM_NAME="baioDigest"
export BAIODIGEST_RECIPIENTS_FILE="/absolute/path/to/recipients.toml"
```

`scripts/run-daily.sh`는 변경 사항이 커밋되고 `git push`가 성공한 경우에만 `uv run python -m baiodigest.notify --date YYYY-MM-DD`를 호출한다.

## License

Private use only.
