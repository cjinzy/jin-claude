"""slop_patterns 모듈 테스트 스위트.

정적 슬롭 패턴 감지, ruff 출력 파싱, 리포트 생성을 검증한다.
"""

import pytest

from slop_patterns import (
    CATEGORY_SEVERITY,
    STATIC_PATTERNS,
    Severity,
    SlopCategory,
    SlopIssue,
    detect_static_patterns,
    format_report,
    parse_ruff_output,
)


class TestSlopCategory:
    """SlopCategory 열거형 테스트."""

    def test_모든_카테고리_8개_존재(self) -> None:
        """8개의 슬롭 카테고리가 모두 정의되어 있는지 확인한다."""
        assert len(SlopCategory) == 8

    def test_카테고리_값_형식(self) -> None:
        """모든 카테고리 값이 kebab-case 문자열인지 확인한다."""
        for cat in SlopCategory:
            assert "-" in cat.value or cat.value.isalpha()
            assert cat.value == cat.value.lower()

    def test_카테고리별_심각도_매핑_완전성(self) -> None:
        """모든 카테고리에 대한 심각도 매핑이 존재하는지 확인한다."""
        for cat in SlopCategory:
            assert cat in CATEGORY_SEVERITY


class TestSeverity:
    """Severity 열거형 테스트."""

    def test_심각도_순서_비교(self) -> None:
        """INFO < WARNING < CRITICAL 순서가 올바른지 확인한다."""
        assert Severity.INFO < Severity.WARNING
        assert Severity.WARNING < Severity.CRITICAL
        assert Severity.INFO < Severity.CRITICAL

    def test_심각도_문자열_표현(self) -> None:
        """str() 변환 시 값 문자열을 반환하는지 확인한다."""
        assert str(Severity.INFO) == "info"
        assert str(Severity.WARNING) == "warning"
        assert str(Severity.CRITICAL) == "critical"

    def test_심각도_동등_비교(self) -> None:
        """동일 심각도 간 비교가 올바른지 확인한다."""
        assert Severity.INFO <= Severity.INFO
        assert Severity.WARNING >= Severity.WARNING
        assert not (Severity.INFO > Severity.INFO)


class TestDetectStaticPatterns:
    """detect_static_patterns 함수 테스트."""

    def test_디버그_print_감지(self, tmp_path: pytest.TempPathFactory) -> None:
        """print() 호출을 leftover-debug로 감지하는지 확인한다."""
        test_file = tmp_path / "debug_test.py"
        test_file.write_text("x = 1\nprint(x)\ny = 2\n", encoding="utf-8")

        issues = detect_static_patterns(test_file)

        assert len(issues) == 1
        assert issues[0].category == SlopCategory.LEFTOVER_DEBUG
        assert issues[0].severity == Severity.CRITICAL
        assert issues[0].line == 2
        assert "print" in issues[0].code_snippet

    def test_console_log_감지(self, tmp_path: pytest.TempPathFactory) -> None:
        """console.log() 호출을 leftover-debug로 감지하는지 확인한다."""
        test_file = tmp_path / "debug_test.js"
        test_file.write_text(
            "const x = 1;\nconsole.log(x);\nconst y = 2;\n",
            encoding="utf-8",
        )

        issues = detect_static_patterns(test_file)

        assert len(issues) == 1
        assert issues[0].category == SlopCategory.LEFTOVER_DEBUG
        assert issues[0].line == 2

    def test_주석처리된_코드_블록_감지(self, tmp_path: pytest.TempPathFactory) -> None:
        """주석 처리된 코드를 dead-code로 감지하는지 확인한다."""
        test_file = tmp_path / "dead_code_test.py"
        test_file.write_text(
            "x = 1\n# def old_function():\n# return None\n",
            encoding="utf-8",
        )

        issues = detect_static_patterns(test_file)

        dead_issues = [i for i in issues if i.category == SlopCategory.DEAD_CODE]
        assert len(dead_issues) >= 1
        assert dead_issues[0].severity == Severity.WARNING

    def test_TODO_주석_감지(self, tmp_path: pytest.TempPathFactory) -> None:
        """TODO/FIXME 주석을 unnecessary-comment로 감지하는지 확인한다."""
        test_file = tmp_path / "todo_test.py"
        test_file.write_text(
            "x = 1\n# TODO: 나중에 수정\n# FIXME: 버그 있음\ny = 2\n",
            encoding="utf-8",
        )

        issues = detect_static_patterns(test_file)

        todo_issues = [
            i for i in issues if i.category == SlopCategory.UNNECESSARY_COMMENT
        ]
        assert len(todo_issues) == 2

    def test_깨끗한_파일_이슈_없음(self, tmp_path: pytest.TempPathFactory) -> None:
        """슬롭이 없는 깨끗한 파일에서는 이슈가 없는지 확인한다."""
        test_file = tmp_path / "clean_test.py"
        test_file.write_text(
            'def add(a: int, b: int) -> int:\n    """두 수를 더한다."""\n    return a + b\n',
            encoding="utf-8",
        )

        issues = detect_static_patterns(test_file)

        assert len(issues) == 0

    def test_존재하지_않는_파일_예외(self, tmp_path: pytest.TempPathFactory) -> None:
        """존재하지 않는 파일에 대해 FileNotFoundError를 발생시키는지 확인한다."""
        fake_file = tmp_path / "nonexistent.py"

        with pytest.raises(FileNotFoundError):
            detect_static_patterns(fake_file)

    def test_breakpoint_감지(self, tmp_path: pytest.TempPathFactory) -> None:
        """breakpoint() 호출을 leftover-debug로 감지하는지 확인한다."""
        test_file = tmp_path / "bp_test.py"
        test_file.write_text("x = 1\nbreakpoint()\ny = 2\n", encoding="utf-8")

        issues = detect_static_patterns(test_file)

        debug_issues = [
            i for i in issues if i.category == SlopCategory.LEFTOVER_DEBUG
        ]
        assert len(debug_issues) == 1
        assert "breakpoint" in debug_issues[0].code_snippet


