"""Tests for jin-interview skill and jin-interview-agent.

Validates:
- Skill YAML frontmatter parsing
- Required interview phases exist
- Agent file structure and frontmatter
- Spec output format template
- File synchronization between ~/.claude and project repo
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# --- Path Constants ---

PROJECT_ROOT = Path(__file__).parent.parent
HOME_CLAUDE = Path.home() / ".claude"

SKILL_PATHS = [
    PROJECT_ROOT / ".claude" / "skills" / "jin-interview" / "SKILL.md",
    HOME_CLAUDE / "skills" / "jin-interview" / "SKILL.md",
]

AGENT_PATHS = [
    PROJECT_ROOT / ".claude" / "agents" / "jin-interview-agent.md",
    HOME_CLAUDE / "agents" / "jin-interview-agent.md",
]

AGENTS_MD_PATHS = [
    PROJECT_ROOT / ".claude" / "agents" / "AGENTS.md",
    HOME_CLAUDE / "agents" / "AGENTS.md",
]


def _parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from a markdown file using regex.

    Handles simple key-value pairs, multi-line strings (using >),
    and list values (using [a, b, c] syntax).
    Does not require pyyaml dependency.

    Args:
        content: The full markdown file content.

    Returns:
        Parsed YAML frontmatter as a dictionary.

    Raises:
        ValueError: If no valid YAML frontmatter is found.
    """
    match = re.match(r"^---\n(.+?)\n---", content, re.DOTALL)
    if not match:
        msg = "No YAML frontmatter found"
        raise ValueError(msg)

    raw = match.group(1)
    result: dict = {}
    current_key: str | None = None
    multiline_value = ""

    for line in raw.split("\n"):
        # Multi-line continuation (indented line after key with >)
        if current_key and line.startswith("  "):
            multiline_value += line.strip() + " "
            continue
        if current_key and multiline_value:
            result[current_key] = multiline_value.strip()
            current_key = None
            multiline_value = ""

        # Key-value pair
        kv_match = re.match(r'^(\S[\w-]*)\s*:\s*(.*)', line)
        if kv_match:
            key = kv_match.group(1)
            value = kv_match.group(2).strip()

            if value == ">":
                # Multi-line string follows
                current_key = key
                multiline_value = ""
            elif value.startswith("[") and value.endswith("]"):
                # List value: [a, b, c]
                items = [item.strip() for item in value[1:-1].split(",")]
                result[key] = items
            elif value.startswith('"') and value.endswith('"'):
                result[key] = value[1:-1]
            else:
                result[key] = value

    # Flush remaining multi-line value
    if current_key and multiline_value:
        result[current_key] = multiline_value.strip()

    return result


# --- Skill YAML Frontmatter Tests ---


class TestSkillFrontmatter:
    """Tests for jin-interview skill YAML frontmatter parsing."""

    @pytest.fixture(params=SKILL_PATHS, ids=["project", "home"])
    def skill_path(self, request: pytest.FixtureRequest) -> Path:
        """Parametrized fixture for skill file paths."""
        path = request.param
        if not path.exists():
            pytest.skip(f"Skill file not found: {path}")
        return path

    def test_skill_file_exists(self, skill_path: Path) -> None:
        """Skill SKILL.md file should exist."""
        assert skill_path.exists(), f"Missing: {skill_path}"

    def test_frontmatter_is_valid_yaml(self, skill_path: Path) -> None:
        """YAML frontmatter should parse without errors."""
        content = skill_path.read_text(encoding="utf-8")
        frontmatter = _parse_frontmatter(content)
        assert isinstance(frontmatter, dict)

    def test_name_is_zy_interview(self, skill_path: Path) -> None:
        """Skill name must be 'jin-interview', not 'mole-interview'."""
        content = skill_path.read_text(encoding="utf-8")
        frontmatter = _parse_frontmatter(content)
        assert frontmatter["name"] == "jin-interview"

    def test_has_description(self, skill_path: Path) -> None:
        """Skill must have a description field."""
        content = skill_path.read_text(encoding="utf-8")
        frontmatter = _parse_frontmatter(content)
        assert "description" in frontmatter
        assert len(frontmatter["description"]) > 10

    def test_has_allowed_tools(self, skill_path: Path) -> None:
        """Skill must declare allowed-tools."""
        content = skill_path.read_text(encoding="utf-8")
        frontmatter = _parse_frontmatter(content)
        assert "allowed-tools" in frontmatter
        tools = frontmatter["allowed-tools"]
        # AskUserQuestion is essential for interview
        assert "AskUserQuestion" in tools


