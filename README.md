# baioDigest

PubMed에서 생명과학 논문을 매일 수집하고, 로컬 LLM으로 한국어 요약을 만든 뒤 정적 웹페이지와 알림 메일로 배포하는 파이프라인입니다.

## Overview

```text
PubMed (queries.toml) -> 수집 -> 중복 제거 -> 제외 키워드 필터 -> LLM 관련성 판정 -> LLM 요약 -> 정적 HTML 생성 -> GitHub Pages
```

- 관심 분야: 단백질 공학, 대사공학, 생물정보학, AI 기반 효소 개량
- 산업 초점: 식품, 화학, 의약 분야에서 참고 가치가 있는 연구

## Tech Stack

- Python 3.12+ / `uv`
- PubMed E-utilities
- Ollama + `qwen3:8b`
- Jinja2 + custom CSS
- GitHub Pages (`docs/`)
- Gmail SMTP notification
- `scripts/run-daily.sh` + macOS `launchd` for local automation

## Quick Start

```bash
# 의존성 설치
uv sync

# Ollama 모델 확인
ollama list  # qwen3:8b 필요

# 전체 파이프라인 실행 (오늘 날짜)
uv run python -m baiodigest.main

# 특정 날짜 실행
uv run python -m baiodigest.main --date 2026-03-01

# 기존 데이터 덮어쓰기
uv run python -m baiodigest.main --force

# 수집만 (LLM 요약 없이)
uv run python -m baiodigest.main --fetch-only

# 기존 데이터로 HTML만 재생성
uv run python -m baiodigest.main --generate-only

# 특정 날짜 다이제스트 알림 메일 발송
uv run python -m baiodigest.notify --date 2026-03-08

# 테스트
uv run pytest
```

## What The Site Shows

- 홈: `Today's Digest`와 최근 다이제스트 목록
- 일간 페이지: 논문별 `왜 읽을 만한가`, `배경`, `방법`, `결과`, `활용`
- 아카이브: 월별 캘린더와 일자별 목록

정적 결과물은 `docs/`에 생성되며, 로컬 확인용 출력은 `BAIODIGEST_DOCS_DIR=preview`로 따로 만들 수 있습니다.

## How It Works

1. 수집: 다이제스트 날짜 기준 전일(D-1) PubMed 논문을 `queries.toml` 기반으로 가져옵니다.
2. 중복 제거: PMID -> DOI -> title hash 순서로 중복을 정리합니다.
3. 제외 키워드 필터: clinical trial, case report 등 임상/역학 논문을 먼저 걸러냅니다.
4. LLM 판정: Ollama 모델이 산업적 관련성을 판정하고 confidence와 판정 근거를 남깁니다.
5. LLM 요약: `background`, `method`, `result`, `significance` 4개 필드를 생성합니다.
6. 사이트 생성: Jinja2 템플릿으로 홈, 일간, 아카이브 페이지를 `docs/`에 생성합니다.
7. 알림 발송: push 성공 후 등록된 수신자에게 Gmail SMTP로 다이제스트 메일을 보냅니다.

## Project Structure

```text
src/baiodigest/
├── main.py           # CLI 진입점, 파이프라인 오케스트레이터
├── notify.py         # 배포 완료 후 이메일 알림 CLI
├── config.py         # 설정값, queries/recipients 로드
├── models.py         # 데이터 모델 (Paper, Summary, DailyDigest)
├── fetchers/         # PubMed E-utilities 클라이언트
├── filters/          # 제외 키워드 + LLM 관련성 판정
├── summarizer/       # Ollama 요약 클라이언트 + 프롬프트
├── notifications/    # Gmail SMTP 알림 발송
└── generator/        # 정적 사이트 생성

scripts/
└── run-daily.sh      # 파이프라인 실행, 커밋/푸시, 알림 발송
```

## Email Notifications

자동 알림은 Gmail SMTP 앱 비밀번호를 사용합니다.

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

`scripts/run-daily.sh`는 변경 사항이 커밋되고 `git push`가 성공한 경우에만 `uv run python -m baiodigest.notify --date YYYY-MM-DD`를 호출합니다.

## License

Private use only.
