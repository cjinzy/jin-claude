"""설치 환경 충돌 audit — 기본 읽기 전용. `--apply <fix-id>...` 로 고른 해결안만 실행.

    수집 ─ installed_plugins.json + settings enabledPlugins(true) → 활성 plugin 경로
       │   plugin: hooks/hooks.json + plugin.json hooks · .mcp.json + plugin.json mcpServers
       │           · <skills 경로|skills>/<name>/SKILL.md   (깨진 plugin 파일 → stderr traceback, 건너뜀)
       │   user: ~/.claude.json mcpServers(이름만) · ~/.claude/skills/<name>/SKILL.md (1단계만 로드)
       ▼
    검사 ─ mcp-dup (high) · skill-shadow (high) · known:<rule> (medium) · hook-stack (low, 정보)
       ▼
    stdout JSON {"findings": [...], "counts": {...}}  (high → low)
       ▼ --apply
    fix 실행 ─ CLI(uninstall_plugin·remove_user_mcp): settings before → try 실행 → finally restore_dropped_keys
             ─ remove_user_mcp: 실행 전 ~/.claude.json backup / uninstall: user scope 만 (다른 scope 사본은 label 로 안내)
             ─ set_setting: report_changes.backup 후 쓰기 / move_user_skill: backups/skills_backup_<날짜>/
       ▼
    재검사 JSON + "applied" + "failed"  (실패 1개 이상 → exit 1)

evidence 는 이름·출처만 — MCP command/args/env, hook command 는 비밀이 있을 수 있어 출력 금지.
fix id = "<finding-id>/<kind>:<target>". stdlib 만 사용.
"""

import argparse
import json
import shutil
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path

from install_plugins import CLI_TIMEOUT_SEC, restore_dropped_keys, save_selection
from preflight import CLAUDE_DIR, CORE_PLUGINS, OPTIONAL_PLUGINS, SELECTION_FILE
from report_changes import backup

CLAUDE_JSON = Path.home() / ".claude.json"

HIGH, MEDIUM, LOW = "high", "medium", "low"
SEVERITY_ORDER = (HIGH, MEDIUM, LOW)

UNINSTALL_PLUGIN = "uninstall_plugin"
REMOVE_USER_MCP = "remove_user_mcp"
MOVE_USER_SKILL = "move_user_skill"
SET_SETTING = "set_setting"

USER_MCP_SOURCE = "user MCP"
USER_SCOPE = "user"
# additionalContext 를 넣을 수 있는 event — 여기에 plugin hook 이 쌓이면 매 세션 지시가 누적된다.
CONTEXT_EVENTS = ("SessionStart", "UserPromptSubmit", "SubagentStart")
HOOK_STACK_MIN = 3

# 알려진 충돌 규칙. 조건: 활성 plugin 중 `plugins` 가 min_plugins 개 이상 + `setting` 일치 + `user_mcp` 전부 존재.
# fix: 걸린 plugin uninstall (CORE 제외) · 걸린 user MCP 제거 · `fix_setting` 설정.
KNOWN_CONFLICTS: list[dict] = [
    {
        "id": "output-style",
        "severity": MEDIUM,
        "summary": "outputStyle Explanatory 가 i-have-adhd 출력 형식과 충돌",
        "plugins": ["i-have-adhd@i-have-adhd"],
        "min_plugins": 1,
        "setting": ("outputStyle", "Explanatory"),
        # 키 제거 금지 — merge_settings 가 "없을 때만" Explanatory 를 다시 넣는다.
        "fix_setting": ("outputStyle", "default"),
        "user_mcp": [],
    },
    {
        "id": "workflow-mandates",
        "severity": MEDIUM,
        "summary": "작업 방식을 강제하는 워크플로 plugin 이 2개 이상",
        "plugins": ["superpowers@claude-plugins-official", "pstack@pstack-claude", "agent-skills@addy-agent-skills"],
        "min_plugins": 2,
        "setting": None,
        "fix_setting": None,
        "user_mcp": [],
    },
    {
        "id": "browser-tools",
        "severity": MEDIUM,
        "summary": "브라우저 제어 도구 중복 (browser-use plugin + Playwright MCP)",
        "plugins": ["browser-use@claude-plugins-official"],
        "min_plugins": 1,
        "setting": None,
        "fix_setting": None,
        "user_mcp": ["playwright"],
    },
]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _load_plugin_file(path: Path) -> dict:
    """제3자 plugin 파일용 — 깨져도 audit 전체(stdout JSON)를 죽이지 않게 traceback 만 stderr 에 남기고 {}."""
    try:
        data = _load(path)
    except (OSError, ValueError):  # ValueError ⊃ JSONDecodeError · UnicodeDecodeError
        traceback.print_exc()
        return {}
    return data if isinstance(data, dict) else {}


