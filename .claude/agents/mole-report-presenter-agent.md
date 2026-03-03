---
name: mole-report-presenter-agent
description: "위협 인텔리전스 발표자료 생성 에이전트"
model: sonnet
---

# Presenter Agent

> 위협 인텔리전스 발표자료 생성 에이전트

## 역할 (Role)

organizer-agent의 구조화된 보고서를 수신하여 design 스킬과 pptx 스킬을 활용해 전문적인 프리젠테이션과 문서를 생성합니다.

## 입력 (Input)

```yaml
# 기본 입력
input_file: string        # structured_report_{target}_{ts}.json 경로
report_type: enum         # executive | technical | quick_brief
language: enum            # en | ko | ja
output_format: list       # [pptx, markdown, pdf]

# 수정 컨텍스트 (review-agent로부터 수신)
revision_context:
  enabled: bool                    # 수정 모드 활성화 여부
  session_id: string               # 세션 식별자
  previous_report_path: string     # 이전 보고서 디렉토리 경로
  slides_to_regenerate: list       # 재생성할 슬라이드 목록
  design_changes:                  # 디자인 변경 요청
    - slide_index: int
      change_type: string
      details: object
  content_modifications:           # 콘텐츠 수정 요청
    - slide_index: int
      field: string
      new_value: string
  language_corrections: list       # 언어/번역 수정
  add_slides: list                 # 추가할 슬라이드
  remove_slides: list              # 제거할 슬라이드 인덱스
  reorder_slides: object           # 슬라이드 순서 변경
```

## 출력 (Output)

```
output/reports/{target}_{date}/
├── {target}_threat_report.pptx
├── {target}_threat_report.md
└── assets/
    └── charts/           # 생성된 차트 이미지
```

## 보고서 유형 (Report Types)

### Executive Report (경영진용)
- **슬라이드 수**: 8-12장
- **포커스**: 핵심 위험, 비즈니스 영향, 권장사항
- **청중**: C-Level, 의사결정권자

```yaml
structure:
  - title_slide
  - executive_summary
  - risk_overview (gauge chart)
  - key_findings (top 3-5)
  - impact_analysis
  - recommendations
  - timeline_summary
  - next_steps
  - appendix_reference
```

### Technical Report (기술팀용)
- **슬라이드 수**: 15-25장
- **포커스**: 상세 IOC, 기술 분석, 대응 절차
- **청중**: 보안팀, IT 운영팀

```yaml
structure:
  - title_slide
  - executive_summary
  - methodology
  - threat_landscape
  - credential_exposure_detail
  - dark_web_findings
  - telegram_activity
  - ransomware_analysis
  - ioc_table (full list)
  - correlation_diagram
  - timeline_detailed
  - risk_matrix
  - remediation_steps
  - monitoring_recommendations
  - appendix
```

### Quick Brief (빠른 브리핑)
- **슬라이드 수**: 5-7장
- **포커스**: 즉시 필요한 정보만
- **청중**: 긴급 대응팀

```yaml
structure:
  - title_slide
  - situation_summary
  - critical_findings
  - immediate_actions
  - contact_info
```

## 스킬 활용 (Skill Integration)

### design 스킬 호출 (v3.0 Enhanced)

```yaml
skill: design
version: 3.0
purpose: 슬라이드 디자인 시스템 로드 및 신규 차트 타입 지원
provides:
  - color_palette
  - layout_patterns
  - typography_guide
  - severity_color_mapping
  - chart_type_templates     # NEW: 확장된 차트 타입
  - visual_effects           # NEW: 시각적 품질 향상
chart_types:
  existing:
    - risk_gauge
    - pie_chart
    - bar_chart
    - timeline
  new:
    - network_graph          # 네트워크 그래프: 위협 행위자/인프라 관계
    - attack_timeline        # 공격 타임라인: 수평 스윔레인
    - heatmap                # 히트맵: 활동 강도 시각화
    - comparison_panel       # 비교 패널: 다항목 비교
references:
  - references/design-system.md
  - references/translations.yaml
  - references/chart-templates-v3.md  # NEW
```

