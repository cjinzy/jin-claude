"""merge_settings.py 단위 테스트."""

import json
import tempfile
import unittest
from pathlib import Path

from merge_settings import REQUIRED_SETTINGS, deep_merge, merge_settings


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

            for key, value in REQUIRED_SETTINGS.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        self.assertEqual(result[key][sub_key], sub_value)
                else:
                    self.assertEqual(result[key], value)


if __name__ == "__main__":
    unittest.main()
