"""프로젝트 구조 분석 및 프레임워크 감지 모듈.

프로젝트 디렉토리를 스캔하여 사용 언어, 프레임워크, 구조를 감지하고
적합한 jin-claude 에이전트를 추천한다.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

# 스캔 시 제외할 디렉토리 목록
IGNORE_DIRS: set[str] = {
    ".git",
    ".venv",
    "venv",
    ".env",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "target",
}

# 파일 확장자 → 언어 매핑
LANGUAGE_EXTENSIONS: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".rs": "Rust",
    ".go": "Go",
    ".java": "Java",
    ".kt": "Kotlin",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C",
    ".hpp": "C++",
    ".cs": "C#",
    ".scala": "Scala",
    ".lua": "Lua",
    ".r": "R",
    ".R": "R",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".fish": "Shell",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "SASS",
    ".less": "LESS",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".dart": "Dart",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".zig": "Zig",
    ".nim": "Nim",
    ".ml": "OCaml",
    ".hs": "Haskell",
    ".clj": "Clojure",
}

# 설정 파일 → 프레임워크 감지 정보
FRAMEWORK_INDICATORS: dict[str, dict] = {
    "package.json": {
        "type": "json",
        "dep_keys": ["dependencies", "devDependencies"],
        "frameworks": {
            "react": "React",
            "react-dom": "React",
            "vue": "Vue",
            "svelte": "Svelte",
            "next": "Next.js",
            "nuxt": "Nuxt",
            "@angular/core": "Angular",
            "express": "Express",
            "fastify": "Fastify",
            "nest": "NestJS",
            "@nestjs/core": "NestJS",
            "electron": "Electron",
            "vite": "Vite",
            "webpack": "Webpack",
            "tailwindcss": "Tailwind CSS",
        },
    },
    "pyproject.toml": {
        "type": "toml",
        "dep_keys": ["project.dependencies", "tool.poetry.dependencies"],
        "frameworks": {
            "fastapi": "FastAPI",
            "django": "Django",
            "flask": "Flask",
            "sqlalchemy": "SQLAlchemy",
            "celery": "Celery",
            "pydantic": "Pydantic",
            "pytest": "Pytest",
            "torch": "PyTorch",
            "tensorflow": "TensorFlow",
            "scikit-learn": "scikit-learn",
            "pandas": "pandas",
            "numpy": "NumPy",
            "loguru": "Loguru",
            "uvicorn": "Uvicorn",
            "httpx": "HTTPX",
        },
    },
    "requirements.txt": {
        "type": "text",
        "frameworks": {
            "fastapi": "FastAPI",
            "django": "Django",
            "flask": "Flask",
            "sqlalchemy": "SQLAlchemy",
            "celery": "Celery",
            "torch": "PyTorch",
            "tensorflow": "TensorFlow",
        },
    },
    "Cargo.toml": {
        "type": "indicator",
        "framework": "Rust (Cargo)",
    },
    "go.mod": {
        "type": "indicator",
        "framework": "Go Modules",
    },
    "build.gradle": {
        "type": "indicator",
        "framework": "Gradle (Java/Kotlin)",
    },
    "build.gradle.kts": {
        "type": "indicator",
        "framework": "Gradle Kotlin DSL",
    },
    "pom.xml": {
        "type": "indicator",
        "framework": "Maven (Java)",
    },
    "Gemfile": {
        "type": "indicator",
        "framework": "Ruby (Bundler)",
    },
    "pubspec.yaml": {
        "type": "indicator",
        "framework": "Flutter/Dart",
    },
    "composer.json": {
        "type": "indicator",
        "framework": "PHP (Composer)",
    },
}

# 프로젝트 특성 → 에이전트 추천 매핑
AGENT_RECOMMENDATIONS: dict[str, dict] = {
    "python": {
        "agent": "python-expert",
        "model": "sonnet",
        "reason": "Python 전문 코딩 및 리팩토링",
        "example": '"이 함수를 리팩토링해줘"',
    },
    "python-swe": {
        "agent": "swe-agent",
        "model": "sonnet",
        "reason": "Python 버그 수정 및 이슈 해결",
        "example": '"jin swe [이슈 설명]"',
    },
    "python-swe-high": {
        "agent": "swe-agent-high",
        "model": "opus",
        "reason": "복잡한 버그 심층 디버깅",
        "example": '"jin swe-high [복잡한 이슈]"',
    },
    "multi-module": {
        "agent": "jin-orchestrator",
        "model": "sonnet",
        "reason": "멀티 에이전트 오케스트레이션",
        "example": '"jin orchestrate [작업 설명]"',
    },
    "large-scale": {
        "agent": "jin-maxwork",
        "model": "sonnet",
        "reason": "대규모 병렬 작업 처리",
        "example": '"jin maxwork [대규모 작업]"',
    },
    "security": {
        "agent": "jin-gcc",
        "model": "sonnet",
        "reason": "보안 관점 코드 리뷰",
        "example": '"jin gcc [보안 검토 대상]"',
    },
    "cti": {
        "agent": "mole-research-agent",
        "model": "sonnet",
        "reason": "CTI/위협 인텔리전스 분석",
        "example": '"mole research [위협 정보]"',
    },
    "onboarding": {
        "agent": "jin-claude-init",
        "model": "sonnet",
        "reason": "프로젝트 초기 설정 및 온보딩",
        "example": '"jin init"',
    },
    "interview": {
        "agent": "jin-interview-agent",
        "model": "sonnet",
        "reason": "작업 전 요구사항 인터뷰",
        "example": '"jin interview"',
    },
    "analysis": {
        "agent": "swe-analyst",
        "model": "sonnet",
        "reason": "코드베이스 분석 및 이해",
        "example": '"이 코드 구조를 분석해줘"',
    },
}


def _should_ignore(path: Path) -> bool:
    """경로가 무시 대상인지 확인한다.

    Args:
        path: 확인할 경로.

    Returns:
        무시해야 하면 True, 아니면 False.
    """
    return any(part in IGNORE_DIRS for part in path.parts)


def detect_languages(project_dir: Path) -> list[str]:
    """프로젝트 디렉토리에서 사용 언어를 감지한다.

    파일 확장자를 기반으로 언어를 감지하고, 빈도순으로 정렬하여 반환한다.

    Args:
        project_dir: 분석할 프로젝트 디렉토리 경로.

    Returns:
        감지된 언어 목록 (빈도 내림차순).
    """
    lang_counter: Counter[str] = Counter()

    for file_path in project_dir.rglob("*"):
        if not file_path.is_file():
            continue
        if _should_ignore(file_path.relative_to(project_dir)):
            continue

        ext = file_path.suffix.lower()
        if ext in LANGUAGE_EXTENSIONS:
            lang_counter[LANGUAGE_EXTENSIONS[ext]] += 1

    return [lang for lang, _ in lang_counter.most_common()]


def detect_frameworks(project_dir: Path) -> dict[str, str]:
    """프로젝트 설정 파일에서 프레임워크를 감지한다.

    package.json, pyproject.toml 등의 설정 파일을 파싱하여
    사용 중인 프레임워크를 식별한다.

    Args:
        project_dir: 분석할 프로젝트 디렉토리 경로.

    Returns:
        감지된 프레임워크 딕셔너리 (설정파일명 → 프레임워크명).
    """
    detected: dict[str, str] = {}

    for config_name, config_info in FRAMEWORK_INDICATORS.items():
        config_path = project_dir / config_name
        if not config_path.exists():
            continue

        config_type = config_info["type"]

        if config_type == "indicator":
            detected[config_name] = config_info["framework"]
            continue

        if config_type == "json":
            _detect_json_frameworks(config_path, config_info, detected)
        elif config_type == "toml":
            _detect_toml_frameworks(config_path, config_info, detected)
        elif config_type == "text":
            _detect_text_frameworks(config_path, config_info, detected)

    return detected


def _detect_json_frameworks(
    config_path: Path,
    config_info: dict,
    detected: dict[str, str],
) -> None:
    """JSON 설정 파일에서 프레임워크를 감지한다.

    Args:
        config_path: JSON 설정 파일 경로.
        config_info: 프레임워크 감지 설정 정보.
        detected: 감지 결과를 저장할 딕셔너리.
    """
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return

    all_deps: dict = {}
    for dep_key in config_info.get("dep_keys", []):
        deps = data.get(dep_key, {})
        if isinstance(deps, dict):
            all_deps.update(deps)

    for pkg_name, framework_name in config_info.get("frameworks", {}).items():
        if pkg_name in all_deps:
            detected[pkg_name] = framework_name


def _detect_toml_frameworks(
    config_path: Path,
    config_info: dict,
    detected: dict[str, str],
) -> None:
    """TOML 설정 파일에서 프레임워크를 감지한다.

    tomllib 없이 텍스트 기반으로 간단히 파싱한다.

    Args:
        config_path: TOML 설정 파일 경로.
        config_info: 프레임워크 감지 설정 정보.
        detected: 감지 결과를 저장할 딕셔너리.
    """
    try:
        content = config_path.read_text(encoding="utf-8").lower()
    except OSError:
        return

    for pkg_name, framework_name in config_info.get("frameworks", {}).items():
        if pkg_name.lower() in content:
            detected[pkg_name] = framework_name


def _detect_text_frameworks(
    config_path: Path,
    config_info: dict,
    detected: dict[str, str],
) -> None:
    """텍스트 기반 설정 파일(requirements.txt 등)에서 프레임워크를 감지한다.

    Args:
        config_path: 텍스트 설정 파일 경로.
        config_info: 프레임워크 감지 설정 정보.
        detected: 감지 결과를 저장할 딕셔너리.
    """
    try:
        content = config_path.read_text(encoding="utf-8").lower()
    except OSError:
        return

    for pkg_name, framework_name in config_info.get("frameworks", {}).items():
        if pkg_name.lower() in content:
            detected[pkg_name] = framework_name


def detect_structure(project_dir: Path) -> str:
    """프로젝트 디렉토리 구조 유형을 판별한다.

    monorepo, standard, flat 중 하나를 반환한다.

    - monorepo: 여러 하위 패키지가 존재 (복수의 package.json 또는 packages/ 디렉토리)
    - standard: src/ 또는 tests/ 같은 표준 디렉토리 구조
    - flat: 모든 파일이 루트에 위치

    Args:
        project_dir: 분석할 프로젝트 디렉토리 경로.

    Returns:
        구조 유형 문자열 ("monorepo", "standard", "flat").
    """
    # monorepo 감지: packages/, apps/ 디렉토리 또는 복수의 package.json
    monorepo_indicators = ["packages", "apps", "libs", "modules"]
    for indicator in monorepo_indicators:
        indicator_dir = project_dir / indicator
        if indicator_dir.is_dir():
            subdirs = [d for d in indicator_dir.iterdir() if d.is_dir()]
            if len(subdirs) >= 2:
                return "monorepo"

    # 하위 디렉토리에 복수의 package.json 확인
    package_json_count = 0
    for child in project_dir.iterdir():
        if child.is_dir() and not child.name.startswith(".") and child.name not in IGNORE_DIRS:
            if (child / "package.json").exists():
                package_json_count += 1
    if package_json_count >= 2:
        return "monorepo"

    # standard 구조 감지: src/, lib/, tests/, test/ 등
    standard_dirs = {"src", "lib", "tests", "test", "app", "api", "core"}
    existing_dirs = {
        d.name for d in project_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    }
    if existing_dirs & standard_dirs:
        return "standard"

    return "flat"


def recommend_agents(
    languages: list[str],
    frameworks: dict[str, str],
    structure: str,
) -> list[dict]:
    """프로젝트 특성에 기반하여 jin-claude 에이전트를 추천한다.

    Args:
        languages: 감지된 언어 목록.
        frameworks: 감지된 프레임워크 딕셔너리.
        structure: 프로젝트 구조 유형.

    Returns:
        추천 에이전트 목록 (각각 agent, model, reason, example 키 포함).
    """
    recommendations: list[dict] = []
    added_agents: set[str] = set()

    def _add(key: str) -> None:
        """중복 없이 에이전트를 추천 목록에 추가한다."""
        if key in AGENT_RECOMMENDATIONS and AGENT_RECOMMENDATIONS[key]["agent"] not in added_agents:
            rec = AGENT_RECOMMENDATIONS[key].copy()
            recommendations.append(rec)
            added_agents.add(rec["agent"])

    # 항상 추천: 온보딩, 인터뷰, 분석
    _add("onboarding")
    _add("interview")
    _add("analysis")

    # 언어 기반 추천
    if "Python" in languages:
        _add("python")
        _add("python-swe")
        _add("python-swe-high")

    # 구조 기반 추천
    if structure == "monorepo" or len(languages) >= 3:
        _add("multi-module")
        _add("large-scale")

    # 보안 관련은 항상 추천
    _add("security")

    # CTI 관련 키워드 확인
    framework_values = {v.lower() for v in frameworks.values()}
    cti_keywords = {"threat", "intel", "security", "mole", "cti"}
    if cti_keywords & framework_values:
        _add("cti")

    return recommendations


def generate_agents_md(
    project_dir: Path,
    languages: list[str],
    frameworks: dict[str, str],
    structure: str,
    agents: list[dict],
) -> str:
    """AGENTS.md 마크다운 콘텐츠를 생성한다.

    Args:
        project_dir: 프로젝트 디렉토리 경로.
        languages: 감지된 언어 목록.
        frameworks: 감지된 프레임워크 딕셔너리.
        structure: 프로젝트 구조 유형.
        agents: 추천 에이전트 목록.

    Returns:
        AGENTS.md 마크다운 문자열.
    """
    # 프로젝트 이름
    project_name = project_dir.name

    # 언어 문자열
    lang_str = ", ".join(languages) if languages else "감지되지 않음"

    # 프레임워크 문자열
    framework_names = sorted(set(frameworks.values()))
    framework_str = ", ".join(framework_names) if framework_names else "감지되지 않음"

    # 구조 설명
    structure_map = {
        "monorepo": "Monorepo (복수 패키지)",
        "standard": "Standard (src/tests)",
        "flat": "Flat (단일 디렉토리)",
    }
    structure_str = structure_map.get(structure, structure)

    # 디렉토리 구조 요약
    dir_summary = _generate_dir_summary(project_dir)

    # 에이전트 테이블
    agent_rows = ""
    for agent in agents:
        agent_rows += (
            f"| {agent['agent']} | {agent['model']} "
            f"| {agent['reason']} | {agent['example']} |\n"
        )

    # 스킬 테이블
    skills_table = _generate_skills_table()

    md = f"""# AGENTS.md — {project_name}

