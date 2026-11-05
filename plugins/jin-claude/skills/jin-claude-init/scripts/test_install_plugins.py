"""install_plugins.py 단위 테스트."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from install_plugins import install, restore_dropped_keys
import pytest

from preflight import CORE_PLUGINS, EXPECTED_MARKETPLACES, EXPECTED_PLUGINS, OPTIONAL_PLUGINS, SELECTION_FILE

GSTACK_GROUP = {"_gstack_source": "gstack", "hooks": [{"type": "command", "command": "true"}]}


def _full_settings() -> dict:
    return {
        "extraKnownMarketplaces": {n: {"source": {"source": "github", "repo": r}} for n, r in EXPECTED_MARKETPLACES.items()},
        "enabledPlugins": {p: True for p in EXPECTED_PLUGINS},
    }


def _write(path: Path, settings: dict, known: list[str] | None = None) -> None:
    """settings.json + 실제 clone 목록(plugins/known_marketplaces.json) 기록. known 기본 = 전부."""
    path.write_text(json.dumps(settings))
    known_path = path.parent / "plugins" / "known_marketplaces.json"
    known_path.parent.mkdir(exist_ok=True)
    known_path.write_text(json.dumps({n: {} for n in (EXPECTED_MARKETPLACES if known is None else known)}))


def _ok(*_a, **_k) -> MagicMock:
    return MagicMock(returncode=0, stdout="", stderr="")


@patch("install_plugins.subprocess.run", side_effect=_ok)
def test_nothing_missing_runs_no_cli(mock_run: MagicMock, tmp_path: Path) -> None:
    """모두 설치돼 있으면 CLI 를 호출하지 않는다 (재 add 가 autoUpdate 를 지움)."""
    path = tmp_path / "settings.json"
    _write(path, _full_settings())
    assert install(path) == 0
    mock_run.assert_not_called()


@patch("install_plugins.subprocess.run", side_effect=_ok)
def test_runs_only_missing(mock_run: MagicMock, tmp_path: Path) -> None:
    settings = _full_settings()
    mp = next(iter(EXPECTED_MARKETPLACES))
    del settings["extraKnownMarketplaces"][mp]
    del settings["enabledPlugins"][EXPECTED_PLUGINS[0]]
    path = tmp_path / "settings.json"
    _write(path, settings)

    assert install(path) == 0
    cmds = [c.args[0] for c in mock_run.call_args_list]
    assert cmds == [
        ["claude", "plugin", "marketplace", "add", EXPECTED_MARKETPLACES[mp]],
        ["claude", "plugin", "install", EXPECTED_PLUGINS[0]],
    ]


@patch("install_plugins.subprocess.run", side_effect=_ok)
def test_adds_marketplace_listed_but_not_cloned(mock_run: MagicMock, tmp_path: Path) -> None:
    """settings 에만 있고 clone 이 없으면(설정 복사 등) add 해야 plugin 설치가 된다."""
    mp = next(iter(EXPECTED_MARKETPLACES))
    path = tmp_path / "settings.json"
    _write(path, _full_settings(), known=[m for m in EXPECTED_MARKETPLACES if m != mp])
    install(path)
    assert [c.args[0] for c in mock_run.call_args_list] == [["claude", "plugin", "marketplace", "add", EXPECTED_MARKETPLACES[mp]]]


def test_failure_counted(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{}")
    with patch("install_plugins.subprocess.run", return_value=MagicMock(returncode=1, stdout="", stderr="x")):
        assert install(path) == len(EXPECTED_MARKETPLACES) + len(EXPECTED_PLUGINS)


def test_restores_keys_cli_dropped(tmp_path: Path) -> None:
    """CLI 가 settings.json 을 다시 쓰며 버린 hook group·marketplace 키를 되살린다."""
    settings = _full_settings()
    mp = next(iter(EXPECTED_MARKETPLACES))
    settings["extraKnownMarketplaces"][mp]["autoUpdate"] = True
    settings["hooks"] = {"Stop": [GSTACK_GROUP]}
    del settings["enabledPlugins"][EXPECTED_PLUGINS[0]]
    path = tmp_path / "settings.json"
    _write(path, settings)

    def cli_rewrite(*_a, **_k) -> MagicMock:
        s = json.loads(path.read_text())
        s["hooks"]["Stop"][0].pop("_gstack_source")
        s["extraKnownMarketplaces"][mp].pop("autoUpdate")
        s["enabledPlugins"][EXPECTED_PLUGINS[0]] = True
        path.write_text(json.dumps(s))
        return _ok()

    with patch("install_plugins.subprocess.run", side_effect=cli_rewrite):
        install(path)
    after = json.loads(path.read_text())
    assert after["hooks"]["Stop"] == [GSTACK_GROUP]
    assert after["extraKnownMarketplaces"][mp]["autoUpdate"] is True
    assert after["enabledPlugins"][EXPECTED_PLUGINS[0]] is True  # CLI 의 정상 변경은 유지


def test_restore_ignores_changed_groups() -> None:
    """hook 내용이 달라진 group 에는 이전 키를 붙이지 않는다."""
    before = {"hooks": {"Stop": [GSTACK_GROUP]}}
    after = {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "other"}]}]}}
    assert restore_dropped_keys(before, after) == []
    assert "_gstack_source" not in after["hooks"]["Stop"][0]


def _installs(mock_run: MagicMock) -> list[str]:
    return [c.args[0][-1] for c in mock_run.call_args_list if c.args[0][2] == "install"]


def test_plugin_lists_consistent() -> None:
    """marketplace 목록 = 플러그인들이 필요로 하는 marketplace 전부, 그 이상도 이하도 아님."""
    assert {p.split("@", 1)[1] for p in EXPECTED_PLUGINS} == set(EXPECTED_MARKETPLACES)
    assert not set(CORE_PLUGINS) & set(OPTIONAL_PLUGINS)


@patch("install_plugins.subprocess.run", side_effect=_ok)
def test_select_installs_core_plus_selected_and_saves(mock_run: MagicMock, tmp_path: Path) -> None:
    pick = next(iter(OPTIONAL_PLUGINS))
    path = tmp_path / "settings.json"
    _write(path, {}, known=[])
    install(path, select=[pick])
    assert _installs(mock_run) == CORE_PLUGINS + [pick]
    needed = {p.split("@", 1)[1] for p in CORE_PLUGINS + [pick]}
    added = [c.args[0][-1] for c in mock_run.call_args_list if c.args[0][2] == "marketplace"]
    assert added == [EXPECTED_MARKETPLACES[m] for m in EXPECTED_MARKETPLACES if m in needed]
    assert json.loads((tmp_path / SELECTION_FILE).read_text()) == {"optional": [pick]}


@patch("install_plugins.subprocess.run", side_effect=_ok)
def test_rerun_uses_saved_selection(mock_run: MagicMock, tmp_path: Path) -> None:
    """선택 안 한 플러그인은 재실행 때도 설치하지 않는다."""
    path = tmp_path / "settings.json"
    _write(path, {})
    (tmp_path / SELECTION_FILE).write_text(json.dumps({"optional": []}))
    install(path)
    assert _installs(mock_run) == CORE_PLUGINS


def test_unknown_selection_rejected(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    _write(path, {})
    with pytest.raises(ValueError):
        install(path, select=["nope@nowhere"])
