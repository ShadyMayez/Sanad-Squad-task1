# Reproducibility, Determinism & Execution Guide

**System:** SanadSquad Content Generation & Verification Pipeline (Evidence-First V2)  
**Date:** 2026-10-17  

---

## 1. Deterministic vs Stochastic Boundaries

Understanding the reproducibility of SanadSquad requires distinguishing between **deterministic pipeline contracts** and **stochastic model outputs**:

### Fully Deterministic Components (100% Bit-Exact Reproducibility)
The following components produce identical results across all environments, hardware architectures, and operating systems:
- **Proposition Catalog Validation:** Proposition graphs, relations, and approved witnesses in `knowledge/evidence_first_v2/catalog.json`.
- **Source Snapshot Provenance:** SHA-256 digests and exact byte-range slices into `source_snapshots/*.txt`.
- **Preflight Conformance Checks:** Vetoes for unlicensed instrumental mechanisms, universal scope expansions, comparative rankings, and alien vulnerability topics.
- **Brand & Platform Gate:** Enforcement of tweet length (≤ 280 chars), thread bounds (5–10 tweets), marketing bounds (exactly 1 tweet), allowed link lists, and banned vocabulary.
- **Export Packaging:** Exact CSV header (`Post Text,Image`), formatting, visual spec path references, and telemetry persistence.
- **Unit & Adversarial Tests:** All 170 tests in `tests/` and `audit/tests/` use deterministic test fixtures and mock doubles to verify control flow and safety invariant enforcement.

### Stochastic Model Components (Controlled Semantic Variance)
The following components involve local LLM inference (`qwen3.5:4b` via Ollama):
- **Writer Realization:** Converting assigned propositions and relations into natural language tweet prose.
- **Reviewer Rubric Scoring:** Qualitative 1–5 scoring and written feedback rationale.
- **Semantic Verification Decisions:** Model-judged entailment between emitted sentences and cited evidence spans.

> [!IMPORTANT]
> Because floating-point operations in neural network inference (especially across differing CPU instruction sets like AVX-512 vs NEON, GPU driver versions, and quantization backends) introduce minor numerical variance, **fresh LLM generations are not promised to be byte-identical to the historical sample**. However, **all deterministic safety, brand, and factual conformance invariants are guaranteed to hold on every run**.

---

## 2. Environment Prerequisites

### Option A: Local Python Runtime
- **Operating System:** Linux (Fedora 40+, Ubuntu 22.04+, Debian 12+) or macOS.
- **Python:** 3.12.x (installed in `.venv`).
- **Ollama:** Version 0.4.x+ with model `qwen3.5:4b` installed (`ollama pull qwen3.5:4b`).
- **Hardware:** Minimum 16 GB RAM (CPU mode) or NVIDIA GPU with 4+ GB VRAM.

### Option B: Self-Contained Offline Docker Runtime (Recommended for Audit)
- **Host Requirement:** Docker 24.0+ or Podman 4.5+ with rootless user socket.
- **Network:** Zero network access required (`--network none`).
- **Hardware:** 8+ CPU cores, 16 GB RAM recommended.

---

## 3. Step-by-Step Native Reproduction

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Run full regression test suite (170 tests)
pytest tests/ audit/tests/ -v

# 3. Verify proposition catalog integrity
python -c "from content_pipeline.proposition_catalog import load_catalog; cat = load_catalog(); assert not cat.validate_catalog_integrity()"

# 4. Execute a fresh Evidence-First V2 full 6-slot week
python run_week.py --plan plan.json --mode evidence_first_v2 --authorization-mode publication_eligible --output output/repro-week-01

# 5. Inspect generated CSV deliverable
head -n 10 output/repro-week-01/posts.csv
```

---

## 4. Step-by-Step Offline Docker Reproduction

```bash
# 1. Load the pre-built self-contained offline container image (exported outside Git)
podman load -i /home/shady/sandsquad_archive/sanadsquad-v2-final.tar
# (Or using docker): docker load -i sanadsquad-v2-final.tar

# 2. Prepare an output directory
mkdir -p output/docker-repro-week

# 3. Execute the full week inside the offline container (--network none)
podman run --rm --network none \
  --userns=keep-id \
  -v "$(pwd)/output/docker-repro-week":/app/output:Z \
  sanadsquad:v2-final \
  --plan /app/plan.json \
  --mode evidence_first_v2 \
  --authorization-mode publication_eligible \
  --output /app/output/v2-week

# 4. Verify output files on the host
ls -la output/docker-repro-week/v2-week/
cat output/docker-repro-week/v2-week/summary.json
head -n 10 output/docker-repro-week/v2-week/posts.csv
```