## 프로젝트 개요

- **언어**: {lang_str}
- **프레임워크**: {framework_str}
- **구조**: {structure_str}

## 디렉토리 구조

```
{dir_summary}
```

## 추천 에이전트

| 에이전트 | 모델 | 추천 이유 | 사용 예시 |
|----------|------|-----------|-----------|
{agent_rows}
## 사용 가능한 스킬

{skills_table}

## 관련 파일

- `agents/` — jin-claude 에이전트 정의 파일
- `skills/` — jin-claude 스킬 정의 파일
- `CLAUDE.md` — 프로젝트 지침 파일
"""
    return md


def _generate_dir_summary(project_dir: Path) -> str:
    """프로젝트 루트의 디렉토리 구조 요약을 생성한다.

    Args:
        project_dir: 프로젝트 디렉토리 경로.

    Returns:
        디렉토리 트리 문자열.
    """
    lines: list[str] = [f"{project_dir.name}/"]

    entries = sorted(project_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name))
    for entry in entries:
        if entry.name.startswith(".") or entry.name in IGNORE_DIRS:
            continue
        if entry.is_dir():
            lines.append(f"  {entry.name}/")
            # 1단계 하위 디렉토리만 표시
            try:
                sub_entries = sorted(entry.iterdir(), key=lambda p: (not p.is_dir(), p.name))
                for sub in sub_entries[:5]:
                    if sub.name.startswith(".") or sub.name in IGNORE_DIRS:
                        continue
                    suffix = "/" if sub.is_dir() else ""
                    lines.append(f"    {sub.name}{suffix}")
                remaining = len([
                    s for s in sub_entries[5:]
                    if not s.name.startswith(".") and s.name not in IGNORE_DIRS
                ])
                if remaining > 0:
                    lines.append(f"    ... (+{remaining} more)")
            except PermissionError:
                lines.append("    (접근 불가)")
        else:
            lines.append(f"  {entry.name}")

    return "\n".join(lines)


def _generate_skills_table() -> str:
    """사용 가능한 jin-claude 스킬 테이블을 생성한다.

    Returns:
        마크다운 테이블 문자열.
    """
    skills = [
        ("jin-orchestrator", '"jin orchestrate"', "멀티 에이전트 오케스트레이션"),
        ("jin-maxwork", '"jin maxwork"', "대규모 병렬 작업 처리"),
        ("jin-commit", '"commit"', "Gitmoji 기반 커밋 메시지 생성"),
        ("jin-deepinit", '"jin deepinit"', "프로젝트 분석 및 AGENTS.md 생성"),
        ("jin-interview", '"jin interview"', "작업 전 요구사항 인터뷰"),
        ("jin-ralph", '"ralph"', "반복 실행 모드"),
        ("jin-gcc", '"jin gcc"', "보안 관점 코드 리뷰"),
        ("jin-swe-fix", '"jin swe"', "SWE 에이전트 버그 수정"),
        ("jin-fsd", '"jin fsd"', "풀스택 개발"),
        ("jin-cleanser", '"jin cleanser"', "코드 정리 및 리팩토링"),
        ("verify-implementation", '"verify"', "구현 검증"),
    ]

    lines = [
        "| 스킬 | 트리거 | 설명 |",
        "|------|--------|------|",
    ]
    for name, trigger, desc in skills:
        lines.append(f"| {name} | {trigger} | {desc} |")

    return "\n".join(lines)


def analyze(project_dir: Path) -> dict:
    """프로젝트를 분석하여 종합 결과를 반환한다.

    Args:
        project_dir: 분석할 프로젝트 디렉토리 경로.

    Returns:
        분석 결과 딕셔너리.
    """
    languages = detect_languages(project_dir)
    frameworks = detect_frameworks(project_dir)
    structure = detect_structure(project_dir)
    agents = recommend_agents(languages, frameworks, structure)

    return {
        "project_dir": str(project_dir.resolve()),
        "project_name": project_dir.name,
        "languages": languages,
        "frameworks": frameworks,
        "structure": structure,
        "recommended_agents": agents,
    }


def main() -> None:
    """CLI 엔트리 포인트. 프로젝트를 분석하고 JSON 결과를 출력한다."""
    if len(sys.argv) > 1:
        project_dir = Path(sys.argv[1])
    else:
        project_dir = Path.cwd()

    if not project_dir.is_dir():
        print(
            json.dumps({"error": f"디렉토리를 찾을 수 없습니다: {project_dir}"}, ensure_ascii=False),
            file=sys.stderr,
        )
        sys.exit(1)

    result = analyze(project_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