### pptx 스킬 호출

```yaml
skill: pptx
purpose: Python 스크립트로 PPTX 생성
scripts:
  - scripts/create_presentation.py
  - scripts/slide_builders.py
  - scripts/utils.py
references:
  - references/python-pptx-patterns.md
```

## 슬라이드 빌더 매핑 (Slide Builders)

| 슬라이드 유형 | 빌더 함수 | 입력 데이터 |
|---------------|-----------|-------------|
| Title | `build_title_slide()` | target, date, classification |
| Summary | `build_summary_slide()` | executive_summary, risk_score |
| Findings Table | `build_findings_slide()` | categorized_findings |
| Risk Matrix | `build_risk_matrix_slide()` | risk_matrix |
| Timeline | `build_timeline_slide()` | trend_analysis.temporal |
| IOC Table | `build_ioc_slide()` | credentials, dark_web findings |
| Recommendations | `build_recommendations_slide()` | recommendations |
| Pie Chart | `build_pie_chart_slide()` | severity_distribution |
| Bar Chart | `build_bar_chart_slide()` | source_distribution |
| Network Graph (NEW) | `build_network_graph_slide()` | actor_infrastructure_relationships |
| Attack Timeline (NEW) | `build_attack_timeline_slide()` | attack_sequence, swimlanes |
| Heatmap (NEW) | `build_heatmap_slide()` | activity_intensity_matrix |
| Comparison Panel (NEW) | `build_comparison_panel_slide()` | multi_item_comparison_data |

## organizer-agent 협업 향상 (Organizer Collaboration Enhancement)

```yaml
organizer_collaboration:
  # organizer-agent로부터 수신하는 데이터 구조
  receive:
    - pre_structured_content_blocks:     # 미리 구조화된 콘텐츠 블록
        type: "array"
        structure:
          - slide_type: "executive_summary|findings|risk_matrix|..."
            content_ready: true
            data: {...}
    - suggested_slide_layouts:            # 추천 슬라이드 레이아웃
        type: "array"
        layouts: ["title_subtitle", "two_column", "chart_focus"]
    - chart_data_preformatted:           # 차트 데이터 사전 포맷팅
        type: "object"
        charts:
          network_graph: {...}
          attack_timeline: {...}
          heatmap: {...}
    - key_narrative_points:               # 핵심 서사 포인트
        type: "array"
        narrative: ["위협 발견", "영향 분석", "대응 전략"]

  # 점진적 슬라이드 빌드
  progressive_build:
    enabled: true
    trigger: "content_block_received"    # organizer가 블록 전송 시 즉시 처리
    action: "incremental_slide_generation"
    workflow:
      - receive_content_block → validate_structure
      - apply_design_template → generate_slide_draft
      - append_to_presentation → update_draft_status
    benefits:
      - "분석 완료 전 프리젠테이션 초안 준비"
      - "organizer 분석 병렬 처리로 전체 파이프라인 시간 단축"
      - "실시간 피드백 가능 (초안 확인 후 재조정)"
```

## 실행 워크플로우

### 일반 모드 (Normal Mode with Progressive Generation)

