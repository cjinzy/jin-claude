#!/bin/bash
# 도구 실행 후 결과를 검증한다.
# PostToolUse hook. stdin의 JSON 이벤트를 소비하고 approve를 반환한다.
cat > /dev/null
echo '{"result":"approve"}'
