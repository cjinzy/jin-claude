# agent 제거 계획

날짜: 2026-09-16

## 목표
jin-claude 플러그인에서 커스텀 agent 전부 제거. Claude Code 내장 Agent/Workflow 가 대체.

## 삭제
- plugins/jin-claude/agents/ (15 agent + templates 3)
- plugins/jin-claude/docs/AGENTS.md
- agent 디스패치 전용 skill 5: jin-orchestrator, jin-fsd, jin-maxwork, jin-ralph, jin-swe-fix

## 참조 정리
- hooks/keyword_detector.py: 5 skill 트리거 제거
- skills/jin-suggest, jin-deepinit(SKILL.md + project_analyzer.py + test): agent 추천 제거
- skills/jin-claude-init(SKILL.md, welcome.md): agent 표·동기화 단계 제거
- README.md(루트), plugins/jin-claude/README.md: agent 카탈로그·트리·카운트
- plugin.json, marketplace.json: description/keywords, version 3.0.10 → 4.0.0
- tests/test_jin_interview.py: agent 참조 확인
- sot/: 있으면 갱신

## 검증
- 전체 grep 으로 agent 이름 잔존 0 (jin-gcc `claude-agent` 는 perspective 이름, 예외)
- pytest tests/ + skills/jin-deepinit/scripts/test_project_analyzer.py
