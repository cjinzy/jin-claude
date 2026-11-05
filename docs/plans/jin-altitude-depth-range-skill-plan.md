# jin-altitude · jin-depth · jin-range 스킬 계획 (검토안)

출처: Felix Rieseberg, "How to be more ambitious: A tutorial for humans with models" (2026-10-13)
https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/

## 글 요약 — 야망 4축
| 축 | 뜻 | 핵심 기법 |
|---|---|---|
| Speed | 같은 일 더 빨리 | (생략 — 기본) |
| Altitude | 작업이 아닌 결과를 맡김 ("목표 너머의 목표") | 단계적 상향 (숫자 갱신 → 결정 3개 → 프로세스 재설계 + 과거 데이터로 증명 + 병행 운영). 사람 없는 지속 워크플로 = 접근 권한·재현 환경 먼저 |
| Depth | 업계 최고 전문가처럼 | 전문가 도구 강요(표 대신 DB·통계), 비합리적 목표, 가정 반증, 새 지식 생산, **외부 판정자** (자기 평가 금지) |
| Range | 여러 분야 동원 | 명사 → 동사 ("덱" → "30분 안에 바쁜 사람이 인과를 믿고 결정하게"), 팀 구성 → 분야·기법 도출. **역할극 금지: 그 직업처럼 쓰지 말고 그 직업이 하는 일을 하라** |

## 기존 스킬과 겹침
- `pstack:sharpen` (개인 설치, 팀 미배포): Depth 4질문(원자료·방법·외부 검증)과 "사용자가 진짜 원하는 것"을 이미 담음. 프롬프트를 돌려주지 않고 바로 실행.
- 빠진 것: Altitude 상향 사다리·지속 워크플로 전제조건, Range 전부, 사용자에게 야망 수준을 고르게 하는 단계.

## 설계 — 3개 스킬로 분리
호출 시점이 다름 → 분리. 모델이 로드해야 하므로 `disable-model-invocation` 은 쓰지 않는다. description 은 "ambition 계획 작성 시" 로 한정.

### 진입: UserPromptSubmit hook (`hooks/ambition_plan.py`)
```
prompt 에 "ambition"/"앰비션"  ──▶ LOAD 주입 (모드 무관, 묻지 않음)
permission_mode == "plan"      ──▶ ASK 주입 (이 대화에서 미결정일 때만 AskUserQuestion → 예면 LOAD)
그 외                          ──▶ 출력 없음
```
- LOAD: Skill 도구로 `jin-claude:jin-altitude`·`jin-depth`·`jin-range` 로드 → 계획에 `## Ambition` 섹션 (Altitude/Depth/Range, 해당 없으면 `N/A — 이유`).
- 중복 질문 방지는 상태 파일 없이 "이 대화에서 이미 정했으면 따른다" 지시로 (모델이 대화 기억).
- 실패 시 출력 없이 exit 0 — 프롬프트를 절대 막지 않는다.
- 한계: 대화 중 모델이 스스로 EnterPlanMode 하면 그 턴의 permission_mode 는 plan 이 아님 → 다음 프롬프트부터 적용.
- 하드 게이트(plan 확정 거부)는 이번 범위 밖.
공통 규칙(각 스킬에 한 줄 중복): 결과 검증은 외부 판정자(테스트·도구·원데이터) — 모델 자기 평가 금지.

| 스킬 | 쓰는 때 | 동작 |
|---|---|---|
| `jin-altitude` | 결과·지속 워크플로를 맡길 때 | 목표 너머의 목표를 2–3단 사다리로 제시 → 사용자가 단 선택 → 그 결과를 사람 없이 유지하는 데 필요한 접근 권한·데이터·재현/검증 환경 점검 → 부족분 먼저 보고 |
| `jin-depth` | 작업 하나를 최고 수준으로 | 최고 전문가가 할 일 / 원자료 / 방법·도구 / 외부 판정 4개 답 → 그 기준으로 작업. 표 대신 DB·통계 등 실제 도구 강제, 핵심 가정 하나를 원자료로 반증 시도 |
| `jin-range` | 접근법을 넓히고 싶을 때 | 작업을 동사로 재서술 → 기여할 분야 2–4개와 각 분야가 실제로 하는 일(역할극 금지) + red team 1개 → 사용자가 채택할 기법 선택 → 적용 |

- 제외: "비합리적 목표" 강요 — agent 환경에선 토큰 낭비·거짓 성공 위험. 외부 판정자가 있을 때만 목표 상향.
- 크기: 각 SKILL.md 40줄 이내, 스크립트 없음.

## 미결정
- `jin-depth` 는 pstack:sharpen 과 상당 부분 중복 — 팀원은 pstack 없음 → 유지 권장.
