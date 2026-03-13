"""project_analyzer 모듈 테스트 스위트.

프로젝트 구조 분석, 프레임워크 감지, 에이전트 추천 기능을
임시 디렉토리를 활용하여 검증한다.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from project_analyzer import (
    detect_frameworks,
    detect_languages,
    detect_structure,
    generate_agents_md,
    recommend_agents,
)


class TestDetectLanguages:
    """언어 감지 기능 테스트."""

    def test_python_only_project(self, tmp_path: Path) -> None:
        """Python 파일만 있는 프로젝트에서 Python을 감지한다."""
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "utils.py").write_text("def helper(): pass")
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_main.py").write_text("def test(): pass")

        languages = detect_languages(tmp_path)

        assert languages == ["Python"]

    def test_mixed_project(self, tmp_path: Path) -> None:
        """여러 언어가 혼합된 프로젝트에서 빈도순으로 반환한다."""
        # Python 파일 3개
        (tmp_path / "app.py").write_text("")
        (tmp_path / "utils.py").write_text("")
        (tmp_path / "models.py").write_text("")
        # TypeScript 파일 2개
        (tmp_path / "index.ts").write_text("")
        (tmp_path / "component.tsx").write_text("")
        # JavaScript 파일 1개
        (tmp_path / "config.js").write_text("")

        languages = detect_languages(tmp_path)

        assert languages[0] == "Python"
        assert "TypeScript" in languages
        assert "JavaScript" in languages

    def test_empty_project(self, tmp_path: Path) -> None:
        """빈 프로젝트에서 빈 목록을 반환한다."""
        languages = detect_languages(tmp_path)

        assert languages == []

    def test_ignores_hidden_directories(self, tmp_path: Path) -> None:
        """숨김 디렉토리(.git 등)의 파일은 무시한다."""
        (tmp_path / "main.py").write_text("")
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "hooks.py").write_text("")
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()
        (venv_dir / "lib.py").write_text("")

        languages = detect_languages(tmp_path)

        assert languages == ["Python"]

    def test_ignores_node_modules(self, tmp_path: Path) -> None:
        """node_modules 디렉토리의 파일은 무시한다."""
        (tmp_path / "index.ts").write_text("")
        nm_dir = tmp_path / "node_modules"
        nm_dir.mkdir()
        (nm_dir / "lodash.js").write_text("")
        (nm_dir / "react.js").write_text("")

        languages = detect_languages(tmp_path)

        assert languages == ["TypeScript"]


class TestDetectFrameworks:
    """프레임워크 감지 기능 테스트."""

    def test_pyproject_with_fastapi(self, tmp_path: Path) -> None:
        """pyproject.toml에서 FastAPI를 감지한다."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[project]\n'
            'name = "myapp"\n'
            'dependencies = [\n'
            '    "fastapi>=0.100.0",\n'
            '    "uvicorn",\n'
            '    "sqlalchemy>=2.0",\n'
            ']\n'
        )

        frameworks = detect_frameworks(tmp_path)

        assert "fastapi" in frameworks
        assert frameworks["fastapi"] == "FastAPI"

    def test_package_json_with_react(self, tmp_path: Path) -> None:
        """package.json에서 React를 감지한다."""
        pkg = tmp_path / "package.json"
        pkg.write_text(json.dumps({
            "name": "my-app",
            "dependencies": {
                "react": "^18.0.0",
                "react-dom": "^18.0.0",
            },
            "devDependencies": {
                "vite": "^5.0.0",
            },
        }))

        frameworks = detect_frameworks(tmp_path)

        assert "react" in frameworks
        assert frameworks["react"] == "React"
        assert "vite" in frameworks
        assert frameworks["vite"] == "Vite"

    def test_no_config_files(self, tmp_path: Path) -> None:
        """설정 파일이 없으면 빈 딕셔너리를 반환한다."""
        (tmp_path / "main.py").write_text("")

        frameworks = detect_frameworks(tmp_path)

        assert frameworks == {}

    def test_cargo_toml_indicator(self, tmp_path: Path) -> None:
        """Cargo.toml 존재 시 Rust를 감지한다."""
        (tmp_path / "Cargo.toml").write_text('[package]\nname = "myapp"\n')

        frameworks = detect_frameworks(tmp_path)

        assert "Cargo.toml" in frameworks
        assert frameworks["Cargo.toml"] == "Rust (Cargo)"

    def test_go_mod_indicator(self, tmp_path: Path) -> None:
        """go.mod 존재 시 Go를 감지한다."""
        (tmp_path / "go.mod").write_text("module example.com/myapp\ngo 1.21\n")

        frameworks = detect_frameworks(tmp_path)

        assert "go.mod" in frameworks
        assert frameworks["go.mod"] == "Go Modules"


