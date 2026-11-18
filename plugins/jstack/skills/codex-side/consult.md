# Consult 모드

Codex 에게 코드베이스에 대한 질문을 하거나 계획을 검토받는다. 같은 대화에서 후속 질문을 이어갈 수 있다.

## 1. 프롬프트 구성

**일반 질문:** 사용자 질문 원문을 그대로 쓴다.

**계획 검토** (질문이 계획/플랜/스펙 검토이거나 계획 파일을 지목한 경우):
- Codex 는 저장소 밖(`~/.claude/plans/` 등)을 못 읽는다 → Claude 가 계획 파일을 Read 해서 **전문을 프롬프트에 넣는다**. 경로만 넘기지 않는다.
- 계획에 나오는 저장소 내 소스 경로를 나열해 Codex 가 바로 읽게 한다.
- 앞에 붙일 지시:

```
You are a brutally honest technical reviewer. Review this plan for: logical gaps and unstated
assumptions, missing error handling or edge cases, overcomplexity (is there a simpler approach?),
feasibility risks, and missing dependencies or sequencing issues. Be direct. Be terse. No compliments.
Also read these source files referenced in the plan: <경로 목록>

THE PLAN:
<계획 전문>
```

## 2. 실행

**새 대화.** 저장소 밖이면 (`ROOT: none`) `cd "$(git rev-parse …)" &&` 와 `-C "$PWD"` 를 빼고 `--skip-git-repo-check` 를 붙인다.

```bash
D=$(mktemp -d) && cd "$(git rev-parse --show-toplevel)" && \
python3 "${CLAUDE_SKILL_DIR}/scripts/codex_run.py" --boundary --log "$D/transcript.log" -- \
  codex exec - -C "$PWD" -s read-only --json -o "$D/last.md" <<'JIN_CODEX_END'
<프롬프트>
JIN_CODEX_END
echo "D=$D"
```

출력의 `SESSION_ID` 를 기억한다 (대화 안에서만, 파일로 남기지 않음).

**후속 질문.** 이 대화에서 앞서 받은 `SESSION_ID` 가 있으면 이어갈지 새로 시작할지 AskUserQuestion 으로 묻는다. 이어가면:

```bash
D=$(mktemp -d) && cd "$(git rev-parse --show-toplevel)" && \
python3 "${CLAUDE_SKILL_DIR}/scripts/codex_run.py" --boundary --log "$D/transcript.log" -- \
  codex exec resume "<SESSION_ID>" - -c 'sandbox_mode="read-only"' --json -o "$D/last.md" <<'JIN_CODEX_END'
<후속 질문>
JIN_CODEX_END
echo "D=$D"
```

`<SESSION_ID>` 는 스크립트가 출력한 값만 쓴다 (영숫자·`-` 만). resume 은 토큰을 아끼지 않는다 — 이전 맥락이 정말 필요할 때만 쓴다. resume 이 실패하면 새 대화로 다시 보낸다.

## 3. 제시

헤더 `CODEX SAYS (consult)`. Claude 이해와 다른 지점은 "Claude 는 X 에 반대 — 이유 Y" 로 표시한다.

권고 예: `Recommendation: Codex 의 "SQLite 로 교체" 제안은 기각한다 because 예상 규모에선 팀의 Postgres 운영 경험이 단순화 이득보다 크고, Codex 의 두 번째 제안(read replica)이 읽기 부하 문제를 이미 해결한다.`
