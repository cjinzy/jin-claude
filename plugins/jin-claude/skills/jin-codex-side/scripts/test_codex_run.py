"""codex_run 테스트. 실제 codex 대신 python 스텁 명령으로 검증한다 (비용·외부 전송 없음)."""

import json
import subprocess
import sys
from pathlib import Path

from codex_run import (
    BOUNDARY,
    EXIT_NESTED,
    EXIT_TIMEOUT,
    parse_events,
    review_gate,
    status_of,
)

SCRIPT = Path(__file__).with_name("codex_run.py")


def jsonl(*events: dict) -> str:
    return "\n".join(json.dumps(e) for e in events)


OK_EVENTS = jsonl(
    {"type": "thread.started", "thread_id": "abc-123"},
    {"type": "item.completed", "item": {"type": "reasoning", "text": "thinking"}},
    {"type": "item.completed", "item": {"type": "command_execution", "command": "git diff"}},
    {"type": "item.completed", "item": {"type": "agent_message", "text": "[P2] nit"}},
    {"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 20}},
)


def invoke(args: list[str], stdin: str = "", env: dict | None = None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        input=stdin,
        capture_output=True,
        text=True,
        env=env,
    )


def test_parse_events_extracts_all_fields():
    ev = parse_events(OK_EVENTS + "\nnot json line")
    assert ev["session_id"] == "abc-123"
    assert ev["tokens"] == 120
    assert ev["completed"] == 1
    assert ev["messages"] == 1
    assert "[codex thinking] thinking" in ev["transcript"]
    assert "[codex ran] git diff" in ev["transcript"]
    assert "not json line" in ev["transcript"]  # 스키마 변경 대비 원문 보존


def test_status_fail_closed():
    ok = parse_events(OK_EVENTS)
    assert status_of(0, ok) == "ok"
    assert status_of(EXIT_TIMEOUT, ok) == "timeout"
    assert status_of(1, ok) == "failed"
    assert status_of(0, parse_events("")) == "empty"
    started = parse_events(jsonl({"type": "thread.started", "thread_id": "t"}))
    assert status_of(0, started) == "no_completion"  # 중간 끊김
    failed = parse_events(jsonl({"type": "turn.failed", "error": {"message": "boom"}}))
    assert status_of(0, failed) == "turn_failed"


def test_review_gate():
    assert review_gate("ok", "[P1] sql injection").startswith("FAIL (1 critical")
    assert review_gate("ok", "P0: data loss").startswith("FAIL")
    assert review_gate("ok", "[P2] naming\n[P3] typo") == "PASS"
    assert review_gate("ok", "looks good").startswith("UNVERIFIED")
    assert review_gate("ok", "").startswith("FAIL (fail-closed")
    assert review_gate("timeout", "[P3] x").startswith("FAIL (fail-closed: timeout")
    # 산문 속 bare P0/P1 은 태그가 아니다
    assert review_gate("ok", "No P0 or P1 issues found. [P3] nit at a.py:1") == "PASS"


def test_stdin_and_boundary_reach_command(tmp_path):
    out = tmp_path / "stdin.txt"
    stub = f"import sys; open({str(out)!r}, 'w').write(sys.stdin.read())"
    r = invoke(["--boundary", "--", sys.executable, "-c", stub], stdin="user $(rm -rf) `x`")
    assert r.returncode == 0
    assert out.read_text() == BOUNDARY + "user $(rm -rf) `x`"  # 셸 해석 없이 그대로


def test_timeout_kills_and_returns_124():
    r = invoke(["--timeout", "0.5", "--", sys.executable, "-c", "import time; time.sleep(30)"])
    assert r.returncode == EXIT_TIMEOUT
    assert "STATUS: timeout" in r.stdout


def test_gate_reads_output_file(tmp_path):
    last = tmp_path / "last.md"
    stub = f"open({str(last)!r}, 'w').write('[P1] bug'); print({OK_EVENTS!r})"
    r = invoke(["--gate", "--", sys.executable, "-c", stub, "-o", str(last)])
    assert "STATUS: ok" in r.stdout
    assert "SESSION_ID: abc-123" in r.stdout
    assert "GATE: FAIL (1 critical findings)" in r.stdout


def test_log_file_and_stderr_excerpt(tmp_path):
    log = tmp_path / "t.log"
    stub = "import sys; sys.stderr.write('401 Unauthorized\\n'); sys.exit(3)"
    r = invoke(["--log", str(log), "--", sys.executable, "-c", stub])
    assert r.returncode == 3
    assert "STATUS: failed" in r.stdout
    assert "codex login" in r.stdout
    assert "401 Unauthorized" in r.stdout
    assert log.exists()


def test_nested_codex_refused():
    env = {"PATH": "/usr/bin:/bin", "CODEX_SANDBOX": "seatbelt"}
    r = invoke(["--", "true"], env=env)
    assert r.returncode == EXIT_NESTED
    assert "STATUS: nested" in r.stdout


def test_missing_binary():
    r = invoke(["--", "definitely-not-a-binary-xyz"])
    assert r.returncode != 0
    assert "STATUS: failed" in r.stdout


def test_plain_text_output_is_ok_and_gated_from_stdout():
    # 최상위 `codex review` 는 JSONL·-o 없이 평문만 낸다 → 평문도 정상 결과로 판정
    r = invoke(["--gate", "--", sys.executable, "-c", "print('[P2] nit')"])
    assert "STATUS: ok" in r.stdout
    assert "GATE: PASS" in r.stdout