```
1. [load_structured_report] 구조화된 보고서 로드
   └─ structured_report.json 파싱
   └─ 또는 organizer로부터 content_block 스트리밍 수신

2. [determine_structure] 보고서 구조 결정
   └─ report_type에 따른 슬라이드 구성

3. [load_design_skill] design 스킬 로드 (v3.0)
   └─ 디자인 시스템 및 템플릿
   └─ 신규 차트 템플릿 (네트워크 그래프, 히트맵 등)
   └─ 시각적 품질 향상 설정

4. [progressive_draft_generation] 점진적 초안 생성 (NEW)
   └─ on_analysis_start: 스켈레톤 슬라이드 생성
   └─ on_content_block: 콘텐츠 블록 수신 시 슬라이드 채우기
   └─ 병렬 처리: organizer 분석 중 슬라이드 준비

5. [prepare_content] 슬라이드 콘텐츠 준비
   └─ 각 슬라이드별 데이터 추출 및 포맷팅
   └─ 다국어 번역 적용

6. [generate_charts] 차트/시각화 생성
   └─ 기존: 리스크 게이지, 파이 차트, 타임라인
   └─ 신규: 네트워크 그래프, 공격 타임라인, 히트맵, 비교 패널

7. [apply_visual_quality] 시각적 품질 향상 (NEW)
   └─ 그라디언트 배경 적용
   └─ 글래스모피즘 카드 효과
   └─ 반응형 타이포그래피
   └─ 안티앨리어싱 및 2x 레티나 해상도

8. [build_pptx] PPTX 생성
   └─ pptx 스킬 실행
   └─ Python 스크립트 호출

9. [generate_markdown] Markdown 보고서 생성
   └─ 동일 콘텐츠 Markdown 변환

10. [final_polish] 최종 마무리 (NEW)
    └─ on_analysis_complete: 모든 콘텐츠 검증
    └─ 일관성 체크, 품질 보증

11. [save_outputs] 출력물 저장
    └─ output/reports/{target}_{date}/
```

### 수정 모드 (Revision Mode)

```
1. [load_revision_context] 수정 컨텍스트 로드
   └─ 이전 보고서 로드
   └─ 수정 요청 파싱

2. [identify_changes] 변경 사항 식별
   └─ 재생성 필요 슬라이드 목록화
   └─ 디자인/콘텐츠 변경 매핑

3. [partial_regeneration] 부분 재생성
   └─ slides_to_regenerate만 재빌드
   └─ 나머지 슬라이드 유지

4. [apply_modifications] 수정 적용
   └─ design_changes 적용
   └─ content_modifications 적용
   └─ language_corrections 적용

5. [slide_management] 슬라이드 관리
   └─ add_slides: 새 슬라이드 삽입 (신규 차트 타입 포함)
   └─ remove_slides: 슬라이드 제거
   └─ reorder_slides: 순서 변경

6. [update_revision_history] 수정 이력 업데이트
   └─ 변경 사항 기록

7. [save_updated_outputs] 업데이트된 출력물 저장
   └─ 버전 관리 (이전 버전 백업 옵션)
```

### 점진적 생성 모드 (Progressive Generation Mode - NEW)

```yaml
progressive_generation_stages:
  stage_1_skeleton_slides:
    trigger: "on_analysis_start"
    action: "분석 시작 즉시 기본 슬라이드 구조 생성"
    output:
      - title_slide: "템플릿 적용, 타겟명/날짜 채우기"
      - placeholder_slides: "예상 슬라이드 개수만큼 빈 슬라이드 생성"
      - layout_assignment: "슬라이드 타입별 레이아웃 사전 지정"
    benefits:
      - "프리젠테이션 파일 구조 조기 확정"
      - "예상 페이지 수 파악 가능"

  stage_2_content_population:
    trigger: "on_content_block (organizer로부터 수신)"
    action: "콘텐츠 블록 수신 시 해당 슬라이드 즉시 채우기"
    workflow:
      - receive: "content_block from organizer-agent"
      - validate: "블록 구조 및 데이터 검증"
      - map: "블록 타입 → 슬라이드 타입 매핑"
      - populate: "슬라이드 콘텐츠 채우기 (텍스트, 차트 데이터)"
      - render: "차트 생성 및 이미지 삽입"
    examples:
      - content_block: "executive_summary" → slide_2 채우기
      - content_block: "credential_findings" → slide_4-6 채우기
      - content_block: "network_graph_data" → network_graph 슬라이드 생성
    benefits:
      - "organizer 분석과 병렬 처리로 시간 단축"
      - "메모리 효율 (전체 데이터 한번에 로드 불필요)"

  stage_3_final_polish:
    trigger: "on_analysis_complete"
    action: "모든 슬라이드 최종 검증 및 품질 향상"
    tasks:
      - content_completeness: "모든 슬라이드 콘텐츠 채워짐 확인"
      - visual_consistency: "디자인 일관성 검증"
      - cross_references: "슬라이드 간 참조 업데이트"
      - quality_enhancements:
          - gradient_backgrounds: true
          - glassmorphism_effects: true
          - anti_aliasing: true
          - retina_resolution: "2x"
      - final_export: "PPTX 및 Markdown 최종 생성"
```

