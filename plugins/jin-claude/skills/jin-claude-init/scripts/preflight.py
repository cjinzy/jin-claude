"""jin-claude-init Pre-flight 체크 스크립트.

설치 상태를 JSON으로 출력하여, 이미 완료된 단계는 자동 스킵할 수 있도록 한다.
settings.json을 직접 읽어 각 항목의 설치 여부를 검사한다.
"""

import json
import platform
import subprocess
import sys
import traceback
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"

# merge_settings.py와 동일한 필수 설정을 import 시도, 실패 시 인라인 정의
try:
    from merge_settings import REQUIRED_SETTINGS
except ImportError:
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
        "effortLevel": "high",
    }

EXPECTED_MARKETPLACES = [
    "obsidian-skills",
    "ui-ux-pro-max-skill",
    "superpowers-marketplace",
    "context-mode",
    "superclaude",
    "harness",
    "autoresearch",
]

EXPECTED_PLUGINS = [
    "obsidian",
    "ui-ux-pro-max",
    "superpowers",
    "context-mode",
    "sc",
    "harness",
    "autoresearch",
]

HOOK_TYPES = ["UserPromptSubmit", "PreToolUse", "PostToolUse", "SessionStart"]

# context-mode는 Step 2의 플러그인이 자동 제공 (plugin:context-mode:context-mode)
MCP_SERVERS = ["context7", "serena"]


def _load_settings() -> dict:
    """settings.json을 로드한다.

    Returns:
        설정 딕셔너리. 파일이 없으면 빈 딕셔너리.
    """
    if SETTINGS_PATH.exists():
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    return {}


def check_marketplaces(settings: dict) -> dict:
    """extraKnownMarketplaces 키에서 marketplace 존재 여부를 확인한다.

    Args:
        settings: settings.json 딕셔너리.

    Returns:
        ok, total, missing 정보가 담긴 딕셔너리.
    """
    marketplaces = settings.get("extraKnownMarketplaces", [])
    mp_names = [mp if isinstance(mp, str) else mp.get("name", "") for mp in marketplaces]
    mp_str = " ".join(mp_names).lower()
    missing = [m for m in EXPECTED_MARKETPLACES if m.lower() not in mp_str]
    ok = len(EXPECTED_MARKETPLACES) - len(missing)
    return {"ok": ok, "total": len(EXPECTED_MARKETPLACES), "missing": missing}


def check_plugins(settings: dict) -> dict:
    """enabledPlugins 키에서 plugin 존재 여부를 확인한다.

    Args:
        settings: settings.json 딕셔너리.

    Returns:
        ok, total, missing 정보가 담긴 딕셔너리.
    """
    enabled = settings.get("enabledPlugins", {})
    if isinstance(enabled, dict):
        plugin_keys = list(enabled.keys())
    elif isinstance(enabled, list):
        plugin_keys = enabled
    else:
        plugin_keys = []
    plugins_str = " ".join(str(k) for k in plugin_keys).lower()
    missing = [p for p in EXPECTED_PLUGINS if p.lower() not in plugins_str]
    ok = len(EXPECTED_PLUGINS) - len(missing)
    return {"ok": ok, "total": len(EXPECTED_PLUGINS), "missing": missing}


def check_statusline() -> bool:
    """statusline-command.sh 존재 여부를 확인한다.

    Returns:
        존재하면 True.
    """
    return (CLAUDE_DIR / "statusline-command.sh").exists()


def check_settings(settings: dict) -> dict:
    """필수 설정 키가 존재하는지 비교한다.

    Args:
        settings: settings.json 딕셔너리.

    Returns:
        complete 여부와 missing 키 목록.
    """
    missing = []
    for key, value in REQUIRED_SETTINGS.items():
        if key not in settings:
            missing.append(key)
        elif isinstance(value, dict):
            for sub_key in value:
                if sub_key not in settings.get(key, {}):
                    missing.append(f"{key}.{sub_key}")
    return {"complete": len(missing) == 0, "missing": missing}


def check_venv() -> bool:
    """~/.claude/.venv/bin/python 존재 여부를 확인한다.

    Returns:
        존재하면 True.
    """
    return (CLAUDE_DIR / ".venv" / "bin" / "python").exists()


