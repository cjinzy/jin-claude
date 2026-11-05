#!/usr/bin/env python3
"""UserPromptSubmit: ambition 모드 계획 진입.

    prompt 에 "ambition"/"앰비션"  → LOAD (모드 무관, 묻지 않음)
    permission_mode == "plan"      → ASK  (이 대화에서 미결정일 때만 사용자에게 묻기)
    그 외                          → 출력 없음

어떤 오류에도 출력 없이 종료한다 — 이 hook 이 프롬프트를 막으면 안 된다.
"""

import json
import re
import sys

KEYWORD = re.compile(r"ambition|앰비션", re.IGNORECASE)
PLAN_MODE = "plan"
SKILLS = ("jin-claude:jin-altitude", "jin-claude:jin-depth", "jin-claude:jin-range")

LOAD = (
    "[jin-claude] Ambition 모드: 계획 작성 전에 Skill 도구로 "
    + ", ".join(SKILLS)
    + " 를 모두 로드하고 각 지침을 따른다. 계획에 `## Ambition` 섹션을 넣는다 "
    "(Altitude / Depth / Range 각 한 항목, 해당 없으면 `N/A — 이유`)."
)
ASK = (
    "[jin-claude] plan 모드: 이 대화에서 아직 정하지 않았다면 계획을 시작하기 전에 AskUserQuestion 으로 "
    "'ambition 모드(" + ", ".join(SKILLS) + " 적용, 계획에 `## Ambition` 섹션)로 계획할까요?' 를 묻는다. "
    "예 → 그 3개 스킬을 Skill 도구로 로드하고 따른다. 아니오 → 일반 계획. 이미 정했으면 그 결정을 따른다."
)


def context_for(prompt: str, mode: str) -> str | None:
    """주입할 지시. 대상이 아니면 None."""
    if KEYWORD.search(prompt):
        return LOAD
    if mode == PLAN_MODE:
        return ASK
    return None


def main() -> None:
    try:
        data = json.loads(sys.stdin.read())
        context = context_for(data.get("prompt", ""), data.get("permission_mode", ""))
    except Exception as e:  # noqa: BLE001 — 프롬프트를 막지 않기 위해 전부 삼킨다
        print(f"[jin-claude] ambition_plan skipped: {e!r}", file=sys.stderr)
        return
    if context:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": context}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