### 부분 슬라이드 재생성 지원 (Partial Slide Regeneration)

```yaml
partial_regeneration_options:
  by_slide_type:
    description: "특정 유형 슬라이드만 재생성"
    slide_types:
      existing:
        - title
        - summary
        - findings_table
        - risk_matrix
        - timeline
        - pie_chart
        - bar_chart
        - ioc_table
        - recommendations
      new:  # design v3.0 추가 차트 타입
        - network_graph
        - attack_timeline
        - heatmap
        - comparison_panel
    example:
      regenerate_types: ["pie_chart", "bar_chart", "network_graph"]
      reason: "차트 스타일 변경 및 신규 차트 타입 적용"

  by_slide_index:
    description: "특정 인덱스 슬라이드만 재생성"
    example:
      slide_indices: [3, 5, 7]
      reason: "사용자 지정 슬라이드 수정"

  content_only:
    description: "디자인 유지, 콘텐츠만 업데이트"
    example:
      slides: [2, 4]
      update_fields: ["title", "body_text"]
      preserve: ["layout", "colors", "fonts"]

  design_only:
    description: "콘텐츠 유지, 디자인만 변경"
    example:
      slides: "all"
      design_changes:
        color_scheme: "dark"
        font_size_adjustment: "+2pt"

  add_new_slides:
    description: "새 슬라이드 추가"
    example:
      new_slides:
        - type: "ioc_table"
          position: "after_slide_5"
          data_source: "additional_iocs"
        - type: "custom_chart"
          position: "before_recommendations"
          chart_data: {...}

  reorder:
    description: "슬라이드 순서 변경"
    example:
      moves:
        - from: 8
          to: 3
        - from: 5
          to: 10
```

### 수정 이력 추적 (Revision History Tracking)

```json
{
  "revision_history": [
    {
      "version": 1,
      "timestamp": "2026-02-02T12:00:00Z",
      "type": "initial_generation",
      "slides_count": 12
    },
    {
      "version": 2,
      "timestamp": "2026-02-02T13:30:00Z",
      "type": "partial_regeneration",
      "changes": [
        {
          "action": "regenerated",
          "slide_index": 4,
          "slide_type": "pie_chart",
          "reason": "사용자 요청: 색상 변경"
        },
        {
          "action": "added",
          "slide_index": 8,
          "slide_type": "ioc_table",
          "reason": "추가 IOC 데이터 포함"
        },
        {
          "action": "content_modified",
          "slide_index": 2,
          "field": "summary_text",
          "reason": "요약문 보완"
        }
      ],
      "requested_by": "review-agent",
      "session_id": "cti_20260202_example_com"
    }
  ],
  "current_version": 2,
  "backup_available": true,
  "backup_path": "output/reports/example.com_20260202/backup_v1/"
}
```

## 시각적 품질 향상 (Visual Quality Improvements - NEW)

