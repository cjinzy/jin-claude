---
name: jin-interview
argument-hint: [instructions]
description: Interview user in-depth to create a detailed spec
allowed-tools: AskUserQuestion, Write
---

Follow the user instructions and interview me in detail using the AskUserQuestionTool about literally anything: technical implementation, UI & UX, concerns, tradeoffs, etc. but make sure the questions are not obvious. be very in-depth and continue interviewing me continually until it's complete. then, write the spec to a file. <instructions>$ARGUMENTS</instructions>

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
