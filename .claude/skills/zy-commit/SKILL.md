---
name: mole-commit
description: gitmoji 기반 커밋 메시지 자동 추천 및 생성
triggers:
  - commit
  - 커밋
  - git
argument-hint: "[message]"
---

# mole-commit: Gitmoji 기반 커밋 메시지 자동 추천

## Gitmoji 레지스트리 (gitmoji.dev 기반, 프로젝트 맞춤 선별)

### 핵심 (자주 사용)

| Emoji | Code | 의미 | 프로젝트 사용빈도 |
|-------|------|------|-------------------|
| ✨ | `:sparkles:` | 새 기능 추가 | 89회 (최다) |
| 🐛 | `:bug:` | 버그 수정 | 3회 |
| ♻️ | `:recycle:` | 코드 리팩토링 | 3회 |
| 🔧 | `:wrench:` | 설정 파일 추가/수정 | 4회 |
| 💄 | `:lipstick:` | UI/스타일 수정 | 1회 |
| 📝 | `:memo:` | 문서 추가/수정 | 1회 |
| 🔒 | `:lock:` | 보안 이슈 수정 | 1회 |
| 🔥 | `:fire:` | 코드/파일 삭제 | 1회 |
| 🗑️ | `:wastebasket:` | 폐기 코드 정리 | 2회 |
| 🔨 | `:hammer:` | 개발 스크립트 추가/수정 | 1회 |

### 권장 (프로젝트에 유용하나 아직 미사용)

| Emoji | Code | 의미 |
|-------|------|------|
| 🚑 | `:ambulance:` | 긴급 핫픽스 |
| ⚡ | `:zap:` | 성능 개선 |
| 🎨 | `:art:` | 코드 구조/포맷 개선 |
| ✅ | `:white_check_mark:` | 테스트 추가/수정/통과 |
| ⬆️ | `:arrow_up:` | 의존성 업그레이드 |
| ➕ | `:heavy_plus_sign:` | 의존성 추가 |
| ➖ | `:heavy_minus_sign:` | 의존성 제거 |
| 🚀 | `:rocket:` | 배포 관련 |
| 🗃️ | `:card_file_box:` | DB 관련 변경 |
| 🔊 | `:loud_sound:` | 로그 추가/수정 |
| 🔇 | `:mute:` | 로그 제거 |
| 🏗️ | `:building_construction:` | 아키텍처 변경 |
| 🩹 | `:adhesive_bandage:` | 사소한 수정 |
| ⚰️ | `:coffin:` | 데드 코드 제거 |
| 🩺 | `:stethoscope:` | 헬스체크 추가/수정 |
| 🧱 | `:bricks:` | 인프라 관련 변경 |
| 🛂 | `:passport_control:` | 인증/권한 관련 |
| 🚸 | `:children_crossing:` | UX/사용성 개선 |
| 🏷️ | `:label:` | 타입 추가/수정 |
| 🌐 | `:globe_with_meridians:` | i18n/l10n |
| ✏️ | `:pencil2:` | 오타 수정 |
| 💥 | `:boom:` | 브레이킹 체인지 |
| ⏪ | `:rewind:` | 변경사항 되돌리기 |
| 🚚 | `:truck:` | 파일/경로 이동/이름변경 |
| 👽 | `:alien:` | 외부 API 변경 대응 |
| 🥅 | `:goal_net:` | 에러 캐치 |
| 🧪 | `:test_tube:` | 실패하는 테스트 추가 |
| 👔 | `:necktie:` | 비즈니스 로직 추가/수정 |
| 🦺 | `:safety_vest:` | 유효성 검증 코드 |
| 🙈 | `:see_no_evil:` | .gitignore 수정 |
| 📦 | `:package:` | 빌드/패키지 관련 |
| 💡 | `:bulb:` | 소스 코드 주석 |

## 커밋 메시지 포맷

```
[Emoji] [한국어 설명] [— 스코프 (선택)] [+ 추가사항]
```

### 예시

```
✨ 후속 쿼리 제안 기능 추가 및 토글 버튼 구현
🐛 Token overflow 시 tool_result 미수신 버그 수정
♻️ 사이드바 탭 메뉴 전환 + 수평 아코디언 + ESC 닫기
✨ 대화 기록 영속화 — Full Stack (Migration + Backend + Frontend)
🔧 docker-compose 설정 수정: 포트 노출 방식 변경
💄 Activity Bar 아이콘 50% 확대 + hover tooltip 추가
📝 System prompt에 MCP 도구 호출 7회 제한 규칙 추가
🗃️ 세션 테이블 마이그레이션 추가 및 Repository 패턴 적용
```

## 스코프 규칙

- **Full-stack 기능**: 관련 파일 모두 하나의 커밋 (`— Full Stack (Backend + Frontend + Migration)`)
- **UI 개선**: 관련 컴포넌트 묶어서 커밋 (`+ 컴포넌트A + 컴포넌트B`)
- **사소한 수정**: 이모지 없이 간단히 (`사이드바 버튼 위치 수정`)
- **복수 변경**: `, ` 또는 ` + ` 로 구분

## 워크플로우

1. `git status` + `git diff` 로 변경사항 분석
2. 변경 유형 분류 → 이모지 자동 선택
3. 한국어 커밋 메시지 생성
4. 커밋 전 사용자 확인

## 주의사항

- `Co-Authored-By` 라인을 커밋 메시지에 포함하지 않는다

## 이모지 자동 선택 규칙

- 새 파일 생성 → ✨
- 기존 버그 수정 → 🐛
- 코드 구조 변경 (기능 동일) → ♻️
- 설정 파일만 변경 → 🔧
- CSS/스타일만 변경 → 💄
- 문서만 변경 → 📝
- 파일 삭제 → 🔥 또는 🗑️
- 테스트 추가 → ✅
- DB 마이그레이션 → 🗃️
- 의존성 변경 → ⬆️/➕/➖
- 보안 관련 → 🔒
- 성능 개선 → ⚡
- 인증/권한 → 🛂
- 인프라/배포 → 🧱/🚀
