"""AI 생성 코드 슬롭 패턴 정의 및 정적 감지 엔진.

패턴 기반으로 불필요한 주석, 디버그 코드, 죽은 코드 등을 감지한다.
시맨틱 분석은 Claude 에이전트가 담당하며, 이 모듈은 정적 패턴만 처리한다.
"""

import re
import traceback
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class SlopCategory(Enum):
    """AI 슬롭 카테고리 열거형."""

    UNNECESSARY_COMMENT = "unnecessary-comment"
    EXCESSIVE_ERROR_HANDLING = "excessive-error-handling"
    UNUSED_IMPORT = "unused-import"
    BOILERPLATE_DOCSTRING = "boilerplate-docstring"
    OVER_ABSTRACTION = "over-abstraction"
    REDUNDANT_TYPE_ANNOTATION = "redundant-type-annotation"
    LEFTOVER_DEBUG = "leftover-debug"
    DEAD_CODE = "dead-code"


class Severity(Enum):
    """이슈 심각도 열거형.

    순서: INFO < WARNING < CRITICAL
    """

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

    def __lt__(self, other: "Severity") -> bool:
        """심각도 비교 연산자."""
        order = {Severity.INFO: 0, Severity.WARNING: 1, Severity.CRITICAL: 2}
        return order[self] < order[other]

    def __le__(self, other: "Severity") -> bool:
        """심각도 이하 비교 연산자."""
        return self == other or self < other

    def __gt__(self, other: "Severity") -> bool:
        """심각도 초과 비교 연산자."""
        return not self <= other

    def __ge__(self, other: "Severity") -> bool:
        """심각도 이상 비교 연산자."""
        return not self < other

    def __str__(self) -> str:
        """심각도를 문자열로 반환한다."""
        return self.value


# 카테고리별 심각도 매핑
CATEGORY_SEVERITY: dict[SlopCategory, Severity] = {
    SlopCategory.UNNECESSARY_COMMENT: Severity.WARNING,
    SlopCategory.EXCESSIVE_ERROR_HANDLING: Severity.WARNING,
    SlopCategory.UNUSED_IMPORT: Severity.WARNING,
    SlopCategory.BOILERPLATE_DOCSTRING: Severity.INFO,
    SlopCategory.OVER_ABSTRACTION: Severity.INFO,
    SlopCategory.REDUNDANT_TYPE_ANNOTATION: Severity.INFO,
    SlopCategory.LEFTOVER_DEBUG: Severity.CRITICAL,
    SlopCategory.DEAD_CODE: Severity.WARNING,
}


@dataclass
class SlopIssue:
    """슬롭 이슈 데이터 클래스.

    정적 분석 또는 시맨틱 분석에서 탐지된 단일 이슈를 나타낸다.
    """

    file: str
    line: int
    category: SlopCategory
    severity: Severity
    code_snippet: str
    suggestion: str
    end_line: int | None = None
    confidence: float = field(default=1.0)

    def __post_init__(self) -> None:
        """confidence 값 범위를 검증한다."""
        if not 0.0 <= self.confidence <= 1.0:
            msg = f"confidence는 0.0~1.0 범위여야 한다: {self.confidence}"
            raise ValueError(msg)


# 정적 감지 패턴 정의
# 각 패턴: (정규식, SlopCategory, 제안 메시지)
STATIC_PATTERNS: dict[SlopCategory, list[tuple[re.Pattern[str], str]]] = {
    SlopCategory.LEFTOVER_DEBUG: [
        (
            re.compile(r"^\s*print\s*\("),
            "디버그용 print() 호출을 제거하세요.",
        ),
        (
            re.compile(r"^\s*console\.log\s*\("),
            "디버그용 console.log() 호출을 제거하세요.",
        ),
        (
            re.compile(r"^\s*debugger\s*;?\s*$"),
            "debugger 문을 제거하세요.",
        ),
        (
            re.compile(r"^\s*pdb\.set_trace\s*\("),
            "pdb.set_trace() 호출을 제거하세요.",
        ),
        (
            re.compile(r"^\s*breakpoint\s*\("),
            "breakpoint() 호출을 제거하세요.",
        ),
        (
            re.compile(r"^\s*import\s+pdb\b"),
            "디버그용 pdb 임포트를 제거하세요.",
        ),
    ],
    SlopCategory.DEAD_CODE: [
        (
            re.compile(r"^\s*#\s*(?:def |class |if |for |while |return |import )"),
            "주석 처리된 코드 블록이 발견되었습니다. 불필요하면 삭제를 고려하세요.",
        ),
    ],
    SlopCategory.UNNECESSARY_COMMENT: [
        (
            re.compile(
                r"^\s*#\s*(?:TODO|FIXME|HACK|XXX|TEMP|TEMPORARY)\b",
                re.IGNORECASE,
            ),
            "TODO/FIXME 등의 임시 주석이 남아있습니다. 처리하거나 제거하세요.",
        ),
    ],
}


