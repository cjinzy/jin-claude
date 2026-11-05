---
name: jin-commit
description: git diff 를 분석해 gitmoji + 한국어 커밋 메시지를 추천하고, 사용자 확인 후 커밋한다. "jin commit", "커밋", "커밋 메시지", "commit", "commit message", "git commit" 요청이나 작업 완료 후 변경사항을 커밋할 때 사용한다.
argument-hint: "[message]"
---

# jin-commit

## 메시지 포맷

```
<Emoji> <한국어 제목> [— 스코프] [+ 추가사항]

<본문 (선택): what/why>
```

- 제목: 이모지로 시작, 명사형 동작어구("버그 수정", "기능 추가"), 한 줄·간결하게, 마침표 없음.
- 영문 규칙 중 "50자 제한·첫 글자 대문자·명령형"은 한국어 제목에 적용하지 않는다. 제목 속 영문 고유명사·코드명은 원래 표기 유지.
- 제목과 본문은 빈 줄로 구분. 본문은 72자에서 줄바꿈, how 가 아닌 what/why.
- 스코프: Full-stack 은 한 커밋에 묶고 `— Full Stack (Backend + Frontend + Migration)`, 관련 컴포넌트는 `+ A + B`, 복수 변경은 `, ` 또는 ` + `.

### 예시

```
✨ 후속 쿼리 제안 기능 추가 및 토글 버튼 구현
🐛 Token overflow 시 tool_result 미수신 버그 수정
♻️ 사이드바 탭 메뉴 전환 + 수평 아코디언 + ESC 닫기
✨ 대화 기록 영속화 — Full Stack (Migration + Backend + Frontend)
🔧 docker-compose 설정 수정: 포트 노출 방식 변경
🗃️ 세션 테이블 마이그레이션 추가 및 Repository 패턴 적용
```

## 이모지 선택 (gitmoji.dev 선별)

변경 성격에 맞는 첫 행을 고른다. 여러 성격이 섞이면 주된 변경 기준.

| Emoji | Code | 선택 기준 |
|-------|------|-----------|
| ✨ | `:sparkles:` | 새 기능·새 파일 |
| 🐛 | `:bug:` | 버그 수정 |
| 🚑 | `:ambulance:` | 긴급 핫픽스 |
| 🩹 | `:adhesive_bandage:` | 사소한 수정 (위치·문구 조정 등) |
| ✏️ | `:pencil2:` | 오타 수정 |
| ♻️ | `:recycle:` | 리팩토링 (동작 동일) |
| 🎨 | `:art:` | 코드 구조·포맷 개선 |
| 🏗️ | `:building_construction:` | 아키텍처 변경 |
| ⚡ | `:zap:` | 성능 개선 |
| 💄 | `:lipstick:` | UI·스타일만 변경 |
| 🚸 | `:children_crossing:` | UX·사용성 개선 |
| 🔧 | `:wrench:` | 설정 파일만 변경 |
| 🔨 | `:hammer:` | 개발 스크립트 |
| 🙈 | `:see_no_evil:` | .gitignore |
| 📝 | `:memo:` | 문서만 변경 |
| 💡 | `:bulb:` | 소스 주석 |
| ✅ | `:white_check_mark:` | 테스트 추가·수정 |
| 🗃️ | `:card_file_box:` | DB·마이그레이션 |
| ⬆️ ➕ ➖ | `:arrow_up:` `:heavy_plus_sign:` `:heavy_minus_sign:` | 의존성 업그레이드·추가·제거 |
| 🔒 | `:lock:` | 보안 |
| 🛂 | `:passport_control:` | 인증·권한 |
| 🥅 | `:goal_net:` | 에러 처리 |
| 🔊 🔇 | `:loud_sound:` `:mute:` | 로그 추가·제거 |
| 🔥 | `:fire:` | 코드·파일 삭제 |
| ⚰️ | `:coffin:` | 데드 코드 제거 |
| 🚚 | `:truck:` | 파일 이동·이름 변경 |
| 💥 | `:boom:` | 브레이킹 체인지 |
| ⏪ | `:rewind:` | 되돌리기 |
| 🧱 | `:bricks:` | 인프라 |
| 🚀 | `:rocket:` | 배포 |
| 📦 | `:package:` | 빌드·패키지 |
| 🔖 | `:bookmark:` | 버전 태그·릴리스 |

## 워크플로우

1. `git status` + `git diff` (스테이징된 경우 `git diff --staged`) 로 변경 분석.
2. 스테이징 대상 결정: 사용자가 지정한 파일 또는 이번 변경에 속한 파일만. `git add -A` / `git add .` 금지. 무관한 변경·비밀 파일(.env 등)은 제외하고 알린다.
3. 이모지 선택 → 메시지 작성 (`$ARGUMENTS` 가 있으면 반영).
4. 스테이징 목록 + 메시지를 보여주고 사용자 확인. 확인 전 커밋 금지.
5. 승인되면 `git add <files>` → `git commit`.

## 주의사항

- `Co-Authored-By` 라인을 넣지 않는다. harness 기본 attribution 안내를 의도적으로 덮어쓰는 사용자 규칙이다.
