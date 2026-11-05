"""모든 테스트가 실제 ~/.claude 변경 기록을 건드리지 않도록 격리한다."""

from pathlib import Path

import pytest
import report_changes


@pytest.fixture(autouse=True)
def _isolate_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """변경 기록 파일을 테스트별 tmp_path 로 돌린다."""
    path = tmp_path / "changes.json"
    monkeypatch.setattr(report_changes, "REPORT_PATH", path)
    return path
