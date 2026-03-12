#!/bin/bash
# 도구 사용 전 규칙을 강제한다.
# PreToolUse hook. stdin의 JSON 이벤트를 소비하고 approve를 반환한다.
# Plan mode에서 편집 도구 차단은 Claude Code가 자체 처리하므로 여기서는 통과만 한다.
cat > /dev/null
echo '{"result":"approve"}'
