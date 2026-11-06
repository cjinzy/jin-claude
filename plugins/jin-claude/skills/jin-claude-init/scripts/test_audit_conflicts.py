"""audit_conflicts.py 단위 테스트. tmp_path 만 사용 (실제 HOME 미접촉), subprocess 는 mock."""

import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import audit_conflicts as ac
import pytest
from merge_settings import merge_settings
from preflight import CORE_PLUGINS, OPTIONAL_PLUGINS, SELECTION_FILE, selected_plugins
from report_changes import backup_path

SECRET = "SECRET_TOKEN_123"
SERENA = "serena@claude-plugins-official"
ADHD = "i-have-adhd@i-have-adhd"
SUPERLITE = "superlite@superlite-dev"
PSTACK = "pstack@pstack-claude"
BROWSER_USE = "browser-use@claude-plugins-official"
GSTACK_GROUP = {"_gstack_source": "gstack", "hooks": [{"type": "command", "command": "true"}]}


def make_env(
    tmp_path: Path,
    plugins: dict[str, dict] | None = None,
    user_mcp: list[str] = (),
    user_skills: list[str] = (),
    settings: dict | None = None,
    disabled: list[str] = (),
) -> tuple[Path, Path]:
    """가짜 ~/.claude + ~/.claude.json 생성. plugins 값: {"mcp","mcp_wrapped","pj_mcp","pj","hooks","skills","scopes"}.

    user 외 scope 항목은 projectPath=/proj/<scope>."""
    claude_dir = tmp_path / "claude"
    claude_dir.mkdir(parents=True)
    installed: dict = {}
    enabled = {}
    for pid, spec in (plugins or {}).items():
        path = claude_dir / "plugins" / "cache" / pid
        (path / ".claude-plugin").mkdir(parents=True)
        if spec.get("mcp"):
            servers = {n: {"command": "x", "env": {"K": SECRET}} for n in spec["mcp"]}
            (path / ".mcp.json").write_text(json.dumps({"mcpServers": servers} if spec.get("mcp_wrapped") else servers))
        pj = {"name": pid.split("@")[0], **spec.get("pj", {})}
        if spec.get("pj_mcp"):
            pj["mcpServers"] = {n: {"command": SECRET} for n in spec["pj_mcp"]}
        (path / ".claude-plugin" / "plugin.json").write_text(json.dumps(pj))
        if spec.get("hooks"):
            (path / "hooks").mkdir()
            hooks = {e: [{"hooks": [{"type": "command", "command": SECRET}]}] for e in spec["hooks"]}
            (path / "hooks" / "hooks.json").write_text(json.dumps({"hooks": hooks}))
        for name in spec.get("skills", []):
            (path / "skills" / name).mkdir(parents=True)
            (path / "skills" / name / "SKILL.md").write_text("x")
        installed[pid] = [{"scope": s, "installPath": str(path), "version": "1"} | ({} if s == "user" else {"projectPath": f"/proj/{s}"})
                          for s in spec.get("scopes", ["user"])]
        enabled[pid] = pid not in disabled
    (claude_dir / "plugins").mkdir(exist_ok=True)
    (claude_dir / "plugins" / "installed_plugins.json").write_text(json.dumps({"version": 2, "plugins": installed}))
    (claude_dir / "settings.json").write_text(json.dumps({"enabledPlugins": enabled, **(settings or {})}))
    for name in user_skills:
        (claude_dir / "skills" / name).mkdir(parents=True)
        (claude_dir / "skills" / name / "SKILL.md").write_text("x")
    claude_json = tmp_path / "claude.json"
    claude_json.write_text(json.dumps({"mcpServers": {n: {"command": "uvx", "args": [SECRET], "env": {"T": SECRET}} for n in user_mcp}}))
    return claude_dir, claude_json


def ids(result: dict) -> list[str]:
    return [f["id"] for f in result["findings"]]


def finding(result: dict, fid: str) -> dict:
    return next(f for f in result["findings"] if f["id"] == fid)


def fix_ids(result: dict, fid: str) -> list[str]:
    return [x["id"] for x in finding(result, fid)["fixes"]]


def _ok(*_a, **_k) -> MagicMock:
    return MagicMock(returncode=0, stdout="", stderr="")


# --- mcp-dup ---

