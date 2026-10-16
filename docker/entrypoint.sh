#!/usr/bin/env bash
set -euo pipefail

OLLAMA_PID=""

cleanup() {
    local exit_code=$?
    if [ -n "$OLLAMA_PID" ] && kill -0 "$OLLAMA_PID" 2>/dev/null; then
        echo "[sanadsquad-entrypoint] Shutting down embedded Ollama server (PID: $OLLAMA_PID)..."
        kill -TERM "$OLLAMA_PID" 2>/dev/null || true
        wait "$OLLAMA_PID" 2>/dev/null || true
    fi
    exit $exit_code
}

trap cleanup SIGINT SIGTERM EXIT

echo "================================================================================"
echo "SANADSQUAD EVIDENCE-FIRST V2 — SELF-CONTAINED OFFLINE RUNTIME"
echo "================================================================================"

# Set up runtime directories in writable area
export OLLAMA_HOST="127.0.0.1:11434"
export OLLAMA_MODELS="${OLLAMA_MODELS:-/app/models}"
export OLLAMA_KEEP_ALIVE="5m"

# Ensure output directory exists and is writable
OUTPUT_DIR="/app/output"
if [ ! -d "$OUTPUT_DIR" ]; then
    mkdir -p "$OUTPUT_DIR" 2>/dev/null || true
fi

# Start embedded Ollama inference server
echo "[sanadsquad-entrypoint] Starting embedded Ollama daemon..."
ollama serve > /tmp/ollama_serve.log 2>&1 &
OLLAMA_PID=$!

# Wait for Ollama readiness on localhost
echo "[sanadsquad-entrypoint] Polling Ollama daemon on http://127.0.0.1:11434/api/tags..."
MAX_WAIT_SECONDS=45
WAIT_COUNT=0
READY=0

while [ $WAIT_COUNT -lt $MAX_WAIT_SECONDS ]; do
    if curl -s -f http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
        READY=1
        break
    fi
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
done

if [ $READY -ne 1 ]; then
    echo "[sanadsquad-entrypoint] ERROR: Ollama daemon failed to report ready within ${MAX_WAIT_SECONDS} seconds." >&2
    if [ -f /tmp/ollama_serve.log ]; then
        cat /tmp/ollama_serve.log >&2
    fi
    exit 1
fi

# Verify required model exists in pre-baked layer
TARGET_MODEL="${OLLAMA_MODEL:-qwen3.5:4b}"
echo "[sanadsquad-entrypoint] Verifying pre-baked model presence: '$TARGET_MODEL'..."
TAGS_RESPONSE=$(curl -s http://127.0.0.1:11434/api/tags || echo "{}")

if ! echo "$TAGS_RESPONSE" | grep -q "\"name\":\"$TARGET_MODEL\""; then
    echo "[sanadsquad-entrypoint] ERROR: Required model '$TARGET_MODEL' not found in container storage." >&2
    echo "[sanadsquad-entrypoint] Installed models: $TAGS_RESPONSE" >&2
    exit 1
fi

echo "[sanadsquad-entrypoint] Verified model '$TARGET_MODEL' is pre-baked and ready for offline inference."

# Determine command to execute
if [ $# -eq 0 ]; then
    echo "[sanadsquad-entrypoint] No CLI arguments passed. Running default 6-slot Evidence-First V2 weekly execution..."
    set -- python /app/run_week.py --plan /app/plan.json --mode evidence_first_v2 --authorization-mode publication_eligible --output /app/output/v2-week
elif [[ "$1" == --* ]]; then
    echo "[sanadsquad-entrypoint] Forwarding flags to run_week.py..."
    set -- python /app/run_week.py "$@"
fi

echo "[sanadsquad-entrypoint] Executing command: $@"
echo "--------------------------------------------------------------------------------"

CMD_EXIT_CODE=0
"$@" || CMD_EXIT_CODE=$?

echo "--------------------------------------------------------------------------------"
echo "[sanadsquad-entrypoint] Process exited with status code: $CMD_EXIT_CODE"

exit $CMD_EXIT_CODE