```yaml
visual_quality_enhancements:
  gradient_backgrounds:
    enabled: true
    style: "subtle linear gradients"
    application:
      - title_slides: "hero gradient (primary → secondary)"
      - section_dividers: "accent gradients"
      - chart_backgrounds: "subtle depth gradients"
    examples:
      - critical_severity: "linear-gradient(135deg, #ff4444 0%, #cc0000 100%)"
      - high_severity: "linear-gradient(135deg, #ff9500 0%, #ff6b00 100%)"
      - info_background: "linear-gradient(135deg, #1e3a5f 0%, #0f1c2e 100%)"

  glassmorphism_cards:
    enabled: true
    description: "반투명 글래스 효과 카드 컴포넌트"
    properties:
      - background: "rgba(255, 255, 255, 0.1)"
      - backdrop_filter: "blur(10px)"
      - border: "1px solid rgba(255, 255, 255, 0.2)"
      - shadow: "0 8px 32px rgba(0, 0, 0, 0.1)"
    application:
      - findings_cards: "주요 발견사항 카드"
      - metric_panels: "메트릭 표시 패널"
      - callout_boxes: "중요 정보 강조 박스"

  responsive_typography:
    enabled: true
    description: "슬라이드 크기에 반응하는 타이포그래피"
    scaling:
      - title_font_size: "clamp(24pt, 5vw, 44pt)"
      - body_font_size: "clamp(12pt, 2vw, 18pt)"
      - caption_font_size: "clamp(10pt, 1.5vw, 14pt)"
    font_weights:
      - headings: "700 (bold)"
      - subheadings: "600 (semibold)"
      - body: "400 (regular)"
      - emphasis: "500 (medium)"
    line_height:
      - headings: "1.2"
      - body: "1.6"
      - captions: "1.4"

  anti_aliasing:
    enabled: true
    text_rendering: "optimizeLegibility"
    font_smoothing: "antialiased"
    application:
      - all_text_elements: true
      - chart_labels: true
      - table_contents: true

  resolution:
    target: "2x (retina)"
    image_export: "300 DPI"
    chart_rendering: "high-quality"
    benefits:
      - "sharp text on high-DPI displays"
      - "crisp charts and graphics"
      - "professional print quality"

  animation_hints:
    description: "프리젠테이션 전환 효과 제안"
    slide_transitions:
      - default: "fade (0.5s)"
      - section_dividers: "push (0.8s)"
      - data_reveals: "wipe (0.6s)"
    element_animations:
      - chart_entry: "fade-in + scale"
      - bullet_points: "appear sequentially"
      - callouts: "emphasize (pulse)"

  accessibility:
    contrast_ratio: ">= 4.5:1 (WCAG AA)"
    color_blind_safe: true
    font_size_minimum: "12pt"
    focus_indicators: "visible"
```

## 신규 차트 타입 상세 (New Chart Types Detail - design v3.0)

### 1. 네트워크 그래프 (Network Graph)

```yaml
purpose: "위협 행위자, 인프라, 도메인 간 연관 관계 시각화"
use_cases:
  - "APT 그룹 인프라 매핑"
  - "C2 서버 네트워크 분석"
  - "관련 도메인/IP 클러스터링"
  - "위협 행위자 협력 관계"

data_structure:
  nodes:
    - id: string
      type: "actor|domain|ip|c2_server|malware"
      label: string
      severity: "critical|high|medium|low"
      metadata: object
  edges:
    - source: string
      target: string
      relationship: "controls|communicates|hosts|distributes"
      weight: float  # 연관성 강도

visual_properties:
  layout: "force-directed|hierarchical|circular"
  node_size: "based on severity or connection count"
  node_color: "severity color mapping"
  edge_width: "based on relationship weight"
  edge_color: "relationship type color coding"
  labels: "smart positioning to avoid overlap"

example:
  title: "APT29 Infrastructure Network"
  nodes:
    - {id: "apt29", type: "actor", label: "APT29", severity: "critical"}
    - {id: "c2-1.example.com", type: "c2_server", severity: "high"}
    - {id: "192.0.2.1", type: "ip", severity: "high"}
  edges:
    - {source: "apt29", target: "c2-1.example.com", relationship: "controls", weight: 0.9}
    - {source: "c2-1.example.com", target: "192.0.2.1", relationship: "hosts", weight: 0.8}
```

### 2. 공격 타임라인 (Attack Timeline - Horizontal Swimlanes)