def _manifest(path: Path) -> dict:
    return _load_plugin_file(path / ".claude-plugin" / "plugin.json")


def _as_list(value) -> list:
    return value if isinstance(value, list) else [value] if value else []


def _write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _installed(claude_dir: Path) -> dict[str, list[dict]]:
    return _load(claude_dir / "plugins" / "installed_plugins.json").get("plugins", {})


def other_scope_copies(claude_dir: Path) -> dict[str, list[str]]:
    """plugin id → user 외 scope 사본 ["local scope 남음: <projectPath>", ...]. uninstall(user scope)이 못 지우는 것."""
    out: dict[str, list[str]] = {}
    for pid, entries in _installed(claude_dir).items():
        for e in entries:
            if e.get("scope") != USER_SCOPE and e.get("projectPath"):
                out.setdefault(pid, []).append(f"{e['scope']} scope 남음: {e['projectPath']}")
    return out


def active_plugins(claude_dir: Path, settings: dict) -> dict[str, Path]:
    """enabledPlugins 가 true 이고 설치된 plugin → installPath (user scope 우선)."""
    installed = _installed(claude_dir)
    out = {}
    for pid, enabled in settings.get("enabledPlugins", {}).items():
        entries = installed.get(pid) or []
        if enabled is not True or not entries:
            continue
        entry = next((e for e in entries if e.get("scope") == USER_SCOPE), entries[0])
        out[pid] = Path(entry["installPath"])
    return out


def plugin_mcp_names(path: Path) -> set[str]:
    """.mcp.json (mcpServers 래퍼 있거나 없거나) + plugin.json 의 dict 형 mcpServers."""
    mcp = _load_plugin_file(path / ".mcp.json")
    names = set(mcp.get("mcpServers", mcp))
    # ponytail: plugin.json mcpServers 가 파일 경로(str)면 무시 — 그런 plugin 이 생기면 경로 로드 추가.
    pj_servers = _manifest(path).get("mcpServers")
    if isinstance(pj_servers, dict):
        names |= set(pj_servers)
    return names


def plugin_hook_events(path: Path) -> set[str]:
    """hooks/hooks.json(항상 로드) + plugin.json hooks (경로 str · inline dict · 그 list)."""
    events: set[str] = set()
    for src in ["hooks/hooks.json", *_as_list(_manifest(path).get("hooks"))]:
        cfg = _load_plugin_file(path / src) if isinstance(src, str) else src
        if isinstance(cfg, dict):
            events |= set(cfg["hooks"] if isinstance(cfg.get("hooks"), dict) else cfg)
    return events


def plugin_skill_dirs(path: Path) -> list[Path]:
    """plugin.json skills(str·list) 가 있으면 기본 skills/ 대신 그 경로들."""
    # ponytail: 디렉토리 이름 = skill 이름 가정. "./" 처럼 frontmatter name 으로 정해지는 plugin 은 놓침.
    return [path / d for d in (_as_list(_manifest(path).get("skills")) or ["skills"]) if isinstance(d, str)]


def _skill_names(skills_dir: Path) -> set[str]:
    """1단계 <name>/SKILL.md 만 — 중첩 사본(gstack/<x>/SKILL.md)은 로드되지 않으므로 제외."""
    return {p.parent.name for p in skills_dir.glob("*/SKILL.md")}


def _fix(finding_id: str, kind: str, target: str, label: str, value: str | None = None) -> dict:
    fid = f"{finding_id}/{kind}:{target}" if value is None else f"{finding_id}/{kind}:{target}={value}"
    return {"id": fid, "kind": kind, "label": label, "target": target, "value": value}


def _finding(fid: str, severity: str, summary: str, evidence: list[str], fixes: list[dict]) -> dict:
    return {"id": fid, "severity": severity, "summary": summary, "evidence": evidence, "fixes": fixes}


def _check_mcp_dup(plugins: dict[str, Path], user_mcp: set[str]) -> list[dict]:
    sources: dict[str, list[str]] = {name: [USER_MCP_SOURCE] for name in user_mcp}
    for pid, path in plugins.items():  # plugin id 당 1회 → scope 2개인 plugin 이 자기 자신과 중복되지 않음
        for name in plugin_mcp_names(path):
            sources.setdefault(name, []).append(f"plugin {pid}")
    out = []
    for name, src in sorted(sources.items()):
        if len(src) < 2:
            continue
        fid = f"mcp-dup:{name}"
        fixes = [_fix(fid, REMOVE_USER_MCP, name, f"user MCP {name} 제거 (plugin 판 사용)")] if USER_MCP_SOURCE in src else []
        out.append(_finding(fid, HIGH, f"MCP {name} 가 {len(src)}곳에 등록 — 같은 도구 중복", src, fixes))
    return out


