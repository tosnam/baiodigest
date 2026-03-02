# baioDigest

PubMed/bioRxiv에서 생명과학 논문을 매일 자동 수집하고, 로컬 LLM으로 한국어 요약을 생성하여 정적 사이트로 배포하는 파이프라인.

## Overview

```
PubMed ──┐
         ├→ 수집 → 중복제거 → 키워드 필터링 → LLM 관련성 판정 → LLM 요약 → HTML 생성 → GitHub Pages
bioRxiv ─┘
```

**관심 분야**: 단백질 공학, 대사공학, 생물정보학, AI 기반 효소 개량
**산업 초점**: 식품, 화학, 의약 분야의 산업적 활용 가치가 있는 연구

## Tech Stack

- **Python 3.12+** / uv
- **PubMed E-utilities** + **bioRxiv Content API**
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

# 특정 날짜 실행
uv run python -m baiodigest.main --date 2026-03-01

# 수집만 (LLM 요약 없이)
uv run python -m baiodigest.main --fetch-only

# 기존 데이터로 HTML만 재생성
uv run python -m baiodigest.main --generate-only

# 테스트
uv run pytest
```

## How It Works

1. **수집**: PubMed/bioRxiv API에서 전일 논문 메타데이터 수집
2. **중복제거**: DOI + 제목 정규화 해시 기반
3. **키워드 필터**: 포함/제외 키워드 규칙으로 1차 선별 (수백편 → ~50편)
4. **LLM 판정**: Qwen3:8b로 산업적 관련성 판정 (~50편 → ~20편)
5. **LLM 요약**: 배경/방법/결과/의미 4섹션 한국어 구조화 요약
6. **사이트 생성**: Jinja2 템플릿으로 정적 HTML 생성 → `docs/`

## Project Structure

```
src/baiodigest/
├── main.py           # CLI 진입점, 파이프라인 오케스트레이터
├── config.py         # 설정값 집중 관리
├── models.py         # 데이터 모델 (Paper, Summary, DailyDigest)
├── fetchers/         # PubMed/bioRxiv API 클라이언트
├── filters/          # 2단계 필터링 (키워드 → LLM)
├── summarizer/       # Ollama 요약 클라이언트 + 프롬프트
└── generator/        # Jinja2 정적 사이트 생성
```

## License

Private use only.