@pytest.mark.parametrize("spec", [{"mcp": ["serena"]}, {"mcp": ["serena"], "mcp_wrapped": True}, {"pj_mcp": ["serena"]}])
def test_mcp_dup_user_and_plugin(tmp_path: Path, spec: dict) -> None:
    result = ac.audit(*make_env(tmp_path, {SERENA: spec}, user_mcp=["serena"]))
    f = finding(result, "mcp-dup:serena")
    assert f["severity"] == "high"
    assert f["fixes"][0]["id"] == "mcp-dup:serena/remove_user_mcp:serena"
    assert f["fixes"][0]["kind"] == "remove_user_mcp"


def test_mcp_single_source_not_dup(tmp_path: Path) -> None:
    env = make_env(tmp_path, {SERENA: {"mcp": ["serena"]}}, user_mcp=["semble"])
    assert ids(ac.audit(*env)) == []


def test_disabled_plugin_not_counted(tmp_path: Path) -> None:
    """enabledPlugins false 인 plugin 은 mcp-dup · skill-shadow 대상이 아니다."""
    env = make_env(tmp_path, {SERENA: {"mcp": ["serena"]}}, user_mcp=["serena"], disabled=[SERENA])
    assert ids(ac.audit(*env)) == []
    env = make_env(tmp_path / "b", {PSTACK: {"skills": ["review"]}}, user_skills=["review"], disabled=[PSTACK])
    assert ids(ac.audit(*env)) == []


def test_plugin_with_two_scopes_not_self_dup(tmp_path: Path) -> None:
    env = make_env(tmp_path, {SERENA: {"mcp": ["serena"], "scopes": ["local", "user"]}})
    assert ids(ac.audit(*env)) == []


def test_plugin_plugin_dup_has_no_user_fix(tmp_path: Path) -> None:
    env = make_env(tmp_path, {SERENA: {"mcp": ["x"]}, PSTACK: {"mcp": ["x"]}})
    assert finding(ac.audit(*env), "mcp-dup:x")["fixes"] == []


# --- skill-shadow ---

def test_nested_gstack_copy_not_shadow(tmp_path: Path) -> None:
    env = make_env(tmp_path, {PSTACK: {"skills": ["review"]}}, user_skills=["gstack/review"])
    assert ids(ac.audit(*env)) == []


def test_top_level_user_skill_shadows_plugin(tmp_path: Path) -> None:
    env = make_env(tmp_path, {PSTACK: {"skills": ["review"]}}, user_skills=["review", "other"])
    result = ac.audit(*env)
    assert ids(result) == ["skill-shadow:review"]
    assert fix_ids(result, "skill-shadow:review") == ["skill-shadow:review/move_user_skill:review"]


# --- known ---

def test_output_style_met_and_core_not_uninstallable(tmp_path: Path) -> None:
    env = make_env(tmp_path, {ADHD: {}}, settings={"outputStyle": "Explanatory"})
    result = ac.audit(*env)
    f = finding(result, "known:output-style")
    assert f["severity"] == "medium"
    assert fix_ids(result, "known:output-style") == ["known:output-style/set_setting:outputStyle=default"]


def test_output_style_not_met(tmp_path: Path) -> None:
    assert ids(ac.audit(*make_env(tmp_path, {ADHD: {}}, settings={"outputStyle": "default"}))) == []
    assert ids(ac.audit(*make_env(tmp_path / "b", {}, settings={"outputStyle": "Explanatory"}))) == []


def test_workflow_mandates_needs_two(tmp_path: Path) -> None:

    assert ids(ac.audit(*make_env(tmp_path / "a", {SUPERLITE: {}}))) == []
    result = ac.audit(*make_env(tmp_path, {SUPERLITE: {}, PSTACK: {}}))
    assert fix_ids(result, "known:workflow-mandates") == [
        f"known:workflow-mandates/uninstall_plugin:{SUPERLITE}",
        f"known:workflow-mandates/uninstall_plugin:{PSTACK}",
    ]