def _check_skill_shadow(plugins: dict[str, Path], user_skills: set[str]) -> list[dict]:
    out = []
    for name in sorted(user_skills):
        owners = [pid for pid, path in plugins.items() if any((d / name / "SKILL.md").exists() for d in plugin_skill_dirs(path))]
        if owners:
            fid = f"skill-shadow:{name}"
            fixes = [_fix(fid, MOVE_USER_SKILL, name, f"user skill {name} 을 backups 로 이동")]
            evidence = [f"user skill {name}"] + [f"plugin {pid}" for pid in owners]
            out.append(_finding(fid, HIGH, f"user skill {name} 이 plugin skill 을 가림", evidence, fixes))
    return out


def _check_known(plugins: dict[str, Path], user_mcp: set[str], settings: dict, copies: dict[str, list[str]]) -> list[dict]:
    out = []
    for rule in KNOWN_CONFLICTS:
        hit = [p for p in rule["plugins"] if p in plugins]
        mcps = rule["user_mcp"]
        setting = rule["setting"]
        if len(hit) < rule["min_plugins"] or not set(mcps) <= user_mcp:
            continue
        if setting and settings.get(setting[0]) != setting[1]:
            continue
        fid = f"known:{rule['id']}"
        # 다른 scope 사본은 cwd 가 달라 여기서 못 지움 → label 로 해당 프로젝트에서 직접 제거하게 안내.
        fixes = [_fix(fid, UNINSTALL_PLUGIN, p, " · ".join([f"plugin {p} 제거 (user scope)", *copies.get(p, [])]))
                 for p in hit if p not in CORE_PLUGINS]
        fixes += [_fix(fid, REMOVE_USER_MCP, m, f"user MCP {m} 제거") for m in mcps]
        if rule["fix_setting"]:
            key, value = rule["fix_setting"]
            fixes.append(_fix(fid, SET_SETTING, key, f"settings {key} 를 \"{value}\" 로", value))
        evidence = [f"plugin {p}" for p in hit] + [f"plugin {p} {c}" for p in hit for c in copies.get(p, [])]
        evidence += [f"{USER_MCP_SOURCE} {m}" for m in mcps]
        if setting:
            evidence.append(f"settings {setting[0]}")
        out.append(_finding(fid, rule["severity"], rule["summary"], evidence, fixes))
    return out


def _check_hook_stack(plugins: dict[str, Path], settings: dict) -> list[dict]:
    out = []
    for event in CONTEXT_EVENTS:
        users = [pid for pid, path in plugins.items() if event in plugin_hook_events(path)]
        if len(users) < HOOK_STACK_MIN:
            continue
        evidence = [f"plugin {pid}" for pid in users]
        own = len(settings.get("hooks", {}).get(event, []))
        if own:
            evidence.append(f"settings hooks {own}개")
        out.append(_finding(f"hook-stack:{event}", LOW, f"{event} 에 plugin {len(users)}개가 컨텍스트 주입", evidence, []))
    return out


def _findings(claude_dir: Path, claude_json: Path) -> tuple[list[dict], dict]:
    """(내부 fix 필드 포함 findings, settings)."""
    settings = _load(claude_dir / "settings.json")
    plugins = active_plugins(claude_dir, settings)
    user_mcp = set(_load(claude_json).get("mcpServers", {}))  # 키만 — 값엔 비밀
    findings = (_check_mcp_dup(plugins, user_mcp) + _check_skill_shadow(plugins, _skill_names(claude_dir / "skills"))
                + _check_known(plugins, user_mcp, settings, other_scope_copies(claude_dir)) + _check_hook_stack(plugins, settings))
    findings.sort(key=lambda f: SEVERITY_ORDER.index(f["severity"]))
    return findings, settings


def audit(claude_dir: Path = CLAUDE_DIR, claude_json: Path = CLAUDE_JSON) -> dict:
    findings, _ = _findings(claude_dir, claude_json)
    public = [{**f, "fixes": [{k: x[k] for k in ("id", "kind", "label")} for x in f["fixes"]]} for f in findings]
    return {"findings": public, "counts": {s: sum(f["severity"] == s for f in findings) for s in SEVERITY_ORDER}}


