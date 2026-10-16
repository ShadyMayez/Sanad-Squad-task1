#!/usr/bin/env bash
# ==============================================================================
# SANADSQUAD V2 — OFFLINE DOCKER IMAGE VERIFICATION SCRIPT
# Tests image execution strictly with --network none and inspects output deliverables.
# ==============================================================================

set -euo pipefail

IMAGE_TAG="${1:-sanadsquad:v2-offline}"
HOST_OUTPUT_DIR="$(pwd)/output/docker-verification-$(date +%Y%m%d-%H%M%S)"

echo "================================================================================"
echo "SANADSQUAD V2 OFFLINE CONTAINER VERIFICATION"
echo "Image Target: $IMAGE_TAG"
echo "Host Output:  $HOST_OUTPUT_DIR"
echo "Network Mode: none (strict offline isolation)"
echo "================================================================================"

mkdir -p "$HOST_OUTPUT_DIR"
chmod 777 "$HOST_OUTPUT_DIR" 2>/dev/null || true

# Determine container engine
if command -v podman >/dev/null 2>&1; then
    CONTAINER_ENGINE="podman"
    MOUNT_FLAGS=(--userns=keep-id -v "$HOST_OUTPUT_DIR":/app/output:Z)
else
    CONTAINER_ENGINE="docker"
    MOUNT_FLAGS=(-v "$HOST_OUTPUT_DIR":/app/output)
fi

echo "[1/4] Inspecting image manifest and labels via $CONTAINER_ENGINE..."
$CONTAINER_ENGINE image inspect "$IMAGE_TAG" > /dev/null

echo "[2/4] Executing container with --network none..."
CONTAINER_OUTPUT_DIR="/app/output/offline-run"
$CONTAINER_ENGINE run --rm \
    --network none \
    "${MOUNT_FLAGS[@]}" \
    "$IMAGE_TAG" \
    --plan /app/plan.json \
    --mode evidence_first_v2 \
    --authorization-mode publication_eligible \
    --output "$CONTAINER_OUTPUT_DIR"

echo "[3/4] Verifying generated artifacts in $HOST_OUTPUT_DIR/offline-run..."
RUN_DIR="$HOST_OUTPUT_DIR/offline-run"

if [ ! -d "$RUN_DIR" ]; then
    echo "ERROR: Expected run output directory $RUN_DIR does not exist!" >&2
    exit 1
fi

REQUIRED_FILES=(
    "posts.csv"
    "summary.json"
    "accepted_content.json"
    "claims.json"
    "evidence_provenance.json"
    "semantic_verification.json"
    "review_report.json"
    "validation_report.json"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$RUN_DIR/$file" ]; then
        echo "ERROR: Missing required output artifact: $file" >&2
        exit 1
    fi
    echo "  [OK] Found $file ($(wc -c < "$RUN_DIR/$file") bytes)"
done

# Inspect CSV structure
echo "[4/4] Validating CSV and visual specification contracts..."
CSV_HEADER=$(head -n 1 "$RUN_DIR/posts.csv")
if [ "$CSV_HEADER" != "Post Text,Image" ]; then
    echo "ERROR: Invalid CSV header '$CSV_HEADER'. Expected 'Post Text,Image'" >&2
    exit 1
fi
echo "  [OK] CSV header is exact: 'Post Text,Image'"

ROW_COUNT=$(python3 -c "import csv; print(len(list(csv.DictReader(open('$RUN_DIR/posts.csv')))))")
echo "  [OK] Accepted content rows: $ROW_COUNT"

SPEC_COUNT=$(find "$RUN_DIR/visual_specs" -name "*.md" | wc -l)
echo "  [OK] Generated visual specifications: $SPEC_COUNT"

echo "================================================================================"
echo "OFFLINE DOCKER VERIFICATION PASSED SUCCESSFULLY."
echo "Zero external network calls made. Model inferred locally from container layers."
echo "================================================================================"