class TestParseRuffOutput:
    """parse_ruff_output 함수 테스트."""

    def test_단일_F401_파싱(self) -> None:
        """ruff F401 단일 출력을 올바르게 파싱하는지 확인한다."""
        output = "src/main.py:10:1: F401 `os` imported but unused\n"

        issues = parse_ruff_output(output)

        assert len(issues) == 1
        assert issues[0].file == "src/main.py"
        assert issues[0].line == 10
        assert issues[0].category == SlopCategory.UNUSED_IMPORT
        assert issues[0].severity == Severity.WARNING
        assert "os" in issues[0].code_snippet

    def test_복수_F401_파싱(self) -> None:
        """ruff F401 복수 출력을 올바르게 파싱하는지 확인한다."""
        output = (
            "src/main.py:1:1: F401 `os` imported but unused\n"
            "src/main.py:2:1: F401 `sys` imported but unused\n"
            "src/utils.py:5:1: F401 `json` imported but unused\n"
        )

        issues = parse_ruff_output(output)

        assert len(issues) == 3
        files = {i.file for i in issues}
        assert files == {"src/main.py", "src/utils.py"}

    def test_빈_출력_빈_리스트(self) -> None:
        """빈 ruff 출력에 대해 빈 리스트를 반환하는지 확인한다."""
        issues = parse_ruff_output("")

        assert issues == []


class TestFormatReport:
    """format_report 함수 테스트."""

    def test_이슈_없으면_깨끗한_메시지(self) -> None:
        """이슈가 없을 때 깨끗한 코드 메시지를 반환하는지 확인한다."""
        report = format_report([])

        assert "슬롭 이슈가 발견되지 않았습니다" in report

    def test_이슈_있으면_마크다운_테이블_생성(self) -> None:
        """이슈가 있을 때 마크다운 테이블을 포함한 리포트를 생성하는지 확인한다."""
        issues = [
            SlopIssue(
                file="test.py",
                line=10,
                category=SlopCategory.LEFTOVER_DEBUG,
                severity=Severity.CRITICAL,
                code_snippet="print('debug')",
                suggestion="디버그용 print() 호출을 제거하세요.",
            ),
            SlopIssue(
                file="test.py",
                line=5,
                category=SlopCategory.UNUSED_IMPORT,
                severity=Severity.WARNING,
                code_snippet="`os` imported but unused",
                suggestion="미사용 임포트를 제거하세요.",
            ),
        ]

        report = format_report(issues)

        assert "## AI Slop 분석 리포트" in report
        assert "| 심각도 | 건수 |" in report
        assert "| critical | 1 |" in report
        assert "| warning | 1 |" in report
        assert "자동 삭제/수정은 하지 않습니다" in report
        # critical이 warning보다 먼저 나오는지 확인 (심각도 내림차순)
        critical_pos = report.index("leftover-debug")
        warning_pos = report.index("unused-import")
        assert critical_pos < warning_pos


class TestSlopIssue:
    """SlopIssue 데이터 클래스 테스트."""

    def test_confidence_범위_초과_예외(self) -> None:
        """confidence가 0.0~1.0 범위를 초과하면 ValueError를 발생시키는지 확인한다."""
        with pytest.raises(ValueError, match="confidence"):
            SlopIssue(
                file="test.py",
                line=1,
                category=SlopCategory.LEFTOVER_DEBUG,
                severity=Severity.CRITICAL,
                code_snippet="print('x')",
                suggestion="제거하세요.",
                confidence=1.5,
            )
