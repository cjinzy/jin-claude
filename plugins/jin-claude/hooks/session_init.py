#!/usr/bin/env python3
"""세션 시작 시 jin-claude 자동 업데이트 및 초기화를 수행한다.

SessionStart hook으로 사용된다.
기존 bash SessionStart hook을 Python으로 이전한 버전.
"""

import json
import subprocess
import sys
from pathlib import Path


def auto_update() -> None:
    """jin-claude marketplace repo를 자동 업데이트한다."""
    base = Path.home() / ".claude" / "plugins" / "marketplaces"
    if not base.exists():
        return
    for mp_dir in base.iterdir():
        jin_dir = mp_dir / "plugins" / "jin-claude"
        if jin_dir.is_dir():
            try:
                result = subprocess.run(
                    ["git", "-C", str(mp_dir), "pull", "--ff-only"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode != 0:
                    print(
                        f"[jin-claude] warning: auto-update failed for {mp_dir.name}",
                        file=sys.stderr,
                    )
            except subprocess.TimeoutExpired:
                print(
                    f"[jin-claude] warning: auto-update timeout for {mp_dir.name}",
                    file=sys.stderr,
                )
            except OSError as e:
                print(
                    f"[jin-claude] warning: auto-update error for {mp_dir.name}: {e}",
                    file=sys.stderr,
                )


def main() -> None:
    """메인 진입점."""
    auto_update()
    print(json.dumps({"result": "approve"}))


if __name__ == "__main__":
    main()
