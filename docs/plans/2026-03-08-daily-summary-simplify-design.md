# Daily Summary Simplify Design

**Date:** 2026-03-08

## Goal

일간 논문 요약 카드에서 `활용`, `주의` 추가 블록을 제거하고, 기존 `의미` 블록의 라벨만 `활용`으로 변경한다. 동시에 더 이상 쓰지 않는 `Summary.application_note`, `Summary.caution_note`와 관련 생성 로직도 제거한다.

## Context

- 직전 변경으로 일간 논문 카드에는 아래 순서의 세로 블록이 추가되었다.
  - `왜 읽을 만한가`
  - `배경`
  - `방법`
  - `결과`
  - `의미`
  - `활용`
  - `주의`
- 사용자는 이 구조가 과하다고 판단했고, `활용`과 `주의` 블록은 제거하기로 했다.
- 대신 기존 `의미`가 사실상 활용 관점 해석에 가깝다고 보고, 이 블록의 제목만 `활용`으로 바꾸길 원한다.

## Chosen Direction

최종 카드 구조는 아래 5개 블록으로 단순화한다.

1. `왜 읽을 만한가`
2. `배경`
3. `방법`
4. `결과`
5. `활용`

여기서 `활용`은 기존 `Summary.significance` 내용을 그대로 사용하고, 라벨만 변경한다.

## Data Model Decision

더 이상 사용하지 않는 필드는 제거한다.

- `Summary.application_note`
- `Summary.caution_note`

요약 프롬프트와 Ollama 파서도 다시 단순화한다.

- summary JSON 키는 `background`, `method`, `result`, `significance`만 유지
- `application_note`, `caution_note` 파싱 제거

## Rendering Decision

- `templates/daily.html`
  - `활용`, `주의` 세부 블록 제거
  - 기존 `의미` 블록 제목을 `활용`으로 변경
- `static/style.css`
  - 현재 `paper-detail-stack` 구조는 유지
  - 단순히 블록 수만 줄어드는 형태
- footer는 그대로 유지
  - `키워드`
  - `confidence`

## Testing Strategy

- 일간 페이지가 `왜 읽을 만한가, 배경, 방법, 결과, 활용`만 순서대로 렌더링하는지 확인
- `주의`와 별도 `활용` 블록이 더 이상 없는지 확인
- `Summary` JSON round-trip에서 `application_note`, `caution_note`가 제거됐는지 확인
- summary 파서가 다시 4개 키만 처리해도 정상 동작하는지 확인

## Success Criteria

- 화면에서 `활용`, `주의` 추가 블록이 사라진다.
- 기존 `의미` 블록은 `활용`으로 보인다.
- 안 쓰는 summary 필드와 관련 생성 로직이 제거된다.
