# Index Hero Copy Design

**Date:** 2026-03-08

## Goal

홈 페이지 히어로 섹션의 두 문구를 영어로 조정한다.

- `최신 다이제스트` -> `Today's Digest`
- `다이제스트 보기` -> `View`

## Context

- 사용자는 홈 페이지의 상단 카드만 더 간결한 영어 라벨로 바꾸길 원한다.
- 다른 한국어 문구와 페이지 구조는 유지한다.
- 이 변경은 정적 사이트 생성 결과와 테스트 기대값에도 반영돼야 한다.

## Chosen Direction

템플릿과 생성 테스트만 수정한다.

- `templates/index.html`의 제목과 CTA 라벨을 변경한다.
- `tests/test_site_generation.py`의 홈 페이지 기대 문자열을 같이 업데이트한다.

## Rendering Decision

- 히어로 상단 `eyebrow`인 `Latest issue`는 유지
- 본문 문장 `2026-03-08 기준으로 선별한 논문 ...`은 유지
- 버튼 스타일과 링크 대상은 유지

## Testing Strategy

- 홈 페이지 생성 테스트가 새 영어 문구를 기대하도록 먼저 변경한다.
- 해당 테스트가 실패하는지 확인한 뒤 템플릿을 수정한다.
- 홈 생성 테스트와 전체 테스트를 다시 통과시킨다.
- 마지막에 `preview/index.html`을 재생성해 실제 확인 경로를 만든다.

## Success Criteria

- 홈 페이지에 `Today's Digest`가 렌더링된다.
- CTA 버튼 문구가 `View`로 렌더링된다.
- 다른 홈 구조와 링크는 바뀌지 않는다.