class TestDetectStructure:
    """프로젝트 구조 유형 감지 테스트."""

    def test_monorepo_with_packages(self, tmp_path: Path) -> None:
        """packages/ 디렉토리가 있고 하위 패키지가 2개 이상이면 monorepo로 판별한다."""
        packages = tmp_path / "packages"
        packages.mkdir()
        (packages / "frontend").mkdir()
        (packages / "frontend" / "package.json").write_text("{}")
        (packages / "backend").mkdir()
        (packages / "backend" / "package.json").write_text("{}")

        structure = detect_structure(tmp_path)

        assert structure == "monorepo"

    def test_monorepo_with_multiple_package_json(self, tmp_path: Path) -> None:
        """루트 하위에 복수의 package.json이 있으면 monorepo로 판별한다."""
        svc_a = tmp_path / "service-a"
        svc_a.mkdir()
        (svc_a / "package.json").write_text("{}")
        svc_b = tmp_path / "service-b"
        svc_b.mkdir()
        (svc_b / "package.json").write_text("{}")

        structure = detect_structure(tmp_path)

        assert structure == "monorepo"

    def test_standard_with_src_tests(self, tmp_path: Path) -> None:
        """src/ 및 tests/ 디렉토리가 있으면 standard로 판별한다."""
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "pyproject.toml").write_text("")

        structure = detect_structure(tmp_path)

        assert structure == "standard"

    def test_flat_structure(self, tmp_path: Path) -> None:
        """표준 디렉토리가 없고 모든 파일이 루트에 있으면 flat으로 판별한다."""
        (tmp_path / "main.py").write_text("")
        (tmp_path / "utils.py").write_text("")
        (tmp_path / "config.json").write_text("{}")

        structure = detect_structure(tmp_path)

        assert structure == "flat"


class TestRecommendAgents:
    """에이전트 추천 기능 테스트."""

    def test_python_project_recommends_python_expert(self) -> None:
        """Python 프로젝트에서 python-expert를 추천한다."""
        agents = recommend_agents(
            languages=["Python"],
            frameworks={"fastapi": "FastAPI"},
            structure="standard",
        )
        agent_names = [a["agent"] for a in agents]

        assert "python-expert" in agent_names
        assert "swe-agent" in agent_names

    def test_complex_project_recommends_orchestrator(self) -> None:
        """복잡한 프로젝트(monorepo)에서 orchestrator를 추천한다."""
        agents = recommend_agents(
            languages=["Python", "TypeScript", "JavaScript"],
            frameworks={"react": "React", "fastapi": "FastAPI"},
            structure="monorepo",
        )
        agent_names = [a["agent"] for a in agents]

        assert "jin-orchestrator" in agent_names
        assert "jin-maxwork" in agent_names

    def test_always_recommends_base_agents(self) -> None:
        """모든 프로젝트에서 기본 에이전트(온보딩, 인터뷰, 분석)를 추천한다."""
        agents = recommend_agents(
            languages=[],
            frameworks={},
            structure="flat",
        )
        agent_names = [a["agent"] for a in agents]

        assert "jin-claude-init" in agent_names
        assert "jin-interview-agent" in agent_names
        assert "swe-analyst" in agent_names

    def test_no_duplicate_agents(self) -> None:
        """동일 에이전트가 중복 추천되지 않는다."""
        agents = recommend_agents(
            languages=["Python", "TypeScript", "JavaScript", "Go"],
            frameworks={"fastapi": "FastAPI", "react": "React"},
            structure="monorepo",
        )
        agent_names = [a["agent"] for a in agents]

        assert len(agent_names) == len(set(agent_names))


class TestGenerateAgentsMd:
    """AGENTS.md 생성 기능 테스트."""

    def test_valid_markdown_output(self, tmp_path: Path) -> None:
        """유효한 마크다운 형식의 출력을 생성한다."""
        agents = [
            {
                "agent": "python-expert",
                "model": "sonnet",
                "reason": "Python 전문 코딩",
                "example": '"이 함수를 리팩토링해줘"',
            },
        ]

        md = generate_agents_md(
            project_dir=tmp_path,
            languages=["Python"],
            frameworks={"fastapi": "FastAPI"},
            structure="standard",
            agents=agents,
        )

        assert md.startswith("# AGENTS.md")
        assert "## 프로젝트 개요" in md
        assert "## 추천 에이전트" in md
        assert "## 사용 가능한 스킬" in md

    def test_contains_agent_table(self, tmp_path: Path) -> None:
        """에이전트 테이블에 추천 에이전트가 포함된다."""
        agents = [
            {
                "agent": "python-expert",
                "model": "sonnet",
                "reason": "Python 전문 코딩",
                "example": '"이 함수를 리팩토링해줘"',
            },
            {
                "agent": "swe-agent",
                "model": "sonnet",
                "reason": "버그 수정",
                "example": '"jin swe [이슈 설명]"',
            },
        ]

        md = generate_agents_md(
            project_dir=tmp_path,
            languages=["Python"],
            frameworks={},
            structure="standard",
            agents=agents,
        )

        assert "python-expert" in md
        assert "swe-agent" in md
        assert "| 에이전트 | 모델 | 추천 이유 | 사용 예시 |" in md

    def test_contains_project_info(self, tmp_path: Path) -> None:
        """프로젝트 개요에 언어, 프레임워크, 구조 정보가 포함된다."""
        md = generate_agents_md(
            project_dir=tmp_path,
            languages=["Python", "TypeScript"],
            frameworks={"fastapi": "FastAPI", "react": "React"},
            structure="monorepo",
            agents=[],
        )

        assert "Python, TypeScript" in md
        assert "FastAPI" in md
        assert "React" in md
        assert "Monorepo" in md

    def test_empty_project_shows_not_detected(self, tmp_path: Path) -> None:
        """언어/프레임워크가 없으면 '감지되지 않음'을 표시한다."""
        md = generate_agents_md(
            project_dir=tmp_path,
            languages=[],
            frameworks={},
            structure="flat",
            agents=[],
        )

        assert "감지되지 않음" in md