def test_core_plugin_never_uninstall_candidate(tmp_path: Path) -> None:
    """known 규칙에 CORE plugin 이 걸려도 uninstall fix 는 안 나온다."""
    rules = [{**r, "plugins": [*r["plugins"], *CORE_PLUGINS], "min_plugins": 1} for r in ac.KNOWN_CONFLICTS]
    env = make_env(tmp_path, {p: {} for p in CORE_PLUGINS}, settings={"outputStyle": "Explanatory"}, user_mcp=["playwright"])
    with patch.object(ac, "KNOWN_CONFLICTS", rules):
        result = ac.audit(*env)
    targets = [x["id"].split(":", 2)[-1] for f in result["findings"] for x in f["fixes"] if x["kind"] == "uninstall_plugin"]
    assert result["findings"] and not set(targets) & set(CORE_PLUGINS)


def test_other_scope_copy_reported(tmp_path: Path) -> None:
    """uninstall 은 user scope 만 지운다 → 남는 local/project 사본을 evidence · label 로 알린다."""
    env = make_env(tmp_path, {SUPERLITE: {"scopes": ["user", "local", "project"]}, PSTACK: {}})
    f = finding(ac.audit(*env), "known:workflow-mandates")
    left = ["local scope 남음: /proj/local", "project scope 남음: /proj/project"]
    assert all(f"plugin {SUPERLITE} {x}" in f["evidence"] for x in left)
    label = next(x["label"] for x in f["fixes"] if x["id"].endswith(SUPERLITE))
    assert all(x in label for x in left)
    assert "남음" not in next(x["label"] for x in f["fixes"] if x["id"].endswith(PSTACK))


def test_browser_tools(tmp_path: Path) -> None:

    assert ids(ac.audit(*make_env(tmp_path / "a", {BROWSER_USE: {}}))) == []
    result = ac.audit(*make_env(tmp_path, {BROWSER_USE: {}}, user_mcp=["playwright"]))
    assert fix_ids(result, "known:browser-tools") == [
        f"known:browser-tools/uninstall_plugin:{BROWSER_USE}",
        "known:browser-tools/remove_user_mcp:playwright",
    ]


# --- hook-stack ---

def test_hook_stack_three_or_more(tmp_path: Path) -> None:
    three = {p: {"hooks": ["SessionStart"]} for p in ["a@m", "b@m", "c@m"]}
    result = ac.audit(*make_env(tmp_path, three))
    f = finding(result, "hook-stack:SessionStart")
    assert (f["severity"], f["fixes"]) == ("low", [])

    assert ids(ac.audit(*make_env(tmp_path / "b", {p: {"hooks": ["SessionStart"]} for p in ["a@m", "b@m"]}))) == []


def test_manifest_hook_and_skill_paths(tmp_path: Path) -> None:
    """plugin.json hooks(경로 str · inline dict) · skills(경로 str) 도 읽는다."""
    plugins = {"a@m": {"pj": {"hooks": "./hooks/custom.json"}}, "b@m": {"pj": {"hooks": {"hooks": {"SessionStart": []}}}},
               "c@m": {"hooks": ["SessionStart"]}, "d@m": {"pj": {"skills": "./.claude/skills/"}}}
    claude_dir, cj = make_env(tmp_path, plugins, user_skills=["deep"])
    a = claude_dir / "plugins" / "cache" / "a@m"
    (a / "hooks").mkdir()
    (a / "hooks" / "custom.json").write_text(json.dumps({"hooks": {"SessionStart": []}}))
    d = claude_dir / "plugins" / "cache" / "d@m" / ".claude" / "skills" / "deep"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text("x")
    result = ac.audit(claude_dir, cj)
    assert finding(result, "hook-stack:SessionStart")["evidence"] == ["plugin a@m", "plugin b@m", "plugin c@m"]
    assert finding(result, "skill-shadow:deep")["evidence"] == ["user skill deep", "plugin d@m"]