def check_timer() -> bool:
    """OS별 타이머 활성 상태를 확인한다.

    Returns:
        타이머가 활성 상태이면 True.
    """
    if platform.system() == "Darwin":
        try:
            result = subprocess.run(
                ["launchctl", "print", f"gui/{_get_uid()}/com.jin-claude.fetch-usage"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, OSError):
            return False
    else:
        try:
            result = subprocess.run(
                ["systemctl", "--user", "is-active", "jin-claude-usage.timer"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout.strip() == "active"
        except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
            return False


def _get_uid() -> int:
    """현재 사용자의 UID를 반환한다.

    Returns:
        사용자 UID.
    """
    import os

    return os.getuid()


def check_mcp_server(name: str) -> bool:
    """특정 MCP 서버가 설치되어 있는지 확인한다.

    standalone (예: "serena:") 또는 플러그인 제공 (예: "plugin:*:serena:") 모두 감지한다.

    Args:
        name: MCP 서버 이름.

    Returns:
        설치되어 있으면 True.
    """
    try:
        result = subprocess.run(
            ["claude", "mcp", "list"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        for line in result.stdout.splitlines():
            raw = line.strip().split(":")[0] if ":" in line else line.strip().split()[0] if line.strip() else ""
            # standalone: "serena: ..." 또는 plugin: "plugin:X:serena: ..."
            if line.strip().startswith(f"{name}:") or f":{name}:" in line:
                return True
        return False
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
        return False


def check_hooks(settings: dict) -> dict:
    """jin-claude hooks 설정 존재 여부를 확인한다.

    플러그인 캐시의 .claude-plugin/hooks/hooks.json을 우선 확인하고,
    없으면 글로벌 settings.json의 hooks 키를 fallback으로 확인한다.

    Args:
        settings: settings.json 딕셔너리.

    Returns:
        installed, total, missing 정보가 담긴 딕셔너리.
    """
    hooks: dict = {}

    # 플러그인 캐시에서 hooks.json 탐색
    cache_base = CLAUDE_DIR / "plugins" / "cache" / "jin-claudecode-mp" / "jin-claude"
    if cache_base.exists():
        versions = sorted(
            [d for d in cache_base.iterdir() if d.is_dir() and d.name[0].isdigit()],
            key=lambda d: d.name,
        )
        if versions:
            hooks_json = versions[-1] / ".claude-plugin" / "hooks" / "hooks.json"
            if hooks_json.exists():
                data = json.loads(hooks_json.read_text(encoding="utf-8"))
                hooks = data.get("hooks", {})

    # fallback: 글로벌 settings.json
    if not hooks:
        hooks = settings.get("hooks", {})

    missing = [h for h in HOOK_TYPES if h not in hooks]
    installed = len(HOOK_TYPES) - len(missing)
    return {"installed": installed, "total": len(HOOK_TYPES), "missing": missing}


def determine_recommendation(report: dict) -> str:
    """체크 결과에 따라 recommendation을 결정한다.

    Args:
        report: 전체 체크 결과 딕셔너리.

    Returns:
        "full", "partial", 또는 "none".
    """
    all_ok = (
        report["marketplaces"]["ok"] == report["marketplaces"]["total"]
        and report["plugins"]["ok"] == report["plugins"]["total"]
        and report["statusline"] is True
        and report["settings"]["complete"] is True
        and report["venv"] is True
        and report["timer"] is True
        and all(report.get(mcp, False) for mcp in MCP_SERVERS)
        and report["hooks"]["installed"] == report["hooks"]["total"]
    )
    if all_ok:
        return "none"

    none_ok = (
        report["marketplaces"]["ok"] == 0
        and report["plugins"]["ok"] == 0
        and report["statusline"] is False
        and report["settings"]["complete"] is False
        and report["venv"] is False
    )
    if none_ok:
        return "full"

    return "partial"


def run_preflight() -> dict:
    """Pre-flight 체크를 실행하고 결과를 반환한다.

    Returns:
        각 항목의 체크 결과가 담긴 딕셔너리.
    """
    settings = _load_settings()

    report: dict = {}
    report["marketplaces"] = check_marketplaces(settings)
    report["plugins"] = check_plugins(settings)
    report["statusline"] = check_statusline()
    report["settings"] = check_settings(settings)
    report["venv"] = check_venv()
    report["timer"] = check_timer()

    for mcp in MCP_SERVERS:
        report[mcp] = check_mcp_server(mcp)

    report["hooks"] = check_hooks(settings)
    report["recommendation"] = determine_recommendation(report)

    return report


def main() -> None:
    """메인 진입점. JSON 결과를 stdout으로 출력한다."""
    try:
        report = run_preflight()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