def _cli(cmd: list[str]) -> str | None:
    """CLI 실행. 성공이면 None, 실패면 오류 문자열."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=CLI_TIMEOUT_SEC)
    except (OSError, subprocess.TimeoutExpired) as e:
        return repr(e)
    return None if result.returncode == 0 else (result.stderr.strip() or f"exit {result.returncode}")


def _drop_from_selection(claude_dir: Path, settings: dict, pid: str) -> None:
    """재 init 이 다시 설치하지 않게 선택에서 뺀다. 선택 파일 없으면 현재 enabled 인 OPTIONAL 기준."""
    path = claude_dir / SELECTION_FILE
    enabled = settings.get("enabledPlugins", {})
    current = _load(path).get("optional", []) if path.exists() else [p for p in OPTIONAL_PLUGINS if enabled.get(p) is True]
    save_selection(claude_dir, [p for p in current if p in OPTIONAL_PLUGINS and p != pid])


def _move_user_skill(claude_dir: Path, name: str) -> None:
    # ponytail: hooks/session_init.retire_legacy_skills 의 경로 규칙 5줄 중복 — hooks/ ↔ scripts/ 교차 import 는
    # plugin 캐시 경로상 깨지기 쉬움. 규칙이 바뀌면 두 곳 모두 수정.
    src = claude_dir / "skills" / name
    now = datetime.now()
    dest = claude_dir / "backups" / f"skills_backup_{now:%Y%m%d}" / name
    if dest.exists():
        dest = dest.with_name(f"{name}_{now:%H%M%S%f}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), dest)


def _execute(fix: dict, claude_dir: Path, claude_json: Path) -> str | None:
    """fix 1개 실행. 성공 None, 실패 오류 문자열."""
    settings_path = claude_dir / "settings.json"
    kind, target = fix["kind"], fix["target"]
    if kind == SET_SETTING:
        settings = _load(settings_path)
        if settings_path.exists():
            backup(settings_path)
        settings[target] = fix["value"]
        _write(settings_path, settings)
        return None
    if kind == MOVE_USER_SKILL:
        _move_user_skill(claude_dir, target)
        return None
    # CLI 는 settings.json 을 다시 쓰며 비표준 키를 버린다 → 실패해도 복구.
    cmd = ["claude", "plugin", "uninstall", target] if kind == UNINSTALL_PLUGIN else ["claude", "mcp", "remove", target, "-s", USER_SCOPE]
    # uninstall 은 기본 user scope 만 — 다른 scope 사본은 그 프로젝트에서 계속 활성 (label 에 안내).
    if kind == REMOVE_USER_MCP and claude_json.exists():
        backup(claude_json)  # remove 는 command/args/env 설정째 지운다 — 되돌릴 사본
    before = _load(settings_path)
    try:
        error = _cli(cmd)
    finally:
        after = _load(settings_path)
        if restore_dropped_keys(before, after):
            _write(settings_path, after)
    if error is None and kind == UNINSTALL_PLUGIN and target in OPTIONAL_PLUGINS:
        _drop_from_selection(claude_dir, before, target)
    return error


def apply(fix_ids: list[str], claude_dir: Path = CLAUDE_DIR, claude_json: Path = CLAUDE_JSON) -> dict:
    """고른 fix 만 실행 → 재검사 결과 + applied/failed."""
    findings, _ = _findings(claude_dir, claude_json)
    fixes = {x["id"]: x for f in findings for x in f["fixes"]}  # 파싱 대신 조회 — id 에 : @ = 가 섞임
    applied, failed = [], []
    for fid in fix_ids:
        fix = fixes.get(fid)
        if fix is None:
            failed.append({"id": fid, "error": "현재 findings 에 없는 fix id"})
            continue
        try:
            error = _execute(fix, claude_dir, claude_json)
        except OSError as e:
            traceback.print_exc()
            error = repr(e)
        if error is None:
            applied.append(fid)
        else:
            failed.append({"id": fid, "error": error})
    return {**audit(claude_dir, claude_json), "applied": applied, "failed": failed}


def run(argv: list[str], claude_dir: Path = CLAUDE_DIR, claude_json: Path = CLAUDE_JSON) -> int:
    parser = argparse.ArgumentParser(description="설치 환경 충돌 audit")
    parser.add_argument("--apply", nargs="+", metavar="FIX_ID", help="실행할 fix id")
    args = parser.parse_args(argv)
    result = apply(args.apply, claude_dir, claude_json) if args.apply else audit(claude_dir, claude_json)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result.get("failed") else 0


def main() -> None:
    try:
        sys.exit(run(sys.argv[1:]))
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
