#!/usr/bin/env bash
# healthcheck.sh - Verify all ORTA and upstream service health endpoints.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORTA_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

fail=0
check() {
  local name="$1" url="$2"
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" || echo "000")
  if [[ "$code" == "200" ]]; then
    echo "OK: $name -> $url ($code)"
  else
    echo "FAIL: $name -> $url ($code)"
    fail=1
  fi
}

echo "== ORTA service health =="
check "ORTA Core"   "http://127.0.0.1:8000/healthz"
check "ORTA Bridge" "http://127.0.0.1:8001/healthz"
check "ORTA UI"     "http://127.0.0.1:3000/"
echo ""
echo "== Upstream service health =="
check "SearXNG"     "http://127.0.0.1:18080/healthz"   || true  # published only if exposed
check "RAGFlow"     "http://127.0.0.1:9380/api/v1/system/healthz"

if [[ "$fail" -ne 0 ]]; then
  echo "== some health checks failed =="
  exit 1
fi
echo "== all health checks passed =="
