---
name: jin-suggest
description: 요청을 분석해 어떤 jin-claude 스킬·워크플로를 쓸지 우선순위와 함께 추천한다. "jin suggest", "어떤 스킬", "무슨 스킬", "뭐 써야", "jin 스킬 추천", "어떤 jin 명령" 처럼 jin-claude 스킬 선택을 물을 때 사용한다.
argument-hint: "[요청 내용]"
---

# jin-suggest

jin-claude 스킬만 추천한다 (외부 플러그인 제외). 구현·버그 수정 자체는 스킬이 아니라 Claude 가 직접 수행하는 단계로 표기한다.

호출명은 `/<skill>` 로 표기한다 (플러그인 정식 이름은 `/jin-claude:<skill>`).

## 스킬 매핑

| 의도 | 키워드 (한/영) | 추천 스킬 |
|------|---------------|----------|
| 환경 설정 | 초기화, 설정, 셋업, init, setup | `/jin-claude-init` |
| 프로젝트 분석 | 프로젝트 분석, AGENTS.md, deepinit | `/jin-deepinit` |
| SoT 문서 | sot, source of truth, 프로젝트 문서, 아키텍처 문서 | `/jin-sot-create` |
| 요구사항·설계 | 설계, 계획, 인터뷰, 요구사항, plan, spec | `/jin-interview` |
| 코딩 규칙 | 가이드라인, 과잉 구현 방지, 최소 변경, guidelines | `/guidelines` |
| 슬롭 정리 | 불필요 코드, 주석 정리, deslop, cleanup | `/jin-cleanser` |
| 세컨드 오피니언 | 리뷰, 검토, 반론, 다른 모델 의견, codex, review, challenge, consult | `/jin-codex-side` |
| 검증 스킬 관리 | 검증 스킬, 스킬 누락, skill 관리 | `/manage-skills` (사용자 직접 호출 전용) |
| 커밋 | 커밋, commit, 커밋 메시지 | `/jin-commit` |
| 스킬 선택 | 어떤 스킬, 뭐 써야 | `/jin-suggest` |

## 프로젝트 컨텍스트 보정

| 감지 | 보정 |
|------|------|
| `.git` 없음 | `/jin-commit` 제외 |
| `AGENTS.md` 있음 | `/jin-deepinit` 불필요 표시 |
| `sot/` 있음 | `/jin-sot-create` 불필요 표시 |

## 워크플로우

1. 요청 키워드를 매핑 표와 대조.
   - 한 의도에 매칭 → 바로 출력.
   - 복수·무매칭·인자 없음 → `AskUserQuestion` 으로 **1회만** 질문 (새 기능 / 버그 수정 / 리뷰·품질 / 프로젝트 설정 / 기타) 후 출력.
2. 컨텍스트 보정 적용.
3. 아래 형식으로 출력. 단일 스킬보다 다단계 워크플로를 우선 제시.

## 출력 형식

```markdown
## jin-suggest 추천 결과

| 우선순위 | 스킬 | 추천 이유 |
|---------|------|----------|
| 1 | `/jin-interview` | [이유] |
| 2 | `/jin-commit` | [이유] |

### 추천 워크플로우
1. `/jin-interview` → 요구사항 정리
2. 구현 (Claude 직접)
3. `/jin-commit` → 커밋
```

## 워크플로우 템플릿

| 시나리오 | 워크플로우 |
|---------|-----------|
| 신규 기능 | `/jin-interview` → 구현 → `/jin-cleanser` → `/jin-codex-side` → `/jin-commit` |
| 버그 수정 | 실패 테스트 작성 → 수정 → `/jin-codex-side` → `/jin-commit` |
| 프로젝트 시작 | `/jin-claude-init` → `/jin-deepinit` → `/jin-sot-create` |
| 코드 품질 개선 | `/jin-cleanser` → `/jin-codex-side` → `/jin-commit` |
| 대규모 리팩토링 | `/jin-interview` → 구현 → `/jin-codex-side` → `/manage-skills` → `/jin-commit` |
