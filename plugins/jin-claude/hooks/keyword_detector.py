#!/usr/bin/env python3
"""사용자 프롬프트에서 magic keyword를 감지하여 스킬을 자동 호출한다.

UserPromptSubmit hook으로 사용된다.
stdin으로 JSON 이벤트를 받아 keyword 매칭 시 block + reason을 반환한다.
"""

import json
import sys

KEYWORDS = {
    "jin init": "jin-claude-init",
    "jin 초기화": "jin-claude-init",
    "jin commit": "jin-commit",
    "jin interview": "jin-interview",
    "jin swe": "jin-swe-fix",
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
