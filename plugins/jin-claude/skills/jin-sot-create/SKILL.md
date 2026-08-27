---
name: jin-sot-create
description: SoT(Source of Truth) 디렉토리 구조 생성 — sot/ 카테고리 디렉토리 + Index.md
triggers:
  - jin sot
  - sot create
  - SoT 생성
  - source of truth
argument-hint: "[프로젝트 경로 (기본: 현재 디렉토리)]"
---

# jin-sot-create: SoT 디렉토리 구조 생성

프로젝트 루트에 SoT(Source of Truth) 문서 구조를 생성한다.

## SoT 카테고리

1. overview — 어떤 프로젝트인지 설명
2. tech-stack — 어떤 기술 스택으로 개발했는지 설명
3. database-schema — DB 스키마 (Excel 컬럼 정의, 시트 + 컬럼 정의)
4. architecture — 아키텍처 구성요소
5. workflow — 어떻게 동작하는지
6. rules — 규칙 등 기타

## 생성 구조

```
sot/
├── Index.md                  # 색인 — 모든 문서 링크
├── overview/
│   └── project.md
├── tech-stack/
│   └── stack.md
├── database-schema/
│   └── schema.md
├── architecture/
│   └── components.md
├── workflow/
│   └── how-it-works.md
└── rules/
    └── guidelines.md
```

## 워크플로우

### Step 0: jin-interview 호출 (필수)

SoT 생성 전에 jin-interview 스킬을 먼저 호출하여 인터뷰를 진행한다. 모호한 프로젝트 설명을 구체적 spec 문서로 변환한 후에 작성을 시작한다. 인터뷰 없이 바로 템플릿을 생성하지 않는다.

### Step 1: 중복 확인

- sot/ 없음 → Step 2로 진행
- sot/ 있음 → 기존 파일 유지, 누락된 카테고리만 추가하고 Index.md 재생성

### Step 2: 디렉토리 생성

```bash
mkdir -p sot/overview sot/tech-stack sot/database-schema sot/architecture sot/workflow sot/rules
```

### Step 3: 템플릿 생성

각 카테고리에 .md 파일 생성. 인터뷰에서 수집한 정보를 기반으로 섹션 골격을 채운다. 남은 불명확한 항목은 TODO로 표시.

### Step 4: Index.md 생성

sot/ 루트에 Index.md 생성. 각 카테고리 문서로의 링크와 한 줄 설명 포함.

## 주의사항

- 하나의 md 파일에 모든 내용을 담지 않는다 — 반드시 카테고리별 디렉토리에 분리된 파일로 저장
- 내용이 많아지면 카테고리 내부에서 추가로 파일을 쪼갠다 (예: architecture/frontend.md, architecture/backend.md)
- 내용 채우기는 이 스킬의 범위 밖 — "Overview 작성해줘" 같은 후속 요청으로 진행
- 기존 sot/ 파일이 있으면 덮어쓰지 않는다
