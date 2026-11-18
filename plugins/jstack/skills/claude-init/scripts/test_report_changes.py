"""report_changes 모듈 단위 테스트 — 백업 이름, 변경 기록, 요약 출력."""

import json
from datetime import date
from pathlib import Path

import report_changes as rc

DAY = date(2026, 11, 5)


class TestBackupPath:
    def test_with_extension(self, tmp_path: Path) -> None:
        assert (
            rc.backup_path(tmp_path / "settings.json", DAY).name == "settings_backup_20261105.json"
        )

    def test_markdown(self, tmp_path: Path) -> None:
        assert rc.backup_path(tmp_path / "CLAUDE.md", DAY).name == "CLAUDE_backup_20261105.md"

    def test_no_extension(self, tmp_path: Path) -> None:
        assert rc.backup_path(tmp_path / "Makefile", DAY).name == "Makefile_backup_20261105"

    def test_dotdir(self, tmp_path: Path) -> None:
        assert (
            rc.backup_path(tmp_path / ".jin-claude-repo", DAY).name
            == ".jin-claude-repo_backup_20261105"
        )

    def test_same_dir(self, tmp_path: Path) -> None:
        assert rc.backup_path(tmp_path / "a.md", DAY).parent == tmp_path


class TestTrackWrite:
    def test_new_file(self, tmp_path: Path, _isolate_report: Path) -> None:
        dst = tmp_path / "new.md"
        assert rc.track_write(dst, unchanged=False) is True
        entry = rc.load_report()[str(dst)]
        assert entry == {"status": rc.NEW, "backup": None, "diff": None}

    def test_unchanged_no_backup(self, tmp_path: Path) -> None:
        dst = tmp_path / "same.md"
        dst.write_text("x")
        assert rc.track_write(dst, unchanged=True) is False
        assert rc.load_report()[str(dst)]["status"] == rc.UNCHANGED
        assert not rc.backup_path(dst).exists()

    def test_changed_creates_backup(self, tmp_path: Path) -> None:
        dst = tmp_path / "CLAUDE.md"
        dst.write_text("old")
        assert rc.track_write(dst, unchanged=False) is True
        bak = rc.backup_path(dst)
        assert bak.read_text() == "old"
        assert rc.load_report()[str(dst)] == {
            "status": rc.CHANGED,
            "backup": str(bak),
            "diff": None,
        }

    def test_keeps_existing_same_day_backup(self, tmp_path: Path) -> None:
        """당일 백업 유지 + 덮어쓸 내용이 다르면 시각 붙은 추가 백업에 보존."""
        dst = tmp_path / "CLAUDE.md"
        bak = rc.backup_path(dst)
        bak.write_text("original")
        dst.write_text("first-init")
        rc.track_write(dst, unchanged=False)
        assert bak.read_text() == "original"
        recorded = Path(rc.load_report()[str(dst)]["backup"])
        assert recorded != bak
        assert recorded.name.startswith(f"CLAUDE{rc.BACKUP_INFIX}{date.today():%Y%m%d}_")
        assert recorded.read_text() == "first-init"

    def test_same_day_backup_equal_content_reused(self, tmp_path: Path) -> None:
        dst = tmp_path / "CLAUDE.md"
        bak = rc.backup_path(dst)
        bak.write_text("same")
        dst.write_text("same")
        rc.track_write(dst, unchanged=False)
        assert rc.load_report()[str(dst)]["backup"] == str(bak)
        assert sorted(p.name for p in tmp_path.glob("CLAUDE*")) == ["CLAUDE.md", bak.name]

    def test_second_same_day_run_keeps_user_edit(self, tmp_path: Path) -> None:
        """init → 사용자 수정 → 같은 날 init: 수정 내용이 기록된 백업에 남는다."""
        dst = tmp_path / "CLAUDE.md"
        dst.write_text("ORIGINAL")
        rc.track_write(dst, unchanged=False)
        dst.write_text("INIT")
        dst.write_text("USER EDIT")
        rc.REPORT_PATH.unlink()
        rc.track_write(dst, unchanged=False)
        assert rc.backup_path(dst).read_text() == "ORIGINAL"
        assert Path(rc.load_report()[str(dst)]["backup"]).read_text() == "USER EDIT"

    def test_diff_stored(self, tmp_path: Path) -> None:
        dst = tmp_path / "settings.json"
        diff = {"added": {"a": 1}, "changed": {}, "removed": {}}
        rc.track_write(dst, unchanged=False, diff=diff)
        assert rc.load_report()[str(dst)]["diff"] == diff


