# 문서·코드 불일치 수정 계획 (2026-11-18)

스킬 문서화(`docs/skills.md`) 중 발견한 불일치. 결정은 사용자 확인 완료.

| # | 항목 | 결정 | 작업 |
|---|---|---|---|
| 1 | `preflight.py:204` Linux 타이머 이름 `jin-claude-usage.timer` | 수정 | 실패 테스트 → `fetch-claude-usage.timer` 로 수정 |
| 2 | `sync_repo.py:73` 같은 날 재실패 시 clone 백업 없이 삭제 | 그대로 | — |
| 3 | `session_init.py:20` 타이머 재등록 5분 고정 | 주기 저장·재사용 | 실패 테스트 → init 이 고른 주기를 `~/.claude/.jin-claude-usage-interval` 에 저장, hook 은 있으면 그 값 사용 (없으면 5) |
| 4 | `keyword_detector.py` 미등록 | 등록하지 않음 | 파일·관련 테스트 삭제 (죽은 코드, 출력 형식도 틀림) |
| 5 | cleanser 패턴 전 파일 적용 | 확장자별 적용 | 실패 테스트 → Python 패턴은 `.py`, JS 패턴은 `.js/.jsx/.ts/.tsx/.mjs/.cjs` 만 |
| 6 | `project_analyzer.py:537` `.` → 빈 이름 | resolve | 실패 테스트 → `Path(...).resolve()` |
| 7 | `verified_commit` "필수" 문구 | 문서를 코드에 | "권장 — 없으면 `UNVERIFIABLE_COMMIT` 경고, overview·rules 면제" |
| 8 | 커밋에 이슈 ID 자리 없음 | 이모지 뒤 대괄호 | commit 양식: 이슈 ID 를 알 때만 `✨ [MOLE-123] 제목`. mole-linear 와 Linear 문서(Version 갱신)도 같은 표기 |
| 9 | SoT 문구 | 수정 | sot-verify 보고 `stale` 의미 명시, 없는 `sot/` 의 오류 코드 문서화, sot-create 미사용 경로 인자 힌트 제거 |
| 10 | cleanser·deepinit 문구 | 수정 | `TEMPORARY` 명시, 깨끗할 때 한 줄 출력 명시, 언어 스캔은 `IGNORE_DIRS` 만 제외 |
| 11 | hook·상태 문구 | 수정 | ambition hook "적용한 축마다", codex-side 상태 블록에 `TURN_FAILED`·`ERROR`, claude-init 에 UserPromptSubmit hook |
| 12 | 이름·설명 잔재 | 수정 | claude-init 설명·`project_analyzer.py` docstring 의 jin-claude → jstack, onboard 설명의 "커밋" 상황 정리 |

마무리: 스킬 테스트 전체 + `claude plugin validate .` → `docs/skills*.md` 해당 부분 갱신 → 버전 6.3.0 → 커밋.


## 4번 메모

등록 검토 결과: 부분 문자열 매칭이라 `commit` 이 "커밋하지 마" 에도 걸리고, `commit` 스킬은 확인 없이 커밋한다. 사용자 결정: 등록하지 않음.

## 추가 결정 (v6.3.1)

| # | 항목 | 결정 |
|---|---|---|
| 13 | cleanser 가 JS/TS `// TODO` 미감지 | JS/TS 에서 `//` 도 감지 (테스트 먼저) |
| 14 | deepinit monorepo 판정이 `packages/.cache` 등도 셈 | 숨김·`IGNORE_DIRS` 제외 (테스트 먼저) |
| 15 | cleanser 정적 스캔이 깨끗하면 합칠 표 없음 | 문서에 "없으면 같은 형식으로 새로 만든다" |
| 16 | `plugins/jstack/systemd/fetch-claude-usage.timer` 미사용 (5분 고정) | 삭제 — `install-timer.sh` 가 주기 반영해 생성 |
