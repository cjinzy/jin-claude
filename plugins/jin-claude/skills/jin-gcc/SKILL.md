---
name: jin-gcc
description: 다중 관점 분석 (GCC). codex/gemini CLI를 우선 시도하고, 없으면 Claude 에이전트로 다양한 관점의 분석을 제공합니다. "jin gcc", "다관점" 시 사용.
triggers:
  - jin gcc
  - 다관점
argument-hint: "[분석할 질문 또는 작업]"
---

# jin-gcc: 다중 관점 분석 (Gemini-Codex-Claude)

외부 AI CLI(codex, gemini)가 있으면 병렬 호출하고, 없으면 Claude 에이전트를 다양한 관점으로 분할하여 분석한다. 최종적으로 모든 관점을 종합하여 합의/충돌/권장 사항을 보고한다.

## 워크플로우

### Step 1: CLI Detection

Bash로 외부 CLI 존재 여부를 확인한다.

```bash
which codex 2>/dev/null && echo "codex:available" || echo "codex:unavailable"
which gemini 2>/dev/null && echo "gemini:available" || echo "gemini:unavailable"
```

- `codex:available` → codex CLI 사용 가능
- `gemini:available` → gemini CLI 사용 가능
- 둘 다 unavailable → Step 3 (Claude Fallback)으로 진행

### Step 2: External CLI Execution (CLI가 있는 경우)

사용 가능한 CLI마다 `Agent(run_in_background=true)`로 병렬 실행한다.

**codex 실행:**
```bash
echo "{user_prompt}" | codex --quiet
```

**gemini 실행:**
```bash
gemini "{user_prompt}"
```

- 각 CLI 출력을 수집한다.
- CLI가 하나만 있으면 그것만 실행하고, Claude 에이전트 1개를 추가로 병렬 실행하여 최소 2개 관점을 확보한다.
- 둘 다 있으면 codex + gemini + Claude 에이전트 1개 = 3개 관점을 확보한다.

### Step 3: Claude Fallback (CLI가 없는 경우)

외부 CLI가 모두 없으면, 5개 기본 관점 + 사용자 커스텀 관점으로 Claude 에이전트를 분할한다.

#### 기본 관점 (Default Perspectives)

| Perspective | Focus |
|-------------|-------|
| backend-architecture | 백엔드 아키텍처, 데이터 모델, API, 확장성 |
| frontend-ux | UX, 접근성, 반응성, 사용자 경험 |
| security | 보안 취약점, OWASP, 인증/인가 |
| side-effects | 부작용, 기존 기능 영향, 호환성 |
| performance | 성능, 메모리, 동시성, 캐싱 |

#### 관점 에이전트 프롬프트 템플릿

각 관점마다 `Agent(run_in_background=true)`를 생성하고 아래 프롬프트를 사용한다:

```
당신은 [{perspective_name}] 전문가입니다.
다음 질문/작업을 [{perspective_name}] 관점에서만 분석하세요:

## 질문
{user_prompt}

## 분석 요구사항
1. 이 관점에서의 핵심 고려사항 (3-5개)
2. 잠재적 위험 또는 주의사항
3. 구체적 권장 사항 (우선순위 순)
4. 다른 관점과의 트레이드오프
```

#### 사용자 커스텀 관점

사용자가 `관점:` 또는 `perspectives:` 접두사로 관점을 지정하면 기본 관점 대신 해당 관점을 사용한다.

예시:
```
jin gcc 관점: devops, cost, compliance 이 아키텍처를 검토해주세요
jin gcc perspectives: scalability, maintainability 이 설계를 분석해주세요
```

### Step 4: Synthesis (종합 보고서)

모든 관점의 출력을 수집한 뒤, 합의/충돌을 식별하고 아래 형식으로 통합 보고서를 작성한다.

#### 보고서 형식

```markdown
# 다중 관점 분석 보고서

## 분석 대상
{user_prompt 요약}

## 사용된 관점
| 관점 | 출처 |
|------|------|
| perspective_name | codex / gemini / claude-agent |

---

## 합의 사항
모든(또는 대다수) 관점에서 동의하는 사항:
- [ ] 합의 항목 1
- [ ] 합의 항목 2

## 충돌 사항
관점 간 의견이 다른 사항 및 트레이드오프 분석:

| 주제 | 관점 A | 관점 B | 트레이드오프 |
|------|--------|--------|-------------|
| topic | opinion_a | opinion_b | trade-off |

## 종합 권장 사항
우선순위 순으로 정리한 액션 아이템:
1. **[높음]** 권장 사항 1
2. **[중간]** 권장 사항 2
3. **[낮음]** 권장 사항 3

## 관점별 상세

### {perspective_name_1}
{해당 관점의 전체 분석 내용}

### {perspective_name_2}
{해당 관점의 전체 분석 내용}

(이하 반복)
```

## 관련 파일

- `skills/jin-gcc/SKILL.md` — 본 스킬 정의
- `skills/jin-cleanser/SKILL.md` — AI 슬롭 코드 리뷰 스킬 (보완적 사용)

## 주의사항

- 외부 CLI 실행 시 타임아웃은 120초로 설정한다.
- CLI 실행이 실패하면 해당 관점은 건너뛰고, 실패 사유를 보고서에 기록한다.
- 최소 2개 이상의 관점이 확보되어야 종합 보고서를 작성한다. 1개만 확보된 경우 단일 분석 결과를 반환한다.
- 병렬 실행으로 전체 분석 시간을 최소화한다.
