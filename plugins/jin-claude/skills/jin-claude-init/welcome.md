# jin-claude 환경 초기화 완료!

## 주요 스킬

| 스킬 | 사용법 | 설명 |
|------|--------|------|
| jin-commit | `jin commit` 또는 `/jin-claude:jin-commit` | gitmoji 커밋 메시지 자동 추천 |
| jin-interview | `jin interview` 또는 `/jin-claude:jin-interview` | 상세 인터뷰 후 스펙 생성 |
| guidelines | `/jin-claude:guidelines` | LLM 코딩 행동 가이드 (Karpathy 기반) |
| verify-implementation | `/jin-claude:verify-implementation` | 구현 검증 |
| manage-skills | `/jin-claude:manage-skills` | 스킬 관리 |
| jin-claude-init | `jin init` 또는 `/jin-claude:jin-claude-init` | 환경 재초기화 |

## Magic Keywords

프롬프트에 아래 키워드를 입력하면 자동으로 해당 스킬이 실행됩니다:

| Keyword | 스킬 |
|---------|------|
| `jin init` / `jin 초기화` | jin-claude-init |
| `jin commit` | jin-commit |
| `jin interview` | jin-interview |

자세한 내용은 README.md를 참고하세요.
