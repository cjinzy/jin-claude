"""merge_settings.py 단위 테스트."""

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

import report_changes
from merge_settings import DEFAULT_SETTINGS, REQUIRED_SETTINGS, deep_merge, merge_settings


class TestDeepMerge(unittest.TestCase):
    """deep_merge 함수 테스트."""

    def test_empty_base(self) -> None:
        """빈 base에 override를 병합하면 override와 동일해야 한다."""
        result = deep_merge({}, {"a": 1})
        self.assertEqual(result, {"a": 1})

    def test_empty_override(self) -> None:
        """빈 override면 base가 그대로 반환되어야 한다."""
        result = deep_merge({"a": 1}, {})
        self.assertEqual(result, {"a": 1})

    def test_preserves_existing_keys(self) -> None:
        """base의 기존 키가 override에 없으면 보존되어야 한다."""
        base = {"existing": "value", "keep": True}
        override = {"new": "added"}
        result = deep_merge(base, override)
        self.assertEqual(result["existing"], "value")
        self.assertEqual(result["keep"], True)
        self.assertEqual(result["new"], "added")

    def test_nested_merge(self) -> None:
        """중첩 딕셔너리가 재귀적으로 병합되어야 한다."""
        base = {"env": {"EXISTING_VAR": "keep"}}
        override = {"env": {"NEW_VAR": "1"}}
        result = deep_merge(base, override)
        self.assertEqual(result["env"]["EXISTING_VAR"], "keep")
        self.assertEqual(result["env"]["NEW_VAR"], "1")

    def test_override_scalar(self) -> None:
        """스칼라 값은 override로 덮어써야 한다."""
        base = {"language": "english"}
        override = {"language": "korean"}
        result = deep_merge(base, override)
        self.assertEqual(result["language"], "korean")

    def test_does_not_mutate_base(self) -> None:
        """원본 base 딕셔너리를 변경하지 않아야 한다."""
        base = {"a": {"b": 1}}
        override = {"a": {"c": 2}}
        deep_merge(base, override)
        self.assertNotIn("c", base["a"])