def test_malformed_plugin_file_skipped(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """제3자 plugin 의 깨진 JSON 하나가 audit 전체를 죽이지 않는다 (stdout JSON 유지, traceback 은 stderr)."""
    three = {p: {"hooks": ["SessionStart"], "mcp": ["x"]} for p in ["a@m", "b@m", "c@m", "x@m"]}
    claude_dir, cj = make_env(tmp_path, three)
    bad = claude_dir / "plugins" / "cache" / "x@m"
    for f in (bad / "hooks" / "hooks.json", bad / ".mcp.json", bad / ".claude-plugin" / "plugin.json"):
        f.write_text("{")
    assert ac.run([], claude_dir, cj) == 0
    out = capsys.readouterr()
    result = json.loads(out.out)
    assert finding(result, "hook-stack:SessionStart")["evidence"] == ["plugin a@m", "plugin b@m", "plugin c@m"]
    assert len(finding(result, "mcp-dup:x")["evidence"]) == 3
    assert "JSONDecodeError" in out.err


def test_findings_sorted_by_severity(tmp_path: Path) -> None:
    """known 규칙 순서가 severity 순이 아니어도 출력은 high → low."""
    rules = [{**r, "severity": "low"} if r["id"] == "output-style" else r for r in ac.KNOWN_CONFLICTS]
    env = make_env(tmp_path, {ADHD: {}, BROWSER_USE: {}}, user_mcp=["playwright"], settings={"outputStyle": "Explanatory"})
    with patch.object(ac, "KNOWN_CONFLICTS", rules):
        result = ac.audit(*env)
    assert [f["severity"] for f in result["findings"]] == ["medium", "low"]


# --- 출력 ---

def test_output_has_no_secret_values_and_sorted(tmp_path: Path) -> None:
    plugins = {SERENA: {"mcp": ["serena"], "hooks": ["SessionStart"]}, ADHD: {"hooks": ["SessionStart"]},
               PSTACK: {"hooks": ["SessionStart"], "skills": ["review"]}}
    env = make_env(tmp_path, plugins, user_mcp=["serena"], user_skills=["review"], settings={"outputStyle": "Explanatory"})
    result = ac.audit(*env)
    dumped = json.dumps(result)
    assert SECRET not in dumped and "uvx" not in dumped
    sev = [f["severity"] for f in result["findings"]]
    assert sev == sorted(sev, key=["high", "medium", "low"].index)
    assert result["counts"] == {"high": 2, "medium": 1, "low": 1}


# --- apply ---

def test_apply_uninstall_preserves_dropped_keys(tmp_path: Path) -> None:
    claude_dir, cj = make_env(tmp_path, {SUPERLITE: {}, PSTACK: {}}, settings={"hooks": {"Stop": [GSTACK_GROUP]}})
    settings_path = claude_dir / "settings.json"

    def cli(cmd, **_k) -> MagicMock:
        s = json.loads(settings_path.read_text())
        s["hooks"]["Stop"][0].pop("_gstack_source")
        s["enabledPlugins"].pop(cmd[-1])
        settings_path.write_text(json.dumps(s))
        return _ok()

    fid = f"known:workflow-mandates/uninstall_plugin:{PSTACK}"
    with patch("audit_conflicts.subprocess.run", side_effect=cli) as run:
        result = ac.apply([fid], claude_dir, cj)
    assert run.call_args.args[0] == ["claude", "plugin", "uninstall", PSTACK]
    after = json.loads(settings_path.read_text())
    assert after["hooks"]["Stop"] == [GSTACK_GROUP]
    assert result["applied"] == [fid] and result["failed"] == []
    assert "known:workflow-mandates" not in ids(result)  # 재검사 반영


def test_apply_cli_failure_still_restores(tmp_path: Path) -> None:
    claude_dir, cj = make_env(tmp_path, {SERENA: {"mcp": ["serena"]}}, user_mcp=["serena"], settings={"hooks": {"Stop": [GSTACK_GROUP]}})
    settings_path = claude_dir / "settings.json"

    def cli(cmd, **_k) -> MagicMock:
        s = json.loads(settings_path.read_text())
        s["hooks"]["Stop"][0].pop("_gstack_source")
        settings_path.write_text(json.dumps(s))
        return MagicMock(returncode=1, stdout="", stderr="boom")

    fid = "mcp-dup:serena/remove_user_mcp:serena"
    with patch("audit_conflicts.subprocess.run", side_effect=cli) as run:
        result = ac.apply([fid], claude_dir, cj)
    assert run.call_args.args[0] == ["claude", "mcp", "remove", "serena", "-s", "user"]
    assert result["failed"] == [{"id": fid, "error": "boom"}]
    assert SECRET in backup_path(cj).read_text()  # remove 전 ~/.claude.json 백업
    assert json.loads(settings_path.read_text())["hooks"]["Stop"] == [GSTACK_GROUP]


def test_set_setting_backs_up_and_survives_reinit(tmp_path: Path) -> None:
    claude_dir, cj = make_env(tmp_path, {ADHD: {}}, settings={"outputStyle": "Explanatory"})
    result = ac.apply(["known:output-style/set_setting:outputStyle=default"], claude_dir, cj)
    assert result["applied"] and "known:output-style" not in ids(result)
    stamp = date.today().strftime("%Y%m%d")
    backup = claude_dir / f"settings_backup_{stamp}.json"
    assert json.loads(backup.read_text())["outputStyle"] == "Explanatory"
    merge_settings(claude_dir / "settings.json")  # 재 init
    assert json.loads((claude_dir / "settings.json").read_text())["outputStyle"] == "default"


@pytest.mark.parametrize("has_file", [False, True])
def test_uninstall_optional_updates_selection(tmp_path: Path, has_file: bool) -> None:
    other, unused = [p for p in OPTIONAL_PLUGINS if p != BROWSER_USE][:2]
    claude_dir, cj = make_env(tmp_path, {BROWSER_USE: {}, other: {}}, user_mcp=["playwright"])
    if has_file:
        (claude_dir / SELECTION_FILE).write_text(json.dumps({"optional": [BROWSER_USE, other]}))
    with patch("audit_conflicts.subprocess.run", side_effect=_ok):
        ac.apply([f"known:browser-tools/uninstall_plugin:{BROWSER_USE}"], claude_dir, cj)
    chosen = selected_plugins(claude_dir)
    assert BROWSER_USE not in chosen and other in chosen  # 재 init 이 다시 설치하지 않음
    assert unused not in chosen  # 파일 없을 때 = enabled 인 OPTIONAL 만


def test_failed_uninstall_keeps_selection(tmp_path: Path) -> None:
    claude_dir, cj = make_env(tmp_path, {BROWSER_USE: {}}, user_mcp=["playwright"])
    (claude_dir / SELECTION_FILE).write_text(json.dumps({"optional": [BROWSER_USE]}))
    with patch("audit_conflicts.subprocess.run", return_value=MagicMock(returncode=1, stdout="", stderr="boom")):
        result = ac.apply([f"known:browser-tools/uninstall_plugin:{BROWSER_USE}"], claude_dir, cj)
    assert result["failed"] and BROWSER_USE in selected_plugins(claude_dir)


def test_uninstall_non_optional_writes_no_selection(tmp_path: Path) -> None:
    claude_dir, cj = make_env(tmp_path, {SUPERLITE: {}, PSTACK: {}})
    with patch("audit_conflicts.subprocess.run", side_effect=_ok):
        ac.apply([f"known:workflow-mandates/uninstall_plugin:{PSTACK}"], claude_dir, cj)
    assert not (claude_dir / SELECTION_FILE).exists()


def test_move_user_skill_and_collision(tmp_path: Path) -> None:
    claude_dir, cj = make_env(tmp_path, {PSTACK: {"skills": ["review"]}}, user_skills=["review"])
    fid = "skill-shadow:review/move_user_skill:review"
    dest_dir = claude_dir / "backups" / f"skills_backup_{date.today():%Y%m%d}"
    (dest_dir / "review").mkdir(parents=True)  # 같은 날 이전 백업
    result = ac.apply([fid], claude_dir, cj)
    assert result["applied"] == [fid] and ids(result) == []
    assert not (claude_dir / "skills" / "review").exists()
    moved = [p.name for p in dest_dir.iterdir()]
    assert len(moved) == 2 and any(n.startswith("review_") for n in moved)


def test_unknown_fix_fails_exit_1(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    claude_dir, cj = make_env(tmp_path)
    assert ac.run(["--apply", "nope/x:y"], claude_dir, cj) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["failed"][0]["id"] == "nope/x:y" and out["applied"] == []


def test_run_audit_only_prints_json(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    claude_dir, cj = make_env(tmp_path)
    with patch("audit_conflicts.subprocess.run") as run:
        assert ac.run([], claude_dir, cj) == 0
    run.assert_not_called()
    assert json.loads(capsys.readouterr().out) == {"findings": [], "counts": {"high": 0, "medium": 0, "low": 0}}
