---
name: jin-suggest
description: 사용자 요청에 가장 적합한 jin-claude 스킬과 에이전트를 추천합니다. "jin suggest", "추천", "뭐 써야", "어떤 스킬" 시 사용.
triggers:
  - jin suggest
  - 추천
  - 뭐 써야
  - 어떤 스킬
argument-hint: "[요청 내용]"
---

# jin-suggest: 스킬/에이전트 추천 엔진

## 목적

사용자 요청을 분석하여 jin-claude 플러그인의 스킬과 에이전트 중 가장 적합한 조합을 추천합니다.
명확한 요청은 즉시 추천(Quick Mode)하고, 모호한 요청은 1회 질문 후 추천(Interactive Mode)합니다.
jin-claude 전용 스킬/에이전트만 추천하며, 외부 플러그인(sc, superpowers 등)은 대상에서 제외합니다.

---

## 의도 카테고리 매핑 테이블

| 의도 카테고리 | 키워드 (한/영) | 추천 스킬 | 추천 에이전트 |
|--------------|---------------|----------|-------------|
| 환경설정 | 초기화, 설정, 셋업, init, setup | `jin-claude-init`, `jin-deepinit` | — |
| 계획/설계 | 설계, 계획, 인터뷰, 요구사항, plan, spec | `jin-interview` | `jin-interview-agent` |
| 구현/개발 | 구현, 개발, 만들어, implement, build, feature | `jin-orchestrator`, `jin-fsd`, `jin-maxwork` | `python-expert`, `swe-agent` |
| 버그수정 | 버그, 수정, 에러, fix, bug, error, issue | `jin-swe-fix`, `jin-ralph` | `swe-agent`, `swe-agent-high` |
| 코드리뷰/분석 | 리뷰, 분석, 검토, review, analyze, check | `jin-gcc`, `jin-cleanser`, `verify-implementation` | `swe-analyst` |
| 커밋/배포 | 커밋, 배포, commit, deploy | `jin-commit` | — |
| API 문서 | API 문서, 라이브러리 문서, chub, context-hub | `jin-chub` | — |
| CTI/보안 | 위협, 보안, CTI, threat, malware, 다크웹 | — | `mole-review-agent` (파이프라인) |

---

## 프로젝트 컨텍스트 감지

파일 시스템을 기반으로 프로젝트 유형을 경량 감지하여 추천을 보정합니다.

| 파일/디렉토리 | 감지 결과 | 추가 추천 |
|--------------|----------|----------|
| `pyproject.toml` | Python 프로젝트 | `py-standard` 스킬 추가 추천 |
| `package.json` | Node.js/React 프로젝트 | 프론트엔드 관련 안내 |
| `.git` | Git 저장소 | `jin-commit` 활성화 |
| `AGENTS.md` | 이미 초기화됨 | `jin-deepinit` 불필요로 표시 |
| `tests/` 또는 `test/` | 테스트 존재 | 검증 스킬 우선 추천 |

---

## 워크플로우

### 1단계: 의도 분류

사용자 입력에서 키워드를 추출하여 위 매핑 테이블과 대조합니다.

- **단일 카테고리 매칭** → Quick Mode로 진행
- **복수 카테고리 매칭** 또는 **매칭 없음** → Interactive Mode로 진행

### 2단계-A: Quick Mode (명확한 의도)

즉시 추천 테이블을 출력합니다. 추가 질문 없이 바로 결과를 제공합니다.

### 2단계-B: Interactive Mode (모호한 의도)

`AskUserQuestion`을 사용하여 **1회만** 객관식 질문을 합니다.

질문 형식:
```
어떤 작업을 하려고 하시나요?

1. 새 기능 구현
2. 버그 수정
3. 코드 리뷰/품질 개선
4. 프로젝트 초기 설정
5. 기타 (직접 설명)
```

사용자 응답을 기반으로 카테고리를 확정한 뒤 Quick Mode와 동일하게 출력합니다.

### 3단계: 출력

아래 출력 형식에 따라 결과를 표시합니다.

---

## 출력 형식

```markdown
## 🔍 jin-suggest 추천 결과

### 추천 스킬
| 우선순위 | 스킬 | 트리거 | 추천 이유 |
|---------|------|--------|----------|
| 1 | `jin-orchestrator` | `jin orchestrate` | [이유] |
| 2 | `jin-interview` | `jin interview` | [이유] |

### 추천 워크플로우
> 1. `jin interview` → 요구사항 정리
> 2. `jin orchestrate` → 멀티 에이전트 구현
> 3. `jin commit` → 커밋

### 관련 에이전트
| 에이전트 | 모델 | 역할 |
|----------|------|------|
| `python-expert` | sonnet | Python 전문 개발 |
```

---

## 워크플로우 템플릿

시나리오별 최적 워크플로우를 사전 정의합니다.

| 시나리오 | 워크플로우 |
|---------|-----------|
| 신규 기능 개발 | `jin-interview` → `jin-orchestrator` / `jin-fsd` → `jin-cleanser` → `jin-commit` |
| 버그 수정 | `jin-swe-fix` → (실패 시 `jin-ralph`) → `jin-commit` |
| 프로젝트 시작 | `jin-claude-init` → `jin-deepinit` → `jin-interview` |
| 코드 품질 개선 | `jin-cleanser` → `jin-gcc` → `verify-implementation` → `jin-commit` |
| 대규모 리팩토링 | `jin-interview` → `jin-maxwork` → `verify-implementation` → `jin-commit` |
| CTI 조사 | `mole-review-agent` (파이프라인 오케스트레이션) |

---

## 복잡도별 에이전트 선택 가이드

작업 복잡도에 따라 적절한 에이전트를 선택합니다.

| 복잡도 | 기준 | 추천 에이전트 | 모델 |
|--------|------|-------------|------|
| LOW | 1 파일, 단순 변경 | `swe-agent` | sonnet |
| MEDIUM | 1-2 파일, 로직 변경 | `swe-agent` | sonnet |
| HIGH | 3+ 파일, 교차 모듈 | `swe-agent-high` | opus |

복잡도 판단 기준:
- **LOW**: 오타 수정, 설정값 변경, 단순 추가
- **MEDIUM**: 함수/메서드 수정, 단일 모듈 로직 변경
- **HIGH**: 다중 모듈 수정, 아키텍처 변경, 교차 의존성 수정

---

## 예외사항

1. **외부 플러그인 제외**: `sc:*`, `superpowers:*` 등 외부 플러그인 스킬은 추천하지 않습니다.
2. **인자 없는 호출**: 인자 없이 `jin suggest`만 호출하면 Interactive Mode로 진입합니다.
3. **복수 추천**: 하나의 요청에 여러 스킬이 해당될 수 있습니다. 우선순위를 매겨 모두 표시합니다.
4. **워크플로우 우선**: 단일 스킬보다 다단계 워크플로우를 우선 추천하여 전체 작업 흐름을 안내합니다.
5. **컨텍스트 보정**: 프로젝트 감지 결과에 따라 추천을 자동 보정합니다 (예: Python 프로젝트에서 `py-standard` 자동 추가).
