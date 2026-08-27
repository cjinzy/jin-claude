#!/usr/bin/env python3
"""사용자 프롬프트에서 magic keyword를 감지하여 스킬을 자동 호출한다.

UserPromptSubmit hook으로 사용된다.
stdin으로 JSON 이벤트를 받아 keyword 매칭 시 block + reason을 반환한다.
"""

import json
import sys

KEYWORDS = {
    # ── 순서 주의: 긴 키워드를 짧은 부분 문자열보다 먼저 배치 ──
    # (예: "deepinit"이 "init"보다 앞에 와야 올바르게 매칭됨)
    #
    # Phase 3C: Deepinit (init 부분 문자열 충돌 방지를 위해 최상단 배치)
    "jin deepinit": "jin-deepinit",
    "deepinit": "jin-deepinit",
    "프로젝트 분석": "jin-deepinit",
    # 기존 스킬 (jin 접두사 + 접두사 없음)
    "jin init": "jin-claude-init",
    "init": "jin-claude-init",
    "jin 초기화": "jin-claude-init",
    "초기화": "jin-claude-init",
    "jin commit": "jin-commit",
    "commit": "jin-commit",
    "jin interview": "jin-interview",
    "interview": "jin-interview",
    "jin swe": "jin-swe-fix",
    "swe": "jin-swe-fix",
    # Phase 1: Orchestrator
    "jin orchestrate": "jin-orchestrator",
    "orchestrate": "jin-orchestrator",
    "오케스트레이션": "jin-orchestrator",
    # Phase 2A: Maxwork
    "jin maxwork": "jin-maxwork",
    "maxwork": "jin-maxwork",
    "병렬": "jin-maxwork",
    # Phase 2B: FSD
    "jin fsd": "jin-fsd",
    "fsd": "jin-fsd",
    "자율실행": "jin-fsd",
    # Phase 2C: Ralph
    "jin ralph": "jin-ralph",
    "ralph": "jin-ralph",
    # Phase 3A: GCC
    "jin gcc": "jin-gcc",
    "gcc": "jin-gcc",
    "다관점": "jin-gcc",
    # Phase 3B: Cleanser
    "jin cleanser": "jin-cleanser",
    "cleanser": "jin-cleanser",
    "jin deslop": "jin-cleanser",
    "deslop": "jin-cleanser",
    # Phase 4: Suggest
    "jin suggest": "jin-suggest",
    "suggest": "jin-suggest",
    "추천": "jin-suggest",
    "뭐 써야": "jin-suggest",
    "어떤 스킬": "jin-suggest",
    # Phase 5: Chub
    "jin chub": "jin-chub",
    "chub": "jin-chub",
    "context-hub": "jin-chub",
    "api 문서": "jin-chub",
    # Phase 6: SoT (substring 충돌 방지 — bare "sot" 미등록)
    "jin sot": "jin-sot-create",
    "sot create": "jin-sot-create",
    "sot 생성": "jin-sot-create",
}


def main() -> None:
    """메인 진입점."""
    event = json.loads(sys.stdin.read())
    prompt = event.get("prompt", "").lower()
    for keyword, skill in KEYWORDS.items():
        if keyword in prompt:
            print(json.dumps({"result": "block", "reason": f"[MAGIC KEYWORD: {skill}]"}))
            return
    print(json.dumps({"result": "approve"}))


if __name__ == "__main__":
    main()
