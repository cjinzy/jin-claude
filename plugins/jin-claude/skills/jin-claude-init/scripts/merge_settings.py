"""settings.json deep merge 스크립트.

REQUIRED_SETTINGS(팀 필수) 는 기존 값을 덮어쓰고, DEFAULT_SETTINGS(개인 선호) 는 없을 때만 넣는다.
전역 "hooks" 는 구버전 jin-hooks/ 항목만 제거한다 (개인 hooks 보존, 현재는 plugin hooks.json 이 관리).
변경 시 settings_backup_<YYYYMMDD>.json 백업 후 쓰고, 키 단위 diff 를 report_changes 에 기록한다.
diff 기준은 `report_changes.py --snapshot` 시점(Step 2 plugin 설치 전) 원본, 없으면 현재 파일.
멱등: 이미 병합된 상태면 파일을 다시 쓰지 않는다. stdlib 만 사용.
"""

import json
import sys
import traceback
from pathlib import Path

from report_changes import diff_dicts, load_baseline, track_write

SETTINGS_PATH = Path.home() / ".claude" / "settings.json"

# 팀 공통 동작에 필요 → 항상 덮어쓴다.
REQUIRED_SETTINGS: dict = {
    "env": {"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"},
    "enableAllProjectMcpServers": True,
    "statusLine": {
        "type": "command",
        "command": "bash ~/.claude/statusline-command.sh",
    },
    "skipDangerousModePermissionPrompt": True,
}

# 개인 선호 → 키가 없을 때만 넣는다 (재 init 이 사용자 선택을 되돌리지 않게).
DEFAULT_SETTINGS: dict = {
    "permissions": {"defaultMode": "plan"},
    "outputStyle": "Explanatory",
    "language": "korean",
    "effortLevel": "high",
    "model": "opus",
    "advisorModel": "fable",
}

# 구버전(≤3.x) sync 가 settings.json 에 직접 등록한 hook 스크립트 경로.
LEGACY_HOOK_MARKER = "/.claude/jin-hooks/"


def drop_legacy_hooks(hooks: dict) -> dict:
    """LEGACY_HOOK_MARKER 를 실행하는 hook 만 제거한다. 빈 group·event 도 제거."""
    kept: dict = {}
    for event, groups in hooks.items():
        new_groups = []
        for group in groups:
            entries = [h for h in group.get("hooks", []) if LEGACY_HOOK_MARKER not in h.get("command", "")]
            if entries:
                new_groups.append({**group, "hooks": entries})
        if new_groups:
            kept[event] = new_groups
    return kept


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

    # 기본값 ← 기존 ← 필수 순으로 덮는다: 기존 값이 기본값을 이기고, 필수가 모두를 이긴다.
    merged = deep_merge(deep_merge(DEFAULT_SETTINGS, existing), REQUIRED_SETTINGS)

    if "hooks" in merged:
        hooks = drop_legacy_hooks(merged["hooks"])
        if hooks != merged["hooks"]:
            print("[merge_settings] 구버전 jin-hooks 항목 제거 (plugin hooks.json 으로 이관됨)")
        if hooks:
            merged["hooks"] = hooks
        else:
            del merged["hooks"]

    # 보고는 snapshot 기준 대비, 쓰기는 현재 파일 대비 — Step 2 변경도 보고에 포함.
    snapped, raw = load_baseline(path)
    baseline = json.loads(raw or "{}") if snapped else existing
    track_write(path, merged == baseline, diff_dicts(baseline, merged))
    if merged == existing:
        print(f"[merge_settings] 변경 없음: {path}")
        return merged

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