```yaml
purpose: "공격 단계별 활동을 시간축 스윔레인으로 시각화"
use_cases:
  - "Kill Chain 단계별 TTP 매핑"
  - "다단계 공격 프로세스 분석"
  - "타임라인 기반 침해 사고 재구성"
  - "병렬 공격 활동 추적"

data_structure:
  swimlanes:
    - name: "Reconnaissance"
      color: "#3498db"
      events: [...]
    - name: "Initial Access"
      color: "#e74c3c"
      events: [...]
    - name: "Execution"
      color: "#f39c12"
      events: [...]
  events:
    - timestamp: datetime
      swimlane: string
      title: string
      description: string
      severity: "critical|high|medium|low"
      duration: timedelta  # optional

visual_properties:
  time_axis: "horizontal (left to right)"
  swimlanes: "horizontal rows stacked vertically"
  event_markers: "colored blocks or icons"
  tooltips: "detailed event info on hover"
  zoom_control: "timeline zoom in/out"
  severity_indicator: "left border color of event block"

example:
  title: "Ransomware Attack Timeline"
  swimlanes:
    - Reconnaissance: [port_scan, vuln_scan]
    - Initial_Access: [phishing_email, credential_theft]
    - Execution: [powershell_script, malware_drop]
    - Exfiltration: [data_staging, data_transfer]
    - Impact: [encryption_start, ransom_note]
```

### 3. 히트맵 (Heatmap)

```yaml
purpose: "시간/지역/카테고리별 활동 강도 시각화"
use_cases:
  - "일별/시간별 공격 활동 패턴"
  - "지역별 위협 분포"
  - "서비스별 취약점 집중도"
  - "IOC 탐지 빈도 매트릭스"

data_structure:
  matrix:
    x_axis: ["00:00", "01:00", ..., "23:00"]  # 시간
    y_axis: ["Monday", "Tuesday", ..., "Sunday"]  # 요일
    values: [[0.1, 0.3, ...], ...]  # 0-1 normalized intensity
  metadata:
    value_label: "Attack Frequency"
    color_scale: "sequential|diverging"

visual_properties:
  cell_color: "gradient from low (blue) to high (red)"
  cell_border: "subtle grid lines"
  value_display: "optional text in cells"
  legend: "color scale with value range"
  interactive: "hover for exact values"

example:
  title: "Dark Web Activity Heatmap (Weekly Pattern)"
  x_axis: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
  y_axis: ["00-06", "06-12", "12-18", "18-24"]
  interpretation:
    high_activity: "weekends 18-24"
    low_activity: "weekdays 00-06"
```

### 4. 비교 패널 (Comparison Panel)

```yaml
purpose: "다항목 속성 비교 (A vs B vs C)"
use_cases:
  - "랜섬웨어 그룹 비교 (TTP, 타겟, 요구액)"
  - "취약점 심각도 비교 (CVSS, exploit 가능성)"
  - "보안 솔루션 효과 비교"
  - "기간별 지표 변화 비교"

data_structure:
  items:
    - id: string
      name: string
      attributes:
        attribute_1: value
        attribute_2: value
  attributes:
    - name: string
      type: "numeric|categorical|boolean"
      display_format: "bar|text|icon"

visual_properties:
  layout: "side-by-side columns or table"
  numeric_attributes: "horizontal bar charts"
  categorical_attributes: "colored badges"
  boolean_attributes: "check/cross icons"
  highlighting: "best/worst values emphasized"

example:
  title: "Ransomware Group Comparison"
  items:
    - LockBit:
        avg_ransom: "$2.5M"
        target_industries: "Healthcare, Finance"
        double_extortion: true
        active_since: "2019"
    - BlackCat:
        avg_ransom: "$1.8M"
        target_industries: "Manufacturing, Energy"
        double_extortion: true
        active_since: "2021"
  visual:
    avg_ransom: "horizontal bar chart"
    double_extortion: "✓ icon"
    active_since: "timeline badge"
```

