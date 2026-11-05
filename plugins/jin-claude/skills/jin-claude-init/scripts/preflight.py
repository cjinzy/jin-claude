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

from merge_settings import DEFAULT_SETTINGS, REQUIRED_SETTINGS  # 설정 단일 출처

CLAUDE_DIR = Path.home() / ".claude"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"

# Step 2 설치 대상 단일 출처 (install_plugins.py 가 사용). ID 형식 = enabledPlugins 키 (plugin@marketplace).
# 필수: 배포 CLAUDE.md·mcp-servers.md 가 전제 → 항상 설치.
CORE_PLUGINS = [
    "context-mode@context-mode",
    "serena@claude-plugins-official",
]
# 선택: init 때 사용자가 고른다 (Step 1). 값 = 질문에 보여줄 설명.
OPTIONAL_PLUGINS: dict[str, str] = {
    "context7@claude-plugins-official": "라이브러리 최신 문서 조회 MCP (claude.ai Context7 커넥터가 있으면 불필요)",
    "pyright-lsp@claude-plugins-official": "Python 타입 검사 LSP",
    "code-simplifier@claude-plugins-official": "코드 단순화 agent",
    "ponytail@ponytail": "최소 코드 모드 — 매 세션 규칙 주입",
    "superlite@superlite-dev": "빌드 라이프사이클 (승인 1회 → 병렬 → 짧은 보고) — 매 세션 주입",
    "ui-ux-pro-max@ui-ux-pro-max-skill": "UI/UX 디자인 DB (스타일·팔레트·폰트)",
    "browser-use@claude-plugins-official": "실제 Chrome 제어 (자동화·스크린샷)",
    "html-plan@claude-community": "구현 계획을 인터랙티브 HTML 한 장으로",
    "i-have-adhd@i-have-adhd": "ADHD 친화 출력 (다음 행동 먼저, 번호 단계)",
    "typesafe@typesafe-ai": "TypeSafe System One API 스킬",
}
EXPECTED_PLUGINS = CORE_PLUGINS + list(OPTIONAL_PLUGINS)
# marketplace 이름 → GitHub 저장소. EXPECTED_PLUGINS 가 필요로 하는 것만 (test 가 정합성 검사).
EXPECTED_MARKETPLACES: dict[str, str] = {
    "context-mode": "mksglu/claude-context-mode",
    "claude-plugins-official": "anthropics/claude-plugins-official",
    "ponytail": "DietrichGebert/ponytail",
    "superlite-dev": "iha2/superlite",
    "ui-ux-pro-max-skill": "nextlevelbuilder/ui-ux-pro-max-skill",
    "claude-community": "anthropics/claude-plugins-community",
    "i-have-adhd": "ayghri/i-have-adhd",
    "typesafe-ai": "typesafe-ai/skills",
}
# 사용자 선택 저장 (~/.claude 기준). 없으면 선택 플러그인 전부 = 선택 기능 이전 init 과 동일.
SELECTION_FILE = ".jin-claude-plugins.json"


def selected_plugins(claude_dir: Path = CLAUDE_DIR) -> list[str]:
    """필수 + 저장된 선택 플러그인. 목록에서 빠진 옛 ID 는 무시."""
    path = claude_dir / SELECTION_FILE
    if not path.exists():
        return list(EXPECTED_PLUGINS)
    chosen = set(json.loads(path.read_text(encoding="utf-8")).get("optional", []))
    return CORE_PLUGINS + [p for p in OPTIONAL_PLUGINS if p in chosen]


def marketplaces_for(plugins: list[str]) -> list[str]:
    """플러그인들이 필요로 하는 marketplace (EXPECTED_MARKETPLACES 순서)."""
    needed = {p.split("@", 1)[1] for p in plugins}
    return [m for m in EXPECTED_MARKETPLACES if m in needed]


HOOK_TYPES = ["SessionStart"]

# context-mode는 Step 2의 플러그인이 자동 제공 (plugin:context-mode:context-mode)
# 현재는 standalone으로 설치할 추가 MCP 서버가 없다.
MCP_SERVERS: list[str] = []


def _load_settings() -> dict:
    """settings.json을 로드한다.

    Returns:
        설정 딕셔너리. 파일이 없으면 빈 딕셔너리.
    """
    if SETTINGS_PATH.exists():
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    return {}


def check_marketplaces(settings: dict, expected: list[str] | None = None) -> dict:
    """extraKnownMarketplaces 키에서 marketplace 존재 여부를 확인한다.

    Args:
        settings: settings.json 딕셔너리.
        expected: 확인할 marketplace. None 이면 EXPECTED_MARKETPLACES 전부.

    Returns:
        ok, total, missing 정보가 담긴 딕셔너리.
    """
    marketplaces = settings.get("extraKnownMarketplaces", {})
    names = {mp if isinstance(mp, str) else mp.get("name", "") for mp in marketplaces}  # dict → 키
    expected = list(EXPECTED_MARKETPLACES) if expected is None else expected
    missing = [m for m in expected if m not in names]
    return {"ok": len(expected) - len(missing), "total": len(expected), "missing": missing}


def check_plugins(settings: dict, expected: list[str] | None = None) -> dict:
    """enabledPlugins 키에서 plugin 존재 여부를 확인한다.

    Args:
        settings: settings.json 딕셔너리.
        expected: 확인할 plugin ID. None 이면 EXPECTED_PLUGINS 전부.

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
    expected = EXPECTED_PLUGINS if expected is None else expected
    missing = [p for p in expected if p not in set(plugin_keys)]
    return {"ok": len(expected) - len(missing), "total": len(expected), "missing": missing}


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
    for key, value in {**DEFAULT_SETTINGS, **REQUIRED_SETTINGS}.items():
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
            # standalone: "serena: ..." 또는 plugin: "plugin:X:serena: ..."
            if line.strip().startswith(f"{name}:") or f":{name}:" in line:
                return True
        return False
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
        return False


def check_hooks(settings: dict) -> dict:
    """jin-claude hooks 설정 존재 여부를 확인한다.

    플러그인 캐시 루트의 hooks/hooks.json(Claude Code 로드 위치)을 우선 확인하고,
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
            hooks_json = versions[-1] / "hooks" / "hooks.json"
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
    plugins = selected_plugins()
    report["marketplaces"] = check_marketplaces(settings, marketplaces_for(plugins))
    report["plugins"] = check_plugins(settings, plugins)
    # Step 1 플러그인 선택 질문 재료. selected = 저장된 선택(없으면 전부) → 질문 기본값.
    report["optional_plugins"] = {p: {"description": d, "selected": p in plugins} for p, d in OPTIONAL_PLUGINS.items()}
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