class TestMergeSettings(unittest.TestCase):
    """merge_settings 함수 테스트."""

    def test_creates_new_file(self) -> None:
        """settings.json이 없을 때 새로 생성해야 한다."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "settings.json"
            result = merge_settings(path)

            self.assertTrue(path.exists())
            saved = json.loads(path.read_text())
            self.assertEqual(saved["language"], "korean")
            self.assertEqual(result["language"], "korean")

    def test_preserves_existing_settings(self) -> None:
        """기존 설정을 보존하면서 필수 설정을 추가해야 한다."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "settings.json"
            existing = {
                "enabledPlugins": {"my-plugin": True},
                "customKey": "custom-value",
            }
            path.write_text(json.dumps(existing))

            result = merge_settings(path)

            self.assertEqual(result["enabledPlugins"], {"my-plugin": True})
            self.assertEqual(result["customKey"], "custom-value")
            self.assertEqual(result["language"], "korean")

    def test_idempotent(self) -> None:
        """여러 번 실행해도 결과가 동일해야 한다."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "settings.json"

            merge_settings(path)
            first = json.loads(path.read_text())

            merge_settings(path)
            second = json.loads(path.read_text())

            self.assertEqual(first, second)

    def test_nested_env_merge(self) -> None:
        """env 안의 기존 변수를 보존하면서 필수 변수를 추가해야 한다."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "settings.json"
            existing = {"env": {"MY_VAR": "keep"}}
            path.write_text(json.dumps(existing))

            result = merge_settings(path)

            self.assertEqual(result["env"]["MY_VAR"], "keep")
            self.assertEqual(
                result["env"]["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"], "1"
            )

    def test_all_required_settings_present(self) -> None:
        """모든 필수 설정이 결과에 포함되어야 한다."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "settings.json"
            result = merge_settings(path)

            for key, value in {**DEFAULT_SETTINGS, **REQUIRED_SETTINGS}.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        self.assertEqual(result[key][sub_key], sub_value)
                else:
                    self.assertEqual(result[key], value)


LEGACY_HOOK = {"hooks": [{"type": "command", "command": "python3 $HOME/.claude/jin-hooks/session_init.py"}]}
PERSONAL_HOOK = {"hooks": [{"type": "command", "command": "echo mine"}]}


def test_forces_required_keys(tmp_path: Path) -> None:
    """팀 필수 키는 기존 값을 덮어쓴다."""
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"enableAllProjectMcpServers": False}))
    assert merge_settings(path)["enableAllProjectMcpServers"] is True


def test_preserves_user_preferences(tmp_path: Path) -> None:
    """개인 선호 키는 기존 값을 유지하고, 없을 때만 기본값을 넣는다."""
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"model": "sonnet", "permissions": {"defaultMode": "auto"}}))
    result = merge_settings(path)
    assert result["model"] == "sonnet"
    assert result["permissions"]["defaultMode"] == "auto"
    assert result["language"] == DEFAULT_SETTINGS["language"]


def test_keeps_personal_hooks_drops_legacy(tmp_path: Path) -> None:
    """jin-hooks/ 구버전 항목만 제거하고 개인 hooks 는 보존. 비면 이벤트·키 삭제."""
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"hooks": {"Stop": [PERSONAL_HOOK, LEGACY_HOOK], "SessionStart": [LEGACY_HOOK]}}))
    assert merge_settings(path)["hooks"] == {"Stop": [PERSONAL_HOOK]}

    path.write_text(json.dumps({"hooks": {"SessionStart": [LEGACY_HOOK]}}))
    assert "hooks" not in merge_settings(path)


def test_changed_settings_backed_up_with_diff(tmp_path: Path) -> None:
    """변경 시 settings_backup_<날짜>.json 백업 + 키 단위 diff(구버전 hooks 삭제 포함) 기록."""
    path = tmp_path / "settings.json"
    original = {"enableAllProjectMcpServers": False, "hooks": {"Stop": [LEGACY_HOOK]}, "customKey": 1}
    path.write_text(json.dumps(original))

    merge_settings(path)

    bak = report_changes.backup_path(path)
    assert bak.name == f"settings_backup_{date.today():%Y%m%d}.json"
    assert json.loads(bak.read_text()) == original
    entry = report_changes.load_report()[str(path)]
    assert entry["status"] == report_changes.CHANGED
    assert entry["backup"] == str(bak)
    assert entry["diff"]["changed"]["enableAllProjectMcpServers"] == [False, True]
    assert entry["diff"]["removed"] == {"hooks": {"Stop": [LEGACY_HOOK]}}
    assert "language" in entry["diff"]["added"]
    assert "customKey" not in entry["diff"]["added"]


def test_unchanged_settings_not_rewritten(tmp_path: Path) -> None:
    """이미 병합된 설정이면 백업·쓰기 없이 unchanged 로 기록."""
    path = tmp_path / "settings.json"
    merge_settings(path)
    mtime = path.stat().st_mtime_ns

    merge_settings(path)

    assert path.stat().st_mtime_ns == mtime
    assert not report_changes.backup_path(path).exists()
    assert report_changes.load_report()[str(path)]["status"] == report_changes.UNCHANGED



def test_diff_against_snapshot_baseline(tmp_path: Path) -> None:
    """Step 2(plugin 설치)가 쓴 키도 snapshot 기준 diff 에 나타나고, 백업은 Step 2 이전 원본."""
    path = tmp_path / "settings.json"
    original = {"model": "sonnet"}
    path.write_text(json.dumps(original))
    report_changes.snapshot(path)
    path.write_text(json.dumps({**original, "enabledPlugins": {"x@y": True}}))  # Step 2

    merge_settings(path)

    entry = report_changes.load_report()[str(path)]
    assert entry["status"] == report_changes.CHANGED
    assert entry["diff"]["added"]["enabledPlugins"] == {"x@y": True}
    assert json.loads(report_changes.backup_path(path).read_text()) == original


def test_already_merged_but_baseline_differs(tmp_path: Path) -> None:
    """파일은 이미 병합 상태(재작성 안 함)여도 snapshot 기준 변경은 보고한다."""
    path = tmp_path / "settings.json"
    path.write_text("{}")
    report_changes.snapshot(path)
    merged = merge_settings(path)
    report_changes.snapshot(path)  # 다음 실행: 기준 = 병합 상태
    path.write_text(json.dumps({**merged, "enabledPlugins": {"x@y": True}}))  # Step 2
    mtime = path.stat().st_mtime_ns

    merge_settings(path)

    assert path.stat().st_mtime_ns == mtime
    entry = report_changes.load_report()[str(path)]
    assert entry["status"] == report_changes.CHANGED
    assert entry["diff"]["added"] == {"enabledPlugins": {"x@y": True}}

if __name__ == "__main__":
    unittest.main()