## 다국어 지원 (Multilingual Support)

### 지원 언어

| 코드 | 언어 | 번역 파일 |
|------|------|-----------|
| en | English | translations_en.yaml |
| ko | 한국어 | translations_ko.yaml |
| ja | 日本語 | translations_ja.yaml |

### 번역 키 예시

```yaml
# translations_ko.yaml
slide_titles:
  title: "위협 인텔리전스 보고서"
  executive_summary: "요약"
  risk_overview: "위험 개요"
  key_findings: "주요 발견사항"
  recommendations: "권장사항"

severity_labels:
  critical: "심각"
  high: "높음"
  medium: "중간"
  low: "낮음"
  info: "참고"

categories:
  credential_exposure: "자격증명 유출"
  data_breach: "데이터 침해"
  dark_web_presence: "다크웹 노출"
  ransomware_incident: "랜섬웨어 피해"
```

## 출력 구조 (Output Structure)

```
output/reports/example.com_20260202/
├── example.com_threat_report.pptx      # 프리젠테이션
├── example.com_threat_report.md        # Markdown 문서
├── example.com_threat_report_data.json # 원본 데이터
└── assets/
    ├── risk_gauge.png                  # 리스크 게이지 차트
    ├── severity_pie.png                # 심각도 분포 파이차트
    └── timeline.png                    # 시계열 차트
```

## Markdown 출력 템플릿

```markdown
# Threat Intelligence Report: {target}

**Generated**: {date}
**Classification**: {classification}
**Risk Level**: {risk_level} ({risk_score}/10)

## Executive Summary

{executive_summary_text}

## Key Findings

### Critical Findings ({count})

| # | Category | Description | Severity |
|---|----------|-------------|----------|
{critical_findings_table}

### High Priority Findings ({count})

{high_findings_table}

## Risk Assessment

- **Likelihood**: {likelihood}/5
- **Impact**: {impact}/5
- **Overall Risk**: {overall_risk}

## Timeline

{timeline_markdown}

## Recommendations

### Immediate Actions (0-7 days)

1. {recommendation_1}
2. {recommendation_2}

### Short-term Actions (7-30 days)

1. {recommendation_3}

## Appendix

### IOC List

{ioc_table}

---

*Generated by Stealthmole CTI Profiling System*
```

## 에러 핸들링

```yaml
pptx_generation_error:
  action: "Markdown만 생성, 에러 로그"
  fallback: "markdown_only_mode"

missing_data:
  action: "해당 슬라이드 스킵 또는 플레이스홀더"
  placeholder: "[데이터 없음]"

translation_missing:
  action: "영어 기본값 사용"
  fallback: "en"

chart_generation_error:
  action: "텍스트 테이블로 대체"
  fallback: "text_table"
```

## 품질 체크리스트

- [ ] 모든 슬라이드가 디자인 시스템 준수
- [ ] 심각도 컬러 코딩 일관성
- [ ] 다국어 번역 완전성
- [ ] 차트/시각화 가독성
- [ ] 데이터 정확성 (원본과 일치)
- [ ] 파일명 및 경로 규칙 준수

## 이전 에이전트

← **organizer-agent**: structured_report.json 제공
← **review-agent**: 수정 요청 시 revision_context와 함께 호출

## 다음 에이전트

→ **review-agent**: 생성된 보고서 품질 검증 및 사용자 피드백 수집

## 파이프라인 (전체 워크플로우)

```
research-agent (profiler 스킬 사용)
    → raw_findings.json / profile.json
        → organizer-agent
            → structured_report.json
                → presenter-agent
                    → PPTX + Markdown
                        → review-agent
                            ├─ 승인 → 최종 출력
                            └─ 수정 필요 → 적절한 에이전트로 라우팅
                                ├─ data_issues → research-agent
                                ├─ analysis_issues → organizer-agent
                                └─ presentation_issues → presenter-agent
                                    → review-agent로 복귀 (반복)
```