def detect_static_patterns(file_path: Path) -> list[SlopIssue]:
    """파일에 대해 정적 패턴 매칭을 수행하여 슬롭 이슈를 반환한다.

    Args:
        file_path: 분석할 파일 경로.

    Returns:
        탐지된 SlopIssue 목록.

    Raises:
        FileNotFoundError: 파일이 존재하지 않을 때.
        UnicodeDecodeError: 파일 인코딩이 올바르지 않을 때.
    """
    issues: list[SlopIssue] = []
    file_str = str(file_path)

    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        traceback.print_exc()
        raise
    except UnicodeDecodeError:
        traceback.print_exc()
        raise

    for line_num, line_content in enumerate(lines, start=1):
        for category, patterns in STATIC_PATTERNS.items():
            for pattern, suggestion in patterns:
                if pattern.search(line_content):
                    issues.append(
                        SlopIssue(
                            file=file_str,
                            line=line_num,
                            category=category,
                            severity=CATEGORY_SEVERITY[category],
                            code_snippet=line_content.strip(),
                            suggestion=suggestion,
                        )
                    )

    return issues


def parse_ruff_output(output: str) -> list[SlopIssue]:
    """ruff check --select F401 의 기본 출력을 파싱하여 SlopIssue 목록을 반환한다.

    ruff 기본 출력 형식:
        path/to/file.py:10:1: F401 `os` imported but unused

    Args:
        output: ruff의 stdout 출력 문자열.

    Returns:
        파싱된 SlopIssue 목록.
    """
    issues: list[SlopIssue] = []
    # ruff 기본 출력 패턴: file:line:col: CODE message
    ruff_pattern = re.compile(
        r"^(.+?):(\d+):\d+:\s+F401\s+(.+)$",
        re.MULTILINE,
    )

    for match in ruff_pattern.finditer(output):
        file_path = match.group(1)
        line_num = int(match.group(2))
        message = match.group(3).strip()

        issues.append(
            SlopIssue(
                file=file_path,
                line=line_num,
                category=SlopCategory.UNUSED_IMPORT,
                severity=Severity.WARNING,
                code_snippet=message,
                suggestion=f"미사용 임포트를 제거하세요: {message}",
            )
        )

    return issues


def format_report(issues: list[SlopIssue]) -> str:
    """슬롭 이슈 목록을 마크다운 리포트로 포맷팅한다.

    Args:
        issues: SlopIssue 목록.

    Returns:
        마크다운 형식의 리포트 문자열.
    """
    if not issues:
        return "## AI Slop 분석 리포트\n\n슬롭 이슈가 발견되지 않았습니다. 코드가 깨끗합니다!"

    # 심각도별 건수 집계
    severity_counts: dict[Severity, int] = {
        Severity.CRITICAL: 0,
        Severity.WARNING: 0,
        Severity.INFO: 0,
    }
    for issue in issues:
        severity_counts[issue.severity] += 1

    # 리포트 헤더
    lines: list[str] = [
        "## AI Slop 분석 리포트",
        "",
        "### 요약",
        "| 심각도 | 건수 |",
        "|--------|------|",
        f"| critical | {severity_counts[Severity.CRITICAL]} |",
        f"| warning | {severity_counts[Severity.WARNING]} |",
        f"| info | {severity_counts[Severity.INFO]} |",
        "",
        "### 이슈 목록",
        "| # | 파일 | 라인 | 카테고리 | 심각도 | 제안 |",
        "|---|------|------|----------|--------|------|",
    ]

    # 심각도 내림차순 정렬 (critical → warning → info)
    sorted_issues = sorted(issues, key=lambda i: i.severity, reverse=True)

    for idx, issue in enumerate(sorted_issues, start=1):
        lines.append(
            f"| {idx} | {issue.file} | {issue.line} "
            f"| {issue.category.value} | {issue.severity.value} "
            f"| {issue.suggestion} |"
        )

    lines.extend([
        "",
        "**주의: 이 도구는 리뷰만 수행합니다. 자동 삭제/수정은 하지 않습니다.**",
    ])

    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("사용법: python slop_patterns.py <파일경로> [파일경로...]")
        print("예시: python slop_patterns.py src/main.py src/utils.py")
        sys.exit(1)

    all_issues: list[SlopIssue] = []
    for arg in sys.argv[1:]:
        target = Path(arg)
        if not target.exists():
            print(f"경고: 파일을 찾을 수 없습니다 — {target}")
            continue
        if target.is_dir():
            for py_file in target.rglob("*.py"):
                try:
                    all_issues.extend(detect_static_patterns(py_file))
                except (UnicodeDecodeError, FileNotFoundError):
                    traceback.print_exc()
        else:
            try:
                all_issues.extend(detect_static_patterns(target))
            except (UnicodeDecodeError, FileNotFoundError):
                traceback.print_exc()

    print(format_report(all_issues))
