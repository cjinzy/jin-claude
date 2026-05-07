"""MCP 서버 설치 스크립트.

플러그인이 자동 제공하지 않는 standalone MCP 서버를 설치한다.
이미 설치된 서버는 건너뛴다 (멱등성 보장).

현재는 추가로 설치할 standalone MCP가 없다.
context-mode는 Step 2의 context-mode 플러그인이 자동 제공한다.
"""

import subprocess
import sys
import traceback
from pathlib import Path

MCP_SERVERS: list[dict] = []


def get_installed_mcps() -> set[str]:
    """현재 설치된 MCP 서버 목록을 반환한다.

    Returns:
        설치된 MCP 서버 이름의 집합.
    """
    try:
        result = subprocess.run(
            ["claude", "mcp", "list"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            print(f"[mcp] claude mcp list 실패: {result.stderr}")
            return set()
        # 출력에서 서버 이름 추출 (각 줄의 첫 번째 단어)
        names = set()
        for line in result.stdout.strip().splitlines():
            parts = line.strip().split()
            if parts:
                # "name: context7" 또는 "context7 ..." 형태 모두 처리
                raw = parts[0].rstrip(":")
                if raw in ("name", "Name"):
                    if len(parts) > 1:
                        names.add(parts[1])
                elif raw.startswith("plugin:"):
                    # "plugin:marketplace:name" → name도 등록 (중복 감지용)
                    plugin_name = raw.split(":")[-1]
                    names.add(raw)
                    names.add(plugin_name)
                else:
                    names.add(raw)
        return names
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError) as e:
        print(f"[mcp] claude mcp list 오류: {e}")
        return set()


def setup_mcp_servers() -> int:
    """MCP 서버를 설치한다. 이미 설치된 서버는 건너뛴다.

    Returns:
        새로 설치된 서버 수.
    """
    installed = get_installed_mcps()
    count = 0
    for server in MCP_SERVERS:
        if server["name"] in installed:
            print(f"[mcp] {server['name']} 이미 설치됨, 스킵")
            continue
        try:
            result = subprocess.run(
                ["claude", "mcp", "add", server["name"], "-s", "user", "--"]
                + server["args"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                print(f"[mcp] {server['name']} 설치 완료")
                count += 1
            else:
                print(f"[mcp] {server['name']} 설치 실패: {result.stderr}")
        except subprocess.TimeoutExpired:
            print(f"[mcp] {server['name']} 설치 타임아웃")
        except OSError as e:
            print(f"[mcp] {server['name']} 설치 오류: {e}")
    return count


def main() -> None:
    """메인 진입점."""
    try:
        count = setup_mcp_servers()
        print(f"[mcp] 총 {count}개 MCP 서버 설치 완료")
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
