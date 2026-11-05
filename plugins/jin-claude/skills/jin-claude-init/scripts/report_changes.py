"""init 변경 추적 — 덮어쓰기 전 날짜 백업, 변경 기록, 사용자용 요약 출력.

sync_repo.py / merge_settings.py 가 파일을 쓰기 직전 track_write() 를 호출한다.
init 마지막에 이 스크립트를 실행하면 기록을 한국어 요약으로 출력하고 기록을 비운다.

    report_changes.py --snapshot settings.json → 기록 초기화 + Step 2 이전 원본 백업·기준 저장
    sync_repo.py ──┐
                   ├─ track_write() → 백업 <stem>_backup_<YYYYMMDD><ext> + REPORT_PATH 기록
    merge_settings ┘
    report_changes.py (main) → 요약 출력 → REPORT_PATH 삭제
"""

import difflib
import json
import shutil
import sys
import traceback
from datetime import date, datetime
from pathlib import Path

REPORT_PATH = Path.home() / ".claude" / ".jin-claude-init-changes.json"
BACKUP_INFIX = "_backup_"
DATE_FORMAT = "%Y%m%d"
TIME_FORMAT = "%H%M%S"
MAX_VALUE_CHARS = 60
MAX_DIFF_LINES = 10
SNAPSHOT_FLAG = "--snapshot"

NEW = "new"
CHANGED = "changed"
UNCHANGED = "unchanged"


def backup_path(path: Path, today: date | None = None) -> Path:
    """같은 디렉토리의 `<stem>_backup_<YYYYMMDD><ext>`. 확장자 없으면 `<name>_backup_<날짜>`."""
    stamp = (today or date.today()).strftime(DATE_FORMAT)
    return path.with_name(f"{path.stem}{BACKUP_INFIX}{stamp}{path.suffix}")


def backup(path: Path) -> tuple[Path, bool]:
    """path 를 날짜 백업으로 복사한다. (덮어쓸 내용을 담은 백업 경로, 이번에 복사했는지)."""
    bak = backup_path(path)
    if bak.exists() and bak.read_bytes() != path.read_bytes():
        # ponytail: 당일 백업은 유지(첫 init 전 원본). 같은 날 재실행이 덮어쓸 내용은
        # 시각 붙은 추가 백업 <stem>_backup_<YYYYMMDD>_<HHMMSS><ext> 에 보존.
        stamp = datetime.now().strftime(f"{DATE_FORMAT}_{TIME_FORMAT}")
        bak = path.with_name(f"{path.stem}{BACKUP_INFIX}{stamp}{path.suffix}")
    if bak.exists():
        return bak, False
    shutil.copy2(path, bak)
    return bak, True


def text_diff(old: str, new: str) -> dict:
    """줄 diff 요약: 추가/삭제 줄 수 + 앞쪽 MAX_DIFF_LINES 개 변경 줄."""
    # [2:] = ---/+++ 헤더 제거. 남은 줄 중 @@ 는 hunk 헤더, 내용 줄은 +/-/공백 접두.
    body = list(difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=0))[2:]
    lines = [line for line in body if line[:1] in "+-"]
    return {
        "plus": sum(line[0] == "+" for line in lines),
        "minus": sum(line[0] == "-" for line in lines),
        "lines": lines[:MAX_DIFF_LINES],
    }


def diff_dicts(old: dict, new: dict, prefix: str = "") -> dict:
    """키 단위 diff. 한쪽에만 있는 하위 트리는 펼치지 않고 그 키로 보고한다."""
    out: dict = {"added": {}, "changed": {}, "removed": {}}
    for key in old.keys() | new.keys():
        name = f"{prefix}{key}"
        if key not in old:
            out["added"][name] = new[key]
        elif key not in new:
            out["removed"][name] = old[key]
        elif isinstance(old[key], dict) and isinstance(new[key], dict):
            for kind, items in diff_dicts(old[key], new[key], f"{name}.").items():
                out[kind].update(items)
        elif old[key] != new[key]:
            out["changed"][name] = [old[key], new[key]]
    return out


def load_report() -> dict:
    """기록된 {대상 경로: {status, backup, diff}} 를 반환한다."""
    return json.loads(REPORT_PATH.read_text(encoding="utf-8")) if REPORT_PATH.exists() else {}


