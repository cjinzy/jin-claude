# jin-claude 환경 초기화 완료!

## 주요 스킬

| 스킬 | 사용법 | 설명 |
|------|--------|------|
| jin-commit | `jin commit` 또는 `/jin-claude:jin-commit` | gitmoji 커밋 메시지 자동 추천 |
| jin-interview | `jin interview` 또는 `/jin-claude:jin-interview` | 상세 인터뷰 후 스펙 생성 |
| jin-swe-fix | `jin swe` 또는 `/jin-claude:jin-swe-fix` | SWE-agent 워크플로우 이슈 수정 |
| py-standard | `/jin-claude:py-standard` | Python 프로젝트 표준 컨벤션 가이드 |
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
| `jin swe` | jin-swe-fix |

## 에이전트 카탈로그

### Opus 모델
| 에이전트 | 용도 |
|----------|------|
| mole-review-agent | CTI 프로파일링 파이프라인 오케스트레이터 |
| swe-agent-high | 복잡한 교차 모듈 이슈 해결 |

### Sonnet 모델
| 에이전트 | 용도 |
|----------|------|
| jin-interview-agent | 구조화된 요구사항 인터뷰 및 스펙 생성 |
| python-expert | 프로덕션급 Python 개발 |
| swe-agent | 6단계 워크플로우 이슈 해결 |
| swe-analyst | 읽기 전용 근본원인 진단 |
| swe-verifier | 수정 후 독립 검증 |
| mole-research-agent | 위협 데이터 수집 |
| mole-report-presenter-agent | 보고서 생성 |
| mole-intel-organizer-agent | 위협 데이터 분류 |
| mole-graph-generator-agent | 관계 그래프 생성 |
| mole-interview-agent | CTI 조사 전 인터뷰 |
| mole-user-identifier-agent | 사용자 신원 분석 |

자세한 내용은 README.md를 참고하세요.
