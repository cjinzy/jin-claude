"""프로젝트 구조 분석 및 프레임워크 감지 모듈.

프로젝트 디렉토리를 스캔하여 사용 언어, 프레임워크, 구조를 감지하고
사용 가능한 jin-claude 스킬을 안내하는 AGENTS.md 를 생성한다.
"""

from __future__ import annotations

import argparse
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

# 플러그인 skills/ 디렉토리 (이 파일: skills/jin-deepinit/scripts/).
# 스킬 테이블을 런타임에 생성해 drift 방지.
DEFAULT_SKILLS_DIR: Path = Path(__file__).resolve().parents[2]
SKILL_FILE = "SKILL.md"
FRONTMATTER_DELIMITER = "---"
# YAML block scalar 표시자 (`description: >` / `|`)
BLOCK_SCALAR_MARKERS = (">", "|", ">-", "|-")

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


def generate_agents_md(
    project_dir: Path,
    languages: list[str],
    frameworks: dict[str, str],
    structure: str,
    skills_dir: Path = DEFAULT_SKILLS_DIR,
) -> str:
    """AGENTS.md 마크다운 콘텐츠를 생성한다.

    Args:
        project_dir: 프로젝트 디렉토리 경로.
        languages: 감지된 언어 목록.
        frameworks: 감지된 프레임워크 딕셔너리.
        structure: 프로젝트 구조 유형.
        skills_dir: 스킬 테이블을 만들 SKILL.md 들의 상위 디렉토리.

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

    # 스킬 테이블
    skills_table = _generate_skills_table(skills_dir)

    md = f"""# AGENTS.md — {project_name}

## 프로젝트 개요

- **언어**: {lang_str}
- **프레임워크**: {framework_str}
- **구조**: {structure_str}

## 디렉토리 구조

```
{dir_summary}
```

## 사용 가능한 스킬

{skills_table}
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


def _read_frontmatter(skill_md: Path) -> dict[str, str]:
    """SKILL.md frontmatter 의 최상위 `key: value` 를 읽는다.

    ponytail: PyYAML 없이 평면 스칼라 + `>`/`|` block scalar 만 지원. 중첩 필드는 무시.
    """
    lines = skill_md.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        return {}

    fields: dict[str, str] = {}
    key = ""
    for line in lines[1:]:
        if line.strip() == FRONTMATTER_DELIMITER:
            break
        if line[:1].isspace():
            # 직전 block scalar 키의 연속 줄
            if key:
                fields[key] = f"{fields[key]} {line.strip()}".strip()
            continue
        name, sep, value = line.partition(":")
        if not sep:
            continue
        value = value.strip()
        key = name.strip() if value in BLOCK_SCALAR_MARKERS else ""
        fields[name.strip()] = "" if key else value.strip("\"'")
    return fields


def _generate_skills_table(skills_dir: Path) -> str:
    """skills_dir 아래 각 SKILL.md 의 name/description 으로 스킬 테이블을 생성한다.

    Returns:
        마크다운 테이블 문자열.
    """
    lines = [
        "| 스킬 | 설명 |",
        "|------|------|",
    ]
    for skill_md in sorted(skills_dir.glob(f"*/{SKILL_FILE}")):
        fields = _read_frontmatter(skill_md)
        name = fields.get("name")
        if not name:
            continue
        desc = fields.get("description", "").replace("|", "\\|")
        lines.append(f"| {name} | {desc} |")

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

    return {
        "project_dir": str(project_dir.resolve()),
        "project_name": project_dir.name,
        "languages": languages,
        "frameworks": frameworks,
        "structure": structure,
    }


def main(argv: list[str] | None = None) -> None:
    """CLI 엔트리 포인트. 분석 결과를 JSON(기본) 또는 AGENTS.md(--markdown)로 출력한다."""
    parser = argparse.ArgumentParser(description="프로젝트 구조 분석")
    parser.add_argument("project_dir", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--markdown", action="store_true", help="AGENTS.md 마크다운 출력")
    args = parser.parse_args(argv)
    project_dir: Path = args.project_dir

    if not project_dir.is_dir():
        print(
            json.dumps({"error": f"디렉토리를 찾을 수 없습니다: {project_dir}"}, ensure_ascii=False),
            file=sys.stderr,
        )
        sys.exit(1)

    result = analyze(project_dir)
    if args.markdown:
        print(
            generate_agents_md(
                project_dir.resolve(),
                result["languages"],
                result["frameworks"],
                result["structure"],
            )
        )
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