def _save(report: dict) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def snapshot(path: Path) -> None:
    """init 시작 시(첫 쓰기 전) 호출. 기록을 비우고 path 원본을 백업·기준(baseline)으로 저장."""
    REPORT_PATH.unlink(missing_ok=True)  # 중단된 이전 실행 기록을 이번 기준으로 오인하지 않게
    bak, created = backup(path) if path.exists() else (None, False)
    baseline = path.read_text(encoding="utf-8") if path.exists() else None
    _save(
        {
            str(path): {
                "status": UNCHANGED,
                "backup": str(bak) if bak else None,
                "diff": None,
                "created": created,
                "baseline": baseline,
            }
        }
    )


def load_baseline(path: Path) -> tuple[bool, str | None]:
    """(snapshot 여부, snapshot 시점 내용 — 파일 없었으면 None)."""
    entry = load_report().get(str(path), {})
    return "baseline" in entry, entry.get("baseline")


def track_write(dst: Path, unchanged: bool, diff: dict | None = None) -> bool:
    """dst 덮어쓰기 직전 호출. 상태를 기록하고, 기준 대비 바뀌면 True.

    snapshot 된 파일은 그 기준·백업을 재사용한다 (unchanged 는 기준 대비로 판단해 넘길 것).
    """
    report = load_report()
    snap = report.get(str(dst), {})
    if "baseline" in snap:
        existed, bak = snap["baseline"] is not None, snap["backup"]
        if unchanged and snap["created"]:
            Path(bak).unlink(missing_ok=True)  # 변경 없으면 백업도 남기지 않는다
            bak = None
    else:
        existed, bak = dst.exists(), None
        if existed and not unchanged:
            bak = str(backup(dst)[0])

    if not existed:
        status = NEW
    elif unchanged:
        status, bak = UNCHANGED, None
    else:
        status = CHANGED

    report[str(dst)] = {"status": status, "backup": bak, "diff": diff}
    _save(report)
    return status != UNCHANGED


def _short(value: object) -> str:
    text = json.dumps(value, ensure_ascii=False)
    return text if len(text) <= MAX_VALUE_CHARS else text[: MAX_VALUE_CHARS - 1] + "…"


def _home(path: str) -> str:
    return path.replace(str(Path.home()), "~", 1)


def format_report(report: dict) -> str:
    """기록을 한국어 요약 문자열로 만든다. 동일 파일은 개수만 표시."""
    if not report:
        return "[jin-claude-init] 변경 기록 없음 (sync_repo.py / merge_settings.py 미실행)"

    n = {s: sum(e["status"] == s for e in report.values()) for s in (NEW, CHANGED, UNCHANGED)}
    lines = [
        f"[jin-claude-init] 변경 요약 — 신규 {n[NEW]} · 변경 {n[CHANGED]} · 동일 {n[UNCHANGED]}"
    ]
    for status, label in ((CHANGED, "변경"), (NEW, "신규")):
        for path, entry in sorted(report.items()):
            if entry["status"] != status:
                continue
            lines.append(f"{label} {_home(path)}")
            if entry["backup"]:
                lines.append(f"  백업: {_home(entry['backup'])}")
            diff = entry["diff"] or {}
            if "lines" in diff:
                lines.append(f"  줄 +{diff['plus']} / -{diff['minus']}")
                lines += [f"    {line[:MAX_VALUE_CHARS]}" for line in diff["lines"]]
            for k, v in sorted(diff.get("added", {}).items()):
                lines.append(f"  + {k}: {_short(v)}")
            for k, (old, new) in sorted(diff.get("changed", {}).items()):
                lines.append(f"  ~ {k}: {_short(old)} → {_short(new)}")
            for k, v in sorted(diff.get("removed", {}).items()):
                lines.append(f"  - {k}: {_short(v)}")
    lines.append("전체 diff: `diff -u <백업> <원본>`")
    lines.append("되돌리기: 변경 파일은 `cp <백업> <원본>`, 신규 파일은 삭제.")
    return "\n".join(lines)


def main() -> None:
    """`--snapshot <경로>`: 기준 저장. 인자 없음: 요약을 출력하고 기록을 비운다."""
    try:
        if len(sys.argv) == 3 and sys.argv[1] == SNAPSHOT_FLAG:
            target = Path(sys.argv[2]).expanduser()
            snapshot(target)
            print(f"[report_changes] 기준 저장: {_home(str(target))}")
            return
        print(format_report(load_report()))
        # ponytail: 읽으면 소비 — 다음 init 기록과 섞이지 않게.
        REPORT_PATH.unlink(missing_ok=True)
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