# --- Required Interview Phases Tests ---


class TestInterviewPhases:
    """Tests for required interview phases in the skill."""

    REQUIRED_PHASES = [
        ("Phase 0", "작업 분류"),
        ("Phase 1", "스코프"),
        ("Phase 2", "기술적 결정"),
        ("Phase 3", "제약"),
        ("Phase 4", "엣지 케이스"),
        ("Phase 5", "테스트"),
        ("Phase 6", "우선순위"),
    ]

    @pytest.fixture()
    def skill_content(self) -> str:
        """Read skill content from project repo."""
        path = PROJECT_ROOT / ".claude" / "skills" / "jin-interview" / "SKILL.md"
        if not path.exists():
            pytest.skip("Skill file not found in project repo")
        return path.read_text(encoding="utf-8")

    @pytest.mark.parametrize(
        ("phase_id", "phase_keyword"),
        [
            ("Phase 0", "작업 분류"),
            ("Phase 1", "스코프"),
            ("Phase 2", "기술적 결정"),
            ("Phase 3", "제약"),
            ("Phase 4", "엣지 케이스"),
            ("Phase 5", "테스트"),
            ("Phase 6", "우선순위"),
        ],
        ids=[f"phase-{i}" for i in range(7)],
    )
    def test_phase_exists(
        self, skill_content: str, phase_id: str, phase_keyword: str
    ) -> None:
        """Each required phase must appear in the skill document."""
        assert phase_id in skill_content, f"Missing {phase_id} in skill"
        assert phase_keyword in skill_content, f"Missing keyword '{phase_keyword}' for {phase_id}"

    def test_spec_output_section(self, skill_content: str) -> None:
        """Skill must define a spec output section."""
        assert "Spec Output" in skill_content or "스펙" in skill_content
        assert ".jin/specs/" in skill_content

    def test_core_principles_section(self, skill_content: str) -> None:
        """Skill must define core principles."""
        assert "Core Principles" in skill_content or "핵심 원칙" in skill_content

    def test_early_termination_rules(self, skill_content: str) -> None:
        """Skill must define early termination conditions."""
        assert "조기 종료" in skill_content or "충분하다" in skill_content


# --- Agent File Structure Tests ---


class TestAgentStructure:
    """Tests for jin-interview-agent file structure and frontmatter."""

    @pytest.fixture(params=AGENT_PATHS, ids=["project", "home"])
    def agent_path(self, request: pytest.FixtureRequest) -> Path:
        """Parametrized fixture for agent file paths."""
        path = request.param
        if not path.exists():
            pytest.skip(f"Agent file not found: {path}")
        return path

    def test_agent_file_exists(self, agent_path: Path) -> None:
        """Agent .md file should exist."""
        assert agent_path.exists(), f"Missing: {agent_path}"

    def test_frontmatter_is_valid_yaml(self, agent_path: Path) -> None:
        """YAML frontmatter should parse without errors."""
        content = agent_path.read_text(encoding="utf-8")
        frontmatter = _parse_frontmatter(content)
        assert isinstance(frontmatter, dict)

    def test_agent_name(self, agent_path: Path) -> None:
        """Agent name must be 'jin-interview-agent'."""
        content = agent_path.read_text(encoding="utf-8")
        frontmatter = _parse_frontmatter(content)
        assert frontmatter["name"] == "jin-interview-agent"

    def test_model_is_sonnet(self, agent_path: Path) -> None:
        """Agent model should be sonnet for speed/quality balance."""
        content = agent_path.read_text(encoding="utf-8")
        frontmatter = _parse_frontmatter(content)
        assert frontmatter["model"] == "sonnet"

    def test_has_required_tools(self, agent_path: Path) -> None:
        """Agent must declare required tools."""
        content = agent_path.read_text(encoding="utf-8")
        frontmatter = _parse_frontmatter(content)
        tools = frontmatter["tools"]
        required = {"AskUserQuestion", "Read", "Glob", "Grep", "Write"}
        assert required.issubset(set(tools)), f"Missing tools: {required - set(tools)}"

    def test_has_role_section(self, agent_path: Path) -> None:
        """Agent must have a Role section."""
        content = agent_path.read_text(encoding="utf-8")
        assert "## Role" in content or "# jin-interview-agent" in content

    def test_has_constraints_section(self, agent_path: Path) -> None:
        """Agent must have a Constraints section."""
        content = agent_path.read_text(encoding="utf-8")
        assert "## Constraints" in content

    def test_no_code_modification_constraint(self, agent_path: Path) -> None:
        """Agent must explicitly forbid code writing/modification."""
        content = agent_path.read_text(encoding="utf-8")
        assert "코드 작성" in content or "코드" in content
        assert "금지" in content

    def test_pipeline_position(self, agent_path: Path) -> None:
        """Agent must describe its pipeline position."""
        content = agent_path.read_text(encoding="utf-8")
        assert "Pipeline" in content or "pipeline" in content
        assert ".jin/specs/" in content


