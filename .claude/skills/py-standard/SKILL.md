---
name: py-standard
description: "Python 프로젝트 표준 컨벤션 가이드. uv 패키지 매니저, Ruff 린터, loguru 로깅, 타입 힌트 기반 개발 환경 설정 및 코드 스타일 가이드. 사용 시점: (1) 새 Python 프로젝트 초기화 시, (2) 기존 코드에 컨벤션 적용/리팩토링, (3) 코드 리뷰 시 컨벤션 검토, (4) Python 프로젝트, 코드 스타일, 컨벤션, 린터 설정 관련 요청 시"
---

# Python Standard Convention

Python 프로젝트의 표준 개발 환경 및 코딩 컨벤션 가이드.

## Quick Start

| 항목 | 표준 |
|------|------|
| 패키지 매니저 | uv |
| Python 버전 | 3.12+ |
| 린터/포맷터 | Ruff |
| 로깅 | loguru |
| 예외 처리 | traceback 필수 |
| Docstring | 한글 |

## 개발 환경

### 패키지 매니저: uv

```bash
# 프로젝트 초기화
uv init
uv add <package>
uv sync
```

### Python 버전

- 최소: Python 3.12
- pyproject.toml에 명시: `requires-python = ">=3.12"`

## 코드 스타일

### Ruff 설정

pyproject.toml:

```toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "W"]

[tool.ruff.lint.isort]
known-first-party = ["src"]
```

### Import 정렬 (PEP8)

```python
# 1. 표준 라이브러리
import os
from pathlib import Path

# 2. 서드파티
import httpx
from pydantic import BaseModel

# 3. 로컬
from src.utils import helper
```

## 타입 힌트

### 기본 규칙

```python
from __future__ import annotations

def process_data(items: list[str], limit: int = 10) -> dict[str, int]:
    """데이터 처리 함수."""
    ...
```

### 복잡한 타입

```python
from typing import TypeAlias

UserData: TypeAlias = dict[str, str | int | None]
```

## 네이밍 컨벤션

| 대상 | 스타일 | 예시 |
|------|--------|------|
| 변수/함수 | snake_case | `user_name`, `get_data()` |
| 클래스 | PascalCase | `UserService`, `DataProcessor` |
| 상수 | UPPER_SNAKE_CASE | `MAX_RETRIES`, `API_URL` |
| 프라이빗 | _prefix | `_internal_method()` |

## 로깅: loguru

### 기본 사용

```python
from loguru import logger

logger.info("처리 시작")
logger.debug(f"데이터: {data}")
logger.error(f"오류 발생: {e}")
```

### 설정 패턴

```python
from loguru import logger
import sys

logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/app.log", rotation="10 MB")
```

## 예외 처리

### 규칙

- **except 블록에서 반드시 traceback 포함**
- `logger.exception()` 사용 권장 (자동 traceback 포함)

### 예시

```python
from loguru import logger

# 권장: logger.exception() 사용
try:
    result = risky_operation()
except Exception as e:
    logger.exception(f"작업 실패: {e}")
    raise

# 대안: traceback 모듈 사용
import traceback

try:
    result = risky_operation()
except Exception as e:
    logger.error(f"작업 실패: {e}\n{traceback.format_exc()}")
    raise
```

### 잘못된 예시

```python
# 금지: traceback 없이 로깅
try:
    result = risky_operation()
except Exception as e:
    logger.error(f"오류: {e}")  # traceback 누락!
```

## Docstring

### 규칙

- **항상 한글로 작성**

### 예시

```python
def calculate_total(items: list[float], tax_rate: float = 0.1) -> float:
    """주어진 가격 목록의 총액을 계산하고 세금을 적용한다.

    각 항목의 가격을 합산한 후, 지정된 세율을 적용하여
    최종 금액을 반환한다. 세율이 지정되지 않으면 기본값 10%가 적용된다.

    Args:
        items (list[float]): 계산할 개별 항목들의 가격 목록.
            빈 리스트인 경우 0.0을 반환한다.
        tax_rate (float): 적용할 세율. 0.1은 10%를 의미한다.
            기본값은 0.1 (10%)이다.

    Returns:
        float: 세금이 포함된 최종 총액.

    Raises:
        ValueError: 세율이 음수인 경우 발생한다.
    """
    ...
```

## 코드 리뷰 체크리스트

프로젝트 초기화 시:
- [ ] uv로 프로젝트 생성됨
- [ ] Python 3.12+ 설정됨
- [ ] Ruff 설정 추가됨

코드 리뷰 시:
- [ ] Import 정렬 (표준 → 서드파티 → 로컬)
- [ ] 타입 힌트 적용
- [ ] 네이밍 컨벤션 준수
- [ ] loguru 사용 (print 대신)
- [ ] except 블록에 traceback 포함
- [ ] Docstring 한글 작성
