# jin-claude-init 현황 조사 및 업데이트 계획

## 현황 조사 결과

### 파일 구조
```
jin-claude-init/
├── SKILL.md                         # 스킬 문서 (5-step 워크플로우)
└── scripts/
    ├── sync_repo.py                 # Step 3: git sync + venv + superclaude
    ├── merge_settings.py            # Step 4: settings deep merge
    ├── test_sync_repo.py            # 10개 테스트 (install_superclaude만)
    └── test_merge_settings.py       # 11개 테스트 (deep_merge + merge_settings)
```

### SKILL.md ↔ 코드 일치 여부

| 항목 | SKILL.md | 코드 | 일치 |
|------|----------|------|------|
| Step 1 Marketplace 목록 (5개) | obsidian, ui-ux-pro-max, superpowers, omc, context-mode | N/A (수동 실행) | — |
| Step 2 Plugin 설치 목록 (5개) | 동일 5개 | N/A (수동 실행) | — |
| SuperClaude fallback 순서 | pipx → pip → uv | 코드 일치 | ✅ |
| Step 3 sync 대상 dirs | agents/, skills/ | `SYNC_TARGETS` 일치 | ✅ |
| Step 3 sync 대상 files | statusline-command.sh, CLAUDE.md | `SYNC_FILES` 일치 | ✅ |
| Step 3 venv 설명 | uv 우선, pip fallback | `ensure_venv()` 일치 | ✅ |
| Step 4 설정 7개 항목 | 전부 나열 | `REQUIRED_SETTINGS` 일치 | ✅ |
| Step 5 검증 절차 | plugin list, settings, agents 확인 | N/A (수동 실행) | — |

### 발견된 불일치 및 개선점

#### 1. SKILL.md Step 3에 SuperClaude 설치 단계 누락 (Medium)
- `sync_repo.py`의 `main()`이 `install_superclaude()`를 호출하지만, Step 3의 "이 스크립트는:" 목록에 SuperClaude 설치가 빠져 있음
- SuperClaude 설명은 Step 2 아래 인용문에만 존재 → Step 3 설명과 분리됨

#### 2. Plugin 목록에 claudeclaw 미포함 (Low — 확인 필요)
- 현재 세션에 `claudeclaw:*` 스킬이 활성화되어 있으나, SKILL.md Step 1/2에 해당 marketplace/plugin이 없음
- 사용자가 별도로 설치한 것인지, SKILL.md에 추가해야 하는지 **확인 필요**

#### 3. 테스트 커버리지 편중 (Low)
- `test_sync_repo.py`는 `install_superclaude()`만 테스트 (10개)
- `clone_or_pull()`, `sync_directory()`, `sync_file()`, `ensure_venv()`, `find_uv()` 등 다른 함수들의 테스트 없음
- `test_merge_settings.py`는 `deep_merge()` + `merge_settings()` 포괄적 테스트 (11개) ✅

#### 4. `.omc/` 및 `__pycache__/` 잔재 파일 (Trivial)
- `.gitignore`에 의해 트래킹되지는 않지만, `scripts/` 안에 `.omc/state/`와 `__pycache__/`가 로컬에 존재
- 정리 권장 (필수 아님)

---

## 업데이트 계획

### Task 1: SKILL.md Step 3 설명 보완
**우선순위: Medium | 난이도: 낮음**

Step 3의 "이 스크립트는:" 목록 끝에 SuperClaude 설치 단계 추가:
```markdown
- SuperClaude Framework 설치 (`pipx` → `pip --user` → `uv tool install` fallback)
  - 설치 성공 시 `superclaude install`로 초기화
```

### Task 2: claudeclaw 포함 여부 결정
**우선순위: Low | 난이도: 낮음**

사용자 확인 필요:
- claudeclaw를 표준 환경에 포함할 것인가?
- 포함한다면 Step 1/2에 marketplace/plugin 명령 추가

### Task 3: sync_repo.py 나머지 함수 테스트 추가
**우선순위: Low | 난이도: 중간**

대상 함수 및 시나리오:
- `find_uv()`: which 성공/실패/타임아웃
- `sync_directory()`: 소스 존재/미존재, 파일 복사 검증
- `sync_file()`: 소스 존재/미존재
- `clone_or_pull()`: clone/pull 성공, pull 실패 시 re-clone
- `ensure_venv()`: pyproject.toml 존재/미존재, uv→pip fallback

### Task 4: 로컬 잔재 파일 정리
**우선순위: Trivial**

```bash
rm -rf .claude/skills/jin-claude-init/scripts/.omc/
rm -rf .claude/skills/jin-claude-init/scripts/__pycache__/
```
