---
name: jin-interview
argument-hint: "[instructions]"
description: 사용자를 깊이 인터뷰해 구현 전 상세 스펙 파일을 작성한다. "jin interview", "인터뷰", "스펙 작성", "요구사항 정리", "spec", "기능 설계 전 질문" 요청이나 모호한 기능을 구현하기 전에 결정 사항을 확정할 때 사용한다.
allowed-tools: AskUserQuestion, Read, Write
---

Follow the user instructions and interview me in detail using AskUserQuestion about anything: technical implementation, UI & UX, concerns, tradeoffs. Skip obvious questions. Read relevant code first so questions are grounded. Keep interviewing until every decision is settled, then write the spec. <instructions>$ARGUMENTS</instructions>

## Output

Write the spec to `docs/specs/<topic>-spec.md` (`<topic>` = kebab-case from the instructions). If the file exists, ask before overwriting.

Required sections:
- `## Goal` — what and why
- `## Scope` — in / out
- `## Decisions` — each `D<N>`: chosen option + reason
- `## Accepted shortcuts` — ceiling + upgrade trigger (or "none")
- `## Open questions`
- `## Success criteria` — verifiable checks

## Question format (decision brief)

Every AskUserQuestion is a decision brief. Number them `D1`, `D2`, … across the interview.

```
D<N> — <one-line question title>
ELI10: <2-4 plain sentences: what is being decided and why it matters>
Recommendation: <choice> because <one-line reason>
Completeness: A=X/10, B=Y/10   (10 = all edge cases, 7 = happy path, 3 = shortcut)
   or: Note: options differ in kind, not coverage — no completeness score
Options:
A) <label> (recommended)
  ✅ <pro>  ❌ <con>
B) <label>
  ✅ <pro>  ❌ <con>
Net: <one-line trade-off>
```

Rules:
- Put the recommended option FIRST with the `(recommended)` suffix on its label.
- `Recommendation:` line is always present. Taste call → `Recommendation: <default> — taste call, no strong preference`.
- Score `Completeness` only when options differ in coverage; otherwise write the kind-note.
- Selected option with Completeness ≤ 7 → record it in the spec under `## Accepted shortcuts` with ceiling and upgrade trigger.
