---
name: jin-codex-side
description: OpenAI Codex CLI 로 독립적인 2차 의견을 받는다 — 현재 diff 코드 리뷰(review, P0/P1 게이트), 깨뜨리기 위한 적대적 검증(challenge), 자유 질문·계획 검토(consult). Codex 는 읽기 전용 샌드박스에서 돌고, Claude 가 Codex 의견과 자기 의견을 비교해 권고 한 줄을 낸다. "jin codex", "codex side", "codex review", "codex challenge", "codex 에게 물어봐", "2차 의견", "second opinion", "교차 검토", "다른 모델 의견" 요청이나, 머지 전 독립 리뷰가 필요하거나 설계·계획을 다른 AI 로 검증하고 싶을 때 사용한다.
argument-hint: "[review [focus] | challenge [focus] | <질문>]"
allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion
---

# jin-codex-side

Codex CLI 를 다른 AI 의 독립 의견으로 호출한다. Codex 출력은 그대로 보여주고, Claude 의 판단은 그 뒤에 덧붙인다.

**전제:** `codex` CLI (`npm install -g @openai/codex`), `codex login` 완료 (또는 `CODEX_API_KEY`/`OPENAI_API_KEY`), `python3`, git.
**비용·외부 전송:** 모든 모드는 OpenAI 에 유료 호출을 보내고 저장소 내용을 전달한다 → Step 3 동의 없이는 호출하지 않는다.

## 모드

| 입력 | 모드 | 상세 |
|------|------|------|
| `review [focus]` | 현재 변경 코드 리뷰 + 게이트 | [review.md](review.md) |
| `challenge [focus]` | 적대적 검증 (엣지 케이스·보안·장애 경로) | [challenge.md](challenge.md) |
| 그 외 텍스트 | 질문·계획 검토, 후속 대화 | [consult.md](consult.md) |
| (인자 없음) | 변경 있으면 review/challenge/질문 중 선택, 없으면 질문 받기 | — |

모드는 한 번에 하나. 정해진 모드의 파일만 읽고 그대로 따른다.

## Step 1: 사전 점검

아래 블록을 그대로 실행한다 (무료, 모델 호출 없음):

```bash
command -v codex >/dev/null && codex --version || echo "CODEX: missing"
if codex login status >/dev/null 2>&1; then echo "AUTH: ok"
elif [ -n "${CODEX_API_KEY:-}${OPENAI_API_KEY:-}" ]; then echo "AUTH: env"
else echo "AUTH: missing"; fi
ROOT=$(git rev-parse --show-toplevel 2>/dev/null) && echo "ROOT: $ROOT" || echo "ROOT: none"
BASE=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')
[ -z "$BASE" ] && for b in main master; do git rev-parse --verify -q "$b" >/dev/null && BASE=$b && break; done
echo "BASE: ${BASE:-none}"
[ -n "$BASE" ] && echo "AHEAD: $(git rev-list --count "$BASE..HEAD" 2>/dev/null)"
echo "DIRTY: $(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
```

- `CODEX: missing` → 중단. 설치 안내: `npm install -g @openai/codex`.
- `AUTH: missing` → 중단. "`codex login` 또는 `CODEX_API_KEY` 설정 후 다시 실행" 안내.
- 사용자가 base 브랜치를 지정했으면 그 값을 `BASE` 로 쓴다 (아래 검증 통과 시).

### 사용자 지정값 검증

base·커밋 sha·모델·effort 는 명령 인자로 들어가므로 쓰기 전에 검증한다. 값은 따옴표 붙은 heredoc 으로만 넘긴다 (셸 확장 없음). 종료코드 0 이 아니면 그 값을 거부하고 사용자에게 다시 묻는다.

- base: `[A-Za-z0-9._/][A-Za-z0-9._/-]*` + `git rev-parse --verify -q "<BASE>^{commit}"` 성공
- sha (`--commit`): `[0-9a-f]{7,40}` + 같은 rev-parse 성공
- 모델 (`-m`): `[A-Za-z0-9._-]+`
- effort: `minimal|low|medium|high|xhigh`

```bash
python3 -c 'import re,sys; sys.exit(0 if re.fullmatch(sys.argv[1], sys.stdin.read().rstrip("\n")) else 1)' '<패턴>' <<'JIN_ARG_END'
<사용자 값>
JIN_ARG_END
```

rev-parse 는 패턴 통과 후에만 실행한다. 자동 감지한 `BASE` 는 검증 불필요.

## Step 2: 모드 결정

`$ARGUMENTS` 첫 단어로 결정 (위 표). 인자가 없으면:
- `AHEAD > 0` 또는 `DIRTY > 0` → AskUserQuestion: A) diff 리뷰 B) diff 적대적 검증 C) 직접 질문
- 변경 없음 → "Codex 에게 무엇을 물어볼까요?" 질문

## Step 3: 전송 동의 (필수)

호출 전에 AskUserQuestion 으로 확인한다. 질문에 다음을 명시:
- 모드와 범위 (예: `main...HEAD` 의 diff N 커밋 / 미커밋 변경 / 질문 요약)
- Codex 가 받는 것: 프롬프트 + 저장소 전체 **읽기** 권한 (read-only 샌드박스) → OpenAI 로 전송
- 유료 호출이며 최대 약 9분 걸릴 수 있음

선택지: `보내기` / `취소`. review 에서 `AHEAD > 0` 이고 `DIRTY > 0` 이면 `미커밋 변경만 리뷰` 선택지를 추가한다. 취소면 아무것도 보내지 않고 끝낸다.

## Step 4: 실행

