#!/usr/bin/env python3
"""사용자 프롬프트에서 magic keyword를 감지하여 스킬을 자동 호출한다.

UserPromptSubmit hook으로 사용된다.
stdin으로 JSON 이벤트를 받아 keyword 매칭 시 block + reason을 반환한다.
"""

import json
import sys

KEYWORDS = {
    # 기존 스킬 (jin 접두사 + 접두사 없음)
    "jin init": "jin-claude-init",
    "jin 초기화": "jin-claude-init",
    "jin commit": "jin-commit",
    "jin interview": "jin-interview",
    "jin swe": "jin-swe-fix",
    # Phase 1: Orchestrator (2개)
    "jin orchestrate": "jin-orchestrator",
    "오케스트레이션": "jin-orchestrator",
    # Phase 2A: Maxwork (2개)
    "jin maxwork": "jin-maxwork",
    "병렬": "jin-maxwork",
    # Phase 2B: FSD (2개)
    "jin fsd": "jin-fsd",
    "자율실행": "jin-fsd",
    # Phase 2C: Ralph (1개)
    "jin ralph": "jin-ralph",
    # Phase 3A: GCC (2개)
    "jin gcc": "jin-gcc",
    "다관점": "jin-gcc",
    # Phase 3B: Cleanser (2개)
    "jin cleanser": "jin-cleanser",
    "jin deslop": "jin-cleanser",
    # Phase 3C: Deepinit (2개)
    "jin deepinit": "jin-deepinit",
    "프로젝트 분석": "jin-deepinit",
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
