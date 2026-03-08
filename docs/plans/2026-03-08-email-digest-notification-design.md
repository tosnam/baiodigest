# Email Digest Notification Design

**Date:** 2026-03-08

## Goal

일일 논문 수집과 정적 사이트 배포가 끝난 뒤, 등록된 이메일 목록에 해당 날짜 다이제스트가 게시되었음을 알리는 메일을 발송한다.

## Scope

- Gmail SMTP 앱 비밀번호 기반 발송
- 수신자 목록은 `queries.toml`과 별도인 TOML 파일로 관리
- 자동 실행 경로에서는 `git push` 성공 뒤에만 메일 발송
- 동일한 내용을 전체 수신자에게 1회 발송

## Out of Scope

- 구독 등록/해지 웹 UI
- 발송 이력 저장 및 중복 발송 방지
- HTML 메일 템플릿
- GitHub Pages 실제 반영 완료 폴링

## Approaches Considered

### 1. `main.py` 안에서 직접 발송

- 장점: 진입점이 적고 구현이 단순하다.
- 단점: 아직 배포 전 단계에서 메일이 나갈 수 있어 "올라갔다"는 의미와 맞지 않는다.

### 2. `scripts/run-daily.sh`에서 셸로 직접 SMTP 처리

- 장점: `git push` 직후에 붙이기 쉽다.
- 단점: SMTP 인증, 본문 조립, 예외 처리, 테스트가 셸에서 불안정하다.

### 3. Python 알림 모듈/CLI를 추가하고 배포 후 호출

- 장점: 발송 시점을 정확히 제어할 수 있고, 메일 로직을 Python에서 테스트 가능하게 유지할 수 있다.
- 단점: CLI 엔트리포인트가 하나 늘어난다.

**Recommendation:** 3번. 파이프라인 생성 책임과 배포 알림 책임을 분리하면서도 운영 흐름과 가장 잘 맞는다.

## Architecture

- `src/baiodigest/config.py`
  - Gmail SMTP 설정과 수신자 파일 경로를 환경변수에서 로드한다.
  - `recipients.toml`을 파싱하는 로더를 추가한다.
- `src/baiodigest/notifications/email.py`
  - 제목/본문 생성
  - Gmail SMTP SSL 연결
  - 다중 수신자 발송
- `src/baiodigest/notify.py`
  - CLI 진입점
  - 대상 날짜의 JSON/HTML 산출물 확인
  - 설정 로드 후 메일 발송 실행
- `scripts/run-daily.sh`
  - 기존 파이프라인 실행과 `git push`는 그대로 유지
  - 새 커밋이 생기고 `push`가 성공한 경우에만 알림 CLI 호출

## Configuration

### Environment Variables

- `BAIODIGEST_SMTP_HOST` default `smtp.gmail.com`
- `BAIODIGEST_SMTP_PORT` default `465`
- `BAIODIGEST_SMTP_USERNAME`
- `BAIODIGEST_SMTP_APP_PASSWORD`
- `BAIODIGEST_SMTP_FROM_NAME` default `baioDigest`
- `BAIODIGEST_RECIPIENTS_FILE` default `recipients.toml`
- `BAIODIGEST_SITE_URL`

`BAIODIGEST_SITE_URL`은 메일에 들어갈 절대 링크 생성을 위해 필요하다. 예: `https://<user>.github.io/baiodigest`

### `recipients.toml`

```toml
[[recipients]]
email = "reader1@example.com"

[[recipients]]
email = "reader2@example.com"
```

초기 버전은 `email`만 필수로 두고, 추후 `name`이나 `enabled` 필드를 추가할 수 있도록 확장 가능한 배열 구조를 사용한다.

## Data Flow

1. `scripts/run-daily.sh`가 `python -m baiodigest.main` 실행
2. 변경 사항이 있으면 `git add`, `commit`, `push`
3. `push` 성공 시 `python -m baiodigest.notify --date YYYY-MM-DD` 실행
4. 알림 CLI가 대상 날짜의 `data/YYYY-MM-DD.json`을 읽어 통계 확보
5. `docs/daily/YYYY-MM-DD.html` 존재 여부와 사이트 URL을 기반으로 링크 생성
6. Gmail SMTP로 전체 수신자에게 동일한 텍스트 메일 발송

## Email Content

- Subject: `[baioDigest] 2026-03-08 digest is live`
- Body:
  - 다이제스트 날짜
  - 포함 논문 수
  - 메인 사이트 링크
  - 해당 날짜 daily 페이지 링크

초기 버전은 plain text 메일만 지원한다. 이유는 Gmail SMTP로 가장 안정적으로 시작할 수 있고 테스트 범위도 작기 때문이다.

## Error Handling

- 수신자 파일이 비어 있거나 누락되면 발송 단계에서 명확한 에러를 발생시킨다.
- SMTP 인증 실패, 연결 실패, 발송 실패는 로그에 남기고 알림 CLI를 non-zero 종료한다.
- `run-daily.sh`는 배포 이후 알림 실패를 감지할 수 있도록 해당 실패를 그대로 반영한다.
- 다이제스트 생성과 배포는 이미 끝난 상태이므로 메일 실패가 산출물 자체를 롤백하지는 않는다.

## Testing Strategy

- `tests/test_config.py`
  - SMTP 설정 기본값/환경변수 로드 검증
  - `recipients.toml` 파싱 검증
- `tests/test_notify.py`
  - 제목/본문 생성 검증
  - 대상 날짜 산출물 경로와 링크 생성 검증
  - SMTP 클라이언트를 대체한 발송 호출 검증
- 셸 스크립트는 직접 단위 테스트하지 않고, 핵심 분기와 메일 로직은 Python 레이어에서 검증한다.

## Operational Notes

- Gmail SMTP 사용 시 발신 계정에는 2단계 인증과 앱 비밀번호가 필요하다.
- 자동 실행 환경에는 SMTP 자격증명과 사이트 URL 환경변수를 함께 주입해야 한다.
- 변경 사항이 없는 날에는 커밋/푸시가 생기지 않으므로 메일도 발송하지 않는다.