class TestSnapshot:
    """init 시작 시 settings.json 기준 상태 고정 — Step 2(plugin 설치) 쓰기 전."""

    def test_backs_up_and_stores_baseline(self, tmp_path: Path) -> None:
        dst = tmp_path / "settings.json"
        dst.write_text('{"a": 1}')
        rc.snapshot(dst)
        entry = rc.load_report()[str(dst)]
        assert entry["baseline"] == '{"a": 1}'
        assert rc.backup_path(dst).read_text() == '{"a": 1}'

    def test_clears_stale_report(self, tmp_path: Path) -> None:
        rc.track_write(tmp_path / "stale.md", unchanged=False)
        rc.snapshot(tmp_path / "settings.json")
        assert str(tmp_path / "stale.md") not in rc.load_report()

    def test_missing_file_is_new(self, tmp_path: Path) -> None:
        dst = tmp_path / "settings.json"
        rc.snapshot(dst)
        dst.write_text("{}")  # Step 2 가 생성
        rc.track_write(dst, unchanged=False)
        assert rc.load_report()[str(dst)]["status"] == rc.NEW

    def test_track_write_reuses_snapshot_backup(self, tmp_path: Path) -> None:
        dst = tmp_path / "settings.json"
        dst.write_text("ORIGINAL")
        rc.snapshot(dst)
        dst.write_text("AFTER STEP 2")
        rc.track_write(dst, unchanged=False)
        entry = rc.load_report()[str(dst)]
        assert entry == {"status": rc.CHANGED, "backup": str(rc.backup_path(dst)), "diff": None}
        assert rc.backup_path(dst).read_text() == "ORIGINAL"

    def test_unchanged_drops_snapshot_backup(self, tmp_path: Path) -> None:
        dst = tmp_path / "settings.json"
        dst.write_text("X")
        rc.snapshot(dst)
        rc.track_write(dst, unchanged=True)
        assert not rc.backup_path(dst).exists()
        assert rc.load_report()[str(dst)]["backup"] is None


class TestTextDiff:
    def test_counts_and_lines(self) -> None:
        d = rc.text_diff("a\nb\nc\n", "a\nB\nc\nd\n")
        assert (d["plus"], d["minus"]) == (2, 1)
        assert d["lines"] == ["-b", "+B", "+d"]

    def test_lines_capped(self) -> None:
        new = "".join(f"{i}\n" for i in range(rc.MAX_DIFF_LINES * 2))
        d = rc.text_diff("", new)
        assert d["plus"] == rc.MAX_DIFF_LINES * 2
        assert len(d["lines"]) == rc.MAX_DIFF_LINES

    def test_content_starting_with_plus_kept(self) -> None:
        assert rc.text_diff("", "++ x\n")["lines"] == ["+++ x"]

    def test_format_shows_text_diff(self, tmp_path: Path) -> None:
        report = {
            str(tmp_path / "CLAUDE.md"): {
                "status": rc.CHANGED,
                "backup": str(tmp_path / "CLAUDE_backup_20261105.md"),
                "diff": rc.text_diff("old\n", "new\n"),
            }
        }
        out = rc.format_report(report)
        assert "+1 / -1" in out
        assert "-old" in out and "+new" in out


class TestDiffDicts:
    def test_added_changed_removed(self) -> None:
        old = {"model": "sonnet", "hooks": {"Stop": []}, "env": {"KEEP": "1"}}
        new = {"model": "opus", "env": {"KEEP": "1", "NEW": "1"}}
        assert rc.diff_dicts(old, new) == {
            "added": {"env.NEW": "1"},
            "changed": {"model": ["sonnet", "opus"]},
            "removed": {"hooks": {"Stop": []}},
        }

    def test_equal(self) -> None:
        assert rc.diff_dicts({"a": {"b": 1}}, {"a": {"b": 1}}) == {
            "added": {},
            "changed": {},
            "removed": {},
        }


class TestFormatAndMain:
    def test_format_lists_changes_and_rollback(self, tmp_path: Path) -> None:
        report = {
            str(tmp_path / "settings.json"): {
                "status": rc.CHANGED,
                "backup": str(tmp_path / "settings_backup_20261105.json"),
                "diff": {
                    "added": {"language": "korean"},
                    "changed": {"model": ["sonnet", "opus"]},
                    "removed": {"hooks": {}},
                },
            },
            str(tmp_path / "new.md"): {"status": rc.NEW, "backup": None, "diff": None},
            str(tmp_path / "same.md"): {"status": rc.UNCHANGED, "backup": None, "diff": None},
        }
        out = rc.format_report(report)
        assert "신규 1 · 변경 1 · 동일 1" in out
        assert "settings_backup_20261105.json" in out
        assert '+ language: "korean"' in out
        assert '~ model: "sonnet" → "opus"' in out
        assert "- hooks" in out
        assert "new.md" in out
        assert "same.md" not in out
        assert "되돌리기" in out

    def test_format_empty(self) -> None:
        assert "변경 기록 없음" in rc.format_report({})

    def test_main_prints_and_consumes(self, tmp_path: Path, _isolate_report: Path, capsys) -> None:
        rc.track_write(tmp_path / "new.md", unchanged=False)
        rc.main()
        assert "new.md" in capsys.readouterr().out
        assert not _isolate_report.exists()

    def test_report_file_is_json(self, tmp_path: Path, _isolate_report: Path) -> None:
        rc.track_write(tmp_path / "a.md", unchanged=False)
        assert json.loads(_isolate_report.read_text())
