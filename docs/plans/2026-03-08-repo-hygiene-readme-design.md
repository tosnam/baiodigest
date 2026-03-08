# Repo Hygiene And README Design

**Date:** 2026-03-08

## Goal

저장소에서 로컬 작업 문서와 에이전트 지침 파일을 제외하고, `README.md`를 현재 서비스 상태와 맞게 정리한다.

## Context

- 사용자는 `CLAUDE.md`, `docs/plans/`, `tasks/`가 원격 저장소에 올라가지 않도록 원한다.
- 현재 이 경로들은 이미 git에 추적 중이라 `.gitignore`만 추가해서는 원격 저장소에서 사라지지 않는다.
- `README.md`는 현재 홈 카피, CSS 설명, 일간 요약 구조 등 일부 표현이 최신 상태와 어긋나 있다.

## Chosen Direction

다음 세 가지를 한 번에 정리한다.

1. `.gitignore`에 `CLAUDE.md`, `docs/plans/`, `tasks/`를 추가한다.
2. 이미 추적 중인 동일 경로는 `git rm --cached`로 인덱스에서만 제거한다.
3. `README.md`를 현재 동작과 맞도록 최소 수정한다.

## README Scope

이번에 바꾸는 범위는 아래에 한정한다.

- 정적 사이트 설명에서 `Pico CSS` 표현 제거
- 일간 페이지 구조를 `왜 읽을 만한가 / 배경 / 방법 / 결과 / 활용` 기준으로 설명
- 홈 페이지가 `Today's Digest` CTA를 쓰는 현재 상태와 어긋나는 표현 정리
- 배포/알림/CLI 설명은 실제 코드와 맞는 선에서 유지

## Non-Goals

- 앱 구조나 파이프라인 동작 자체 변경
- GitHub Actions, 배포 전략, 이메일 기능 재설계
- `docs/` 정적 산출물 제거

## Testing Strategy

- `.gitignore` 변경 뒤 `git status --short`로 추적 해제 대상이 기대대로 보이는지 확인
- `README.md` 수정 후 전체 테스트 실행
- 브랜치를 `main`에 병합한 뒤 다시 테스트 실행
- 마지막에 `git push origin main`으로 원격 반영

## Success Criteria

- `CLAUDE.md`, `docs/plans/`, `tasks/`가 더 이상 원격 저장소에 남지 않는다.
- 같은 경로는 이후 새 파일이 생겨도 기본적으로 추적되지 않는다.
- `README.md`가 현재 프로젝트 상태와 맞는다.
