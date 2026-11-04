# jin-sot-create — design 카테고리 + DESIGN.md 연동

## 문제
SoT 카테고리 6개에 디자인 규칙 소유자가 없고, 루트 `DESIGN.md`(디자인 토큰)를 참조하지 않음.

## 결정
- 7번째 카테고리 `design/`, 접두사 `DSN`. 기존 소유자가 없는 사실이라 소유권 분할 없음.
  - 대안 `rules/design.md`는 코딩 규칙과 디자인 규칙을 한 카테고리에 섞어 기각.
- 토큰(색·타이포·간격)의 소유자는 루트 `DESIGN.md`(tracked, design.md 포맷). 디자인 도구가 루트에서 읽음.
  `design/` 문서는 `Evidence: DESIGN.md:<line>`로 인용만 하고 복사하지 않음(불변식 1).
- `design/` 문서의 `verified_paths`에 `DESIGN.md`를 넣어 토큰이 바뀌면 `DRIFT`가 나게 함.
- `sot_index.py`는 `DESIGN.md`가 있을 때만 Index.md에 링크(dead link 방지).
- 스킬은 `DESIGN.md`를 생성하지 않음. 없으면 `TODO(sot)` → `/design-consultation`.

## 변경
- `scripts/sot_validate.py`: `CATEGORY_PREFIXES["design"]="DSN"`, `DESIGN_FILENAME`
- `scripts/sot_index.py`: `render(rows, root)` — DESIGN.md 포인터
- `scripts/test_sot_*.py`: design 카테고리 / 포인터 테스트
- `SKILL.md`: 카테고리 표, DESIGN.md 절, 레이아웃, Step 1/2/3, 가드레일
- `.claude/CLAUDE.md` (+ `~/.claude/CLAUDE.md`): 카테고리 목록에 Design 추가

## 미포함
- 배포(버전 bump, 플러그인 재설치) — 별도 요청 시.