# --- Spec Output Format Tests ---


class TestSpecOutputFormat:
    """Tests for the spec output format template in the skill."""

    @pytest.fixture()
    def skill_content(self) -> str:
        """Read skill content from project repo."""
        path = PROJECT_ROOT / ".claude" / "skills" / "jin-interview" / "SKILL.md"
        if not path.exists():
            pytest.skip("Skill file not found in project repo")
        return path.read_text(encoding="utf-8")

    REQUIRED_SPEC_SECTIONS = [
        "Overview",
        "Requirements",
        "Technical Decisions",
        "Constraints",
        "Edge Cases",
        "Acceptance Criteria",
        "Test Plan",
        "Open Questions",
    ]

    @pytest.mark.parametrize("section", REQUIRED_SPEC_SECTIONS)
    def test_spec_template_has_section(self, skill_content: str, section: str) -> None:
        """Spec output template must include all required sections."""
        assert section in skill_content, f"Missing spec section: {section}"

    def test_spec_output_path_format(self, skill_content: str) -> None:
        """Spec output path must follow .jin/specs/{task-name}-spec.md pattern."""
        assert ".jin/specs/" in skill_content
        assert "-spec.md" in skill_content


# --- AGENTS.md Registry Tests ---


class TestAgentsRegistry:
    """Tests for AGENTS.md containing jin-interview-agent entry."""

    @pytest.fixture(params=AGENTS_MD_PATHS, ids=["project", "home"])
    def agents_md_content(self, request: pytest.FixtureRequest) -> str:
        """Read AGENTS.md content."""
        path = request.param
        if not path.exists():
            pytest.skip(f"AGENTS.md not found: {path}")
        return path.read_text(encoding="utf-8")

    def test_agent_listed_in_key_files(self, agents_md_content: str) -> None:
        """jin-interview-agent must appear in AGENTS.md."""
        assert "jin-interview-agent" in agents_md_content

    def test_interview_category_exists(self, agents_md_content: str) -> None:
        """Interview category must exist in Agent Categories."""
        assert "Interview" in agents_md_content


# --- File Synchronization Tests ---


class TestFileSynchronization:
    """Tests that files are synchronized between ~/.claude and project repo."""

    def test_skill_files_match(self) -> None:
        """Skill SKILL.md should be identical in both locations."""
        project = PROJECT_ROOT / ".claude" / "skills" / "jin-interview" / "SKILL.md"
        home = HOME_CLAUDE / "skills" / "jin-interview" / "SKILL.md"
        if not project.exists() or not home.exists():
            pytest.skip("One or both skill files not found")
        assert project.read_text(encoding="utf-8") == home.read_text(encoding="utf-8")

    def test_agent_files_match(self) -> None:
        """Agent .md should be identical in both locations."""
        project = PROJECT_ROOT / ".claude" / "agents" / "jin-interview-agent.md"
        home = HOME_CLAUDE / "agents" / "jin-interview-agent.md"
        if not project.exists() or not home.exists():
            pytest.skip("One or both agent files not found")
        assert project.read_text(encoding="utf-8") == home.read_text(encoding="utf-8")
