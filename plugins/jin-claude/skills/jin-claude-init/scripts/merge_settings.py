"""settings.json deep merge 스크립트.

기존 설정을 보존하면서 필수 설정만 추가/갱신한다.
멱등성 보장: 여러 번 실행해도 결과가 동일하다.
stdlib만 사용하여 외부 의존성이 없다.
"""

import json
import sys
import traceback
from pathlib import Path

SETTINGS_PATH = Path.home() / ".claude" / "settings.json"

REQUIRED_SETTINGS: dict = {
    "env": {"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"},
    "permissions": {"defaultMode": "plan"},
    "enableAllProjectMcpServers": True,
    "statusLine": {
        "type": "command",
        "command": "bash ~/.claude/statusline-command.sh",
    },
    "outputStyle": "Explanatory",
    "language": "korean",
    "skipDangerousModePermissionPrompt": True,
}


def deep_merge(base: dict, override: dict) -> dict:
    """두 딕셔너리를 재귀적으로 병합한다.

    Args:
        base: 기존 설정 딕셔너리.
        override: 덮어쓸 설정 딕셔너리.

    Returns:
        병합된 새 딕셔너리. base의 기존 키는 보존되고,
        override의 키가 추가/갱신된다.
    """
    merged = base.copy()
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def merge_settings(settings_path: Path | None = None) -> dict:
    """settings.json에 필수 설정을 병합한다.

    Args:
        settings_path: 설정 파일 경로. None이면 기본 경로 사용.

    Returns:
        병합된 설정 딕셔너리.
    """
    path = settings_path or SETTINGS_PATH

    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        print(f"[merge_settings] 기존 설정 로드: {path}")
    else:
        existing = {}
        print(f"[merge_settings] 설정 파일 없음, 새로 생성: {path}")

    merged = deep_merge(existing, REQUIRED_SETTINGS)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(merged, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"[merge_settings] 설정 병합 완료: {path}")
    return merged


def main() -> None:
    """메인 진입점."""
    try:
        settings_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
        merge_settings(settings_path)
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
