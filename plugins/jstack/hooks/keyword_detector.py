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
    "jin deepinit": "deepinit",
    "deepinit": "deepinit",
    "프로젝트 분석": "deepinit",
    # Codex second opinion (commit/init 등 generic 키워드보다 먼저 매칭)
    "jin codex": "codex-side",
    # 기존 스킬 (jin 접두사 + 접두사 없음)
    "jin init": "claude-init",
    "init": "claude-init",
    "jin 초기화": "claude-init",
    "초기화": "claude-init",
    "jin commit": "commit",
    "commit": "commit",
    "jin interview": "interview",
    "interview": "interview",
    # Phase 3B: Cleanser
    "jin cleanser": "cleanser",
    "cleanser": "cleanser",
    "jin deslop": "cleanser",
    "deslop": "cleanser",
    # Phase 6: SoT (substring 충돌 방지 — bare "sot" 미등록)
    "jin sot": "sot-create",
    "sot create": "sot-create",
    "sot 생성": "sot-create",
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