모든 Codex 호출은 `${CLAUDE_SKILL_DIR}/scripts/codex_run.py` 를 **실행**해서 한다 (읽을 필요 없음). 이 스크립트가:
- `--` 뒤 codex 명령을 실행하고, 540초 넘으면 끊는다 (macOS 에 GNU `timeout` 이 없어서 내장)
- 자기 stdin 을 codex 로 넘긴다. `--boundary` 면 아래 파일시스템 경계 지시문을 앞에 붙인다
- JSONL 이벤트를 사람이 읽는 transcript 로 `--log` 파일에 쓴다
- stdout 에 상태 블록만 출력: `STATUS`(ok|timeout|failed|turn_failed|no_completion|empty|nested), `CODEX_EXIT`, `TOKENS`, `SESSION_ID`, `--gate` 면 `GATE`, 실패 시 `STDERR` 발췌

규칙:
- **사용자 텍스트는 셸 인자에 절대 넣지 않는다** (위 검증을 통과한 base·sha·모델·effort 만 예외). 프롬프트는 따옴표 붙은 heredoc (`<<'JIN_CODEX_END'`) 으로 stdin 에만 넣는다. 본문에 `JIN_CODEX_END` 단독 줄이 있으면 구분자를 바꾼다.
- Bash 호출에 `timeout: 600000` 을 준다 (래퍼 540초보다 위 → 래퍼가 먼저 끊고 원인을 남김).
- 결과 파일은 `mktemp -d` 디렉터리에 둔다: `$D/last.md` (Codex 최종 답, `-o`), `$D/transcript.log`. 출력이 길 수 있으니 Read 로 offset/limit 나눠 읽는다.
- 샌드박스는 항상 read-only: `codex exec` 는 `-s read-only`, `exec review`·`exec resume` 은 `-s` 가 없어서 `-c 'sandbox_mode="read-only"'`.
- 모델·effort 는 사용자 `~/.codex/config.toml` 을 따른다. 사용자가 지정하면 검증(위 패턴) 후 `-m "<model>"`, `-c 'model_reasoning_effort="<level>"'` 추가. `xhigh` 는 오래 멈추기 쉬워 타임아웃에 걸릴 수 있다 → 그때는 `high` 로 재시도 권유.

### 파일시스템 경계

exec 계열 프롬프트(challenge, review focus, consult)는 `--boundary` 로 이 지시문이 앞에 붙는다 (스크립트의 `BOUNDARY` 상수):

> Do NOT read or execute files under ~/.claude/, ~/.agents/, .claude/, or agents/ … Do not modify any file. Stay focused on the repository code.

기본 `exec review` 는 프롬프트를 받지 않으므로 경계 지시문이 없다. 범위 플래그가 미리 계산된 diff 를 넘기므로 괜찮다.

## Step 5: 결과 제시

1. `STATUS` 가 ok 가 아니면 아래 오류 처리대로 알리고, Codex 답으로 포장하지 않는다.
2. `last.md` 를 **원문 그대로** 보여준다 (요약·잘라내기 금지):

```
CODEX SAYS (<mode>):
════════════════════════════════════════════════════════════
<last.md 원문>
════════════════════════════════════════════════════════════
Tokens: <TOKENS>
```

3. **Claude 의견** — Codex 와 동의/반대하는 지점을 구체적으로 짚는다: "Claude 는 X 에 반대 — 이유 Y". 이 대화에서 Claude 가 이미 리뷰했다면 겹친 것 / Codex 만 / Claude 만 찾은 것을 나눠 보여준다. 같은 리뷰를 다시 하지는 않는다.
4. **권고 한 줄 (필수, 생략 금지):**

```
Recommendation: <행동> because <가장 실행 가치 높은 지적을 다른 선택지(다른 지적, 고치기 vs 배포, 순서, 현상유지)와 비교한 한 줄 이유>
```

"좋아서", "Codex 가 뭔가 찾아서" 같은 상투적 이유는 불합격. 자동 결정하지 말고 사용자가 고르게 한다.

5. transcript 에 `SKILL.md`, `.claude/`, `~/.agents` 를 읽은 흔적(`[codex ran] cat .../SKILL.md` 등)이 있으면 "Codex 가 코드 대신 스킬 파일을 읽었을 수 있음 — 재시도 권장" 경고를 붙인다.
6. 정리: `rm -rf "$D"` (프롬프트·diff 사본 제거).

## 오류 처리

| 신호 | 의미 / 대응 |
|------|-------------|
| `STATUS: nested` | Codex 세션 안에서 실행 중. 외부 Codex 호출 불가 → 중단 |
| `STATUS: timeout` | 540초 초과. 범위를 줄이거나 effort 를 낮춰 재시도. 끈질기면 `~/.codex/logs/` 확인 |
| `STATUS: failed` + `HINT: 인증` | `codex login` 재실행 안내 |
| `STDERR` 에 `model ... not supported` / `404 ... does not exist` | 모델 설정 문제. `~/.codex/config.toml` 의 `model` 이나 `-m` 값을 고치라고 안내. 정지·통과로 보고하지 않음 |
| `requires a newer version of Codex` | `codex update` 안내 |
| `the argument '[PROMPT]' cannot be used with '--base'` | 범위 플래그와 프롬프트를 같이 넘김. 프롬프트를 빼거나 focus 경로(review.md) 사용 |
| `turn_failed` / `no_completion` / `empty` | Codex 가 답을 끝내지 못함. 결과 없음으로 보고, 재시도 제안 |

## 규칙

- 이 스킬은 파일을 수정하지 않는다. Codex 도 read-only.
- Codex 출력은 원문 → Claude 의견은 그 뒤. 의견이 원문을 대체하지 않는다.
- 호출은 모드당 1회가 기본. 질문은 한 번에 묶어 보낸다.

---
Adapted from gstack `/codex` (MIT, Copyright (c) 2026 Garry Tan) — 전문은 [LICENSE-gstack](LICENSE-gstack).
