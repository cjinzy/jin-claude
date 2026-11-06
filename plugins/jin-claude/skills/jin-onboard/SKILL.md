---
name: jin-onboard
argument-hint: "[상황: 새 프로젝트|기능|버그|큰 작업|리뷰|이슈|환경]"
description: jin-claude 사용 온보딩 — 상황별 워크플로(새 프로젝트·기능 개발·버그·큰 작업·리뷰·커밋·이슈·환경 유지)와 어떤 스킬을 언제 쓰는지 안내한다. jin-claude-init 완료 직후, 또는 "jin onboard", "온보딩", "사용법", "어떻게 써", "워크플로 안내", "뭐부터 해야" 요청 시 사용한다.
---

# jin-onboard

상황별로 jin-claude 를 쓰는 흐름을 안내한다.

**진행**: 인자 `$ARGUMENTS` 가 아래 상황 중 하나면 그 흐름만 보여준다. 비었으면 "기본 흐름" + 상황 목록을 보여주고, AskUserQuestion 으로 지금 하려는 일을 골라 그 흐름을 자세히 안내한다. 스킬은 키워드로 부르면 Claude 가 고르고(확정 아님), 확실히 실행하려면 `/jin-claude:<스킬>`.

## 기본 흐름 (모든 작업)
1. 세션은 **plan 모드**로 시작한다 (기본값, `Shift+Tab` 으로 전환). 계획 → 승인 → 실행.
2. plan 모드에서 ambition 계획 여부를 묻는다. 프롬프트에 `ambition` 을 쓰면 묻지 않고 적용.
3. 버그 수정은 실패하는 테스트 먼저 → 수정 → 통과 확인 (CLAUDE.md 규칙).
4. 끝은 실행 → 검증 → `jin commit` (커밋 메시지 추천 → 확인 후 커밋). push 는 직접.

## 새 프로젝트
1. `jin deepinit` — 프로젝트 분석 후 AGENTS.md 생성.
2. `jin sot` — SoT 문서셋(`sot/`) 생성. 아키텍처·스키마·규칙의 인용 가능한 출처.

## 기능 개발
1. 요구가 모호하면 `jin interview` — 질문으로 스펙 파일 확정.
2. plan 모드에서 계획. 범위·깊이를 키우려면 `ambition` (Altitude·Depth·Range, `/jin-claude:jin-ambition depth` 처럼 축 하나만도 가능).
3. 승인 후 구현 → 테스트.
4. `/code-review` 로 버그 리뷰, `/simplify` 로 정리 (Claude Code 내장).
5. `jin commit`.

## 버그
1. 재현하는 실패 테스트를 먼저 쓴다. 실패를 확인한다.
2. 원인을 고친다 (증상 말고). 테스트 통과를 확인한다.
3. 막히면 `jin codex challenge` 로 다른 모델의 반론 (Codex CLI 필요).

## 큰 작업 (여러 영역 · 병렬 · 장기)
- `/jin-claude:jin-maestro` — 이 세션은 계획·분배·보고만, 작업은 이름 붙은 하위 세션에 위임. 후속은 같은 세션에, 끝난 세션은 보관. `maestro 종료` 로 마침.
- 넓은 1회성 작업(전수 audit·일괄 변경·철저한 리뷰)은 프롬프트에 `ultracode` — 여러 에이전트 workflow 로 수행 (토큰 많이 씀).

## 리뷰 · 정리
- `jin codex review` — Codex 세컨드 오피니언.
- `jin cleanser` — AI 코드 슬롭 리포트.
- `/code-review` (깊이 `low`~`max`), 원격 다중 에이전트 리뷰는 `/code-review ultra` (유료).

## 이슈 (Linear)
- Linear 작업은 `mole-linear` 가 자동 적용 — 팀 규칙대로 이슈·댓글 작성. 라벨·상태 생성과 이슈 삭제는 하지 않는다.

## 환경 유지
- 새 버전 반영: `claude plugin update jin-claude@jin-claudecode-mp` 후 새 세션 (marketplace 저장소는 세션 시작 때 자동 갱신).
- `jin init` 재실행 (모두 설치돼 있으면) → "충돌 audit 만" 으로 설치 환경 충돌(MCP 중복·스킬 가림·알려진 충돌) 점검, "선택만 변경" 으로 선택 플러그인 변경.
- 검증 스킬 관리: `/jin-claude:manage-skills`.

## 스킬 표
| 스킬 | 부르기 | 용도 |
|------|--------|------|
| jin-onboard | `jin onboard` | 이 안내 |
| jin-interview | `jin interview` | 인터뷰 후 스펙 작성 |
| jin-ambition | plan 모드 질문 / `ambition` | 계획 3축 (Altitude·Depth·Range) |
| jin-maestro | `/jin-claude:jin-maestro` | 오케스트레이션 세션 |
| jin-deepinit | `jin deepinit` | AGENTS.md 생성 |
| jin-sot-create | `jin sot` | SoT 문서셋 |
| jin-codex-side | `jin codex` | Codex 세컨드 오피니언 |
| jin-cleanser | `jin cleanser` | AI 슬롭 리포트 |
| jin-commit | `jin commit` | gitmoji 커밋 |
| mole-linear | Linear 작업 시 자동 | Linear 팀 규칙 |
| manage-skills | `/jin-claude:manage-skills` | verify-* 스킬 관리 |
| jin-claude-init | `jin init` | 환경 (재)초기화 · 충돌 audit |
