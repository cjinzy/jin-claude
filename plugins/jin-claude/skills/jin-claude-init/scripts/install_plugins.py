"""Step 2: 빠진 marketplace·plugin 만 설치한다.

`claude plugin` CLI 는 settings.json 을 통째로 다시 쓰면서
  - hook group 의 비표준 키(gstack 의 `_gstack_source` 등)를 버리고,
  - 이미 있는 marketplace 를 다시 add 하면 그 항목을 새로 써서 `autoUpdate` 를 버린다.
그래서 (1) 빠진 항목만 실행하고 (marketplace 는 settings 항목 + 실제 clone 둘 다 있어야 설치됨 —
settings 만 복사된 머신은 clone 이 없어 plugin install 이 "not found in marketplace" 로 실패) (2) 실행 후 버려진 키를 실행 전 값으로 되살린다.

    settings 읽기(before) → missing 계산 → CLI 실행 → settings 읽기(after) → 버린 키 복구 → 쓰기
"""

import argparse
import json
import subprocess
import sys
import traceback
from pathlib import Path

from preflight import (
    CORE_PLUGINS,
    EXPECTED_MARKETPLACES,
    OPTIONAL_PLUGINS,
    SELECTION_FILE,
    SETTINGS_PATH,
    check_marketplaces,
    check_plugins,
    marketplaces_for,
    selected_plugins,
)

CLI_TIMEOUT_SEC = 300  # marketplace clone 이 느린 망에서도 끝나도록


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def restore_dropped_keys(before: dict, after: dict) -> list[str]:
    """CLI 가 버린 키를 after 에 되살린다 (in-place). 되살린 경로 목록을 반환.

    - hook group: 같은 event 에서 `hooks` 내용이 같은 group 끼리 비교 → 사라진 키 복구.
    - marketplace: 같은 이름 항목에서 사라진 키 복구.
    CLI 가 바꾼 값·추가한 키는 건드리지 않는다.
    """
    restored = []
    for event, groups in after.get("hooks", {}).items():
        old_groups = before.get("hooks", {}).get(event, [])
        for group in groups:
            old = next((g for g in old_groups if g.get("hooks") == group.get("hooks")), None)
            for key, value in (old or {}).items():
                if key not in group:
                    group[key] = value
                    restored.append(f"hooks.{event}.{key}")
    for name, entry in after.get("extraKnownMarketplaces", {}).items():
        old = before.get("extraKnownMarketplaces", {}).get(name, {})
        for key, value in old.items():
            if key not in entry:
                entry[key] = value
                restored.append(f"extraKnownMarketplaces.{name}.{key}")
    return restored


def _run(cmd: list[str]) -> bool:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=CLI_TIMEOUT_SEC)
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"[install_plugins] 실패: {' '.join(cmd)}: {e!r}", file=sys.stderr)
        return False
    if result.returncode != 0:
        print(f"[install_plugins] 실패: {' '.join(cmd)}: {result.stderr.strip()}", file=sys.stderr)
        return False
    print(f"[install_plugins] 완료: {' '.join(cmd[2:])}")
    return True


def install(settings_path: Path = SETTINGS_PATH, select: list[str] | None = None) -> int:
    """필수 + 선택 플러그인 중 빠진 것만 설치하고 실패 개수를 반환한다.

    Args:
        select: 이번에 고른 선택 플러그인 ID (저장됨). None 이면 저장된 선택 사용.
    """
    claude_dir = settings_path.parent
    if select is not None:
        unknown = set(select) - set(OPTIONAL_PLUGINS)
        if unknown:
            raise ValueError(f"선택 목록에 없는 plugin: {sorted(unknown)}")
        (claude_dir / SELECTION_FILE).write_text(json.dumps({"optional": select}) + "\n", encoding="utf-8")
    plugins = selected_plugins(claude_dir)
    before = _load(settings_path)
    cloned = _load(claude_dir / "plugins" / "known_marketplaces.json")
    needed = marketplaces_for(plugins)
    unlisted = set(check_marketplaces(before, needed)["missing"])
    cmds = [["claude", "plugin", "marketplace", "add", EXPECTED_MARKETPLACES[m]]
            for m in needed if m in unlisted or m not in cloned]
    cmds += [["claude", "plugin", "install", p] for p in check_plugins(before, plugins)["missing"]]
    # ponytail: 선택 해제는 제거하지 않고 알리기만 — 다른 경로로 설치했을 수 있음.
    leftover = [p for p in OPTIONAL_PLUGINS if p not in plugins and p in before.get("enabledPlugins", {})]
    if leftover:
        print(f"[install_plugins] 선택 안 함·설치돼 있음 (제거: claude plugin uninstall <id>): {', '.join(leftover)}")
    if not cmds:
        print("[install_plugins] 모두 설치됨, 스킵")
        return 0

    failures = sum(not _run(cmd) for cmd in cmds)

    after = _load(settings_path)
    restored = restore_dropped_keys(before, after)
    if restored:
        settings_path.write_text(json.dumps(after, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[install_plugins] CLI 가 지운 키 {len(restored)}개 복구: {', '.join(restored)}")
    print(f"[install_plugins] {len(cmds) - failures}/{len(cmds)} 완료")
    return failures


def main() -> None:
    """`--select a@m,b@m` (빈 값 = 선택 없음) 로 선택 저장 후 설치. 생략 시 저장된 선택."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--select", help="선택 플러그인 ID 쉼표 구분 (필수: " + ", ".join(CORE_PLUGINS) + ")")
    args = parser.parse_args()
    select = None if args.select is None else [p for p in args.select.split(",") if p]
    try:
        sys.exit(1 if install(select=select) else 0)
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
