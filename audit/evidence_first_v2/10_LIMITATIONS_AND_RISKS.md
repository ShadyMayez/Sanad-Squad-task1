# Stage 10 / Risk: Limitations, Boundaries & Residual Risks

**Document ID:** `AUDIT_EVIDENCE_FIRST_V2_10_LIMITATIONS_AND_RISKS`  
**Date:** October 2026  
**System:** SanadSquad V2 Content Generation Engine  
**Status:** DISCLOSED & DOCUMENTED  

---

## 1. Disclosed Engineering Limitations

In accordance with the Science and Engineering Acceptance Gate, the following operational limitations and residual risks are explicitly declared:

### 1.1 Local Model Parameter Capacity (`qwen3.5:4b`)
- `qwen3.5:4b` is a 4-billion parameter quantized local model optimized for low-latency CPU/GPU inference on edge hardware.
- While it demonstrates reliable conformance verification and natural realization under constrained Pydantic schemas, it does not possess the broad world knowledge or nuanced stylistic flexibility of frontier 70B+ models.
- It must not be deployed with unconstrained open-ended prompts or zero-shot ungrounded reasoning tasks.

### 1.2 Knowledge Catalog Coverage Boundary
- The Evidence-First V2 engine operates strictly under a **closed-world authority assumption**.
- The current catalog (`knowledge/evidence_first_v2/catalog.json`) covers 24 verified propositions, 23 typed relations, and 7 evidence witnesses across SWC-107, SWC-104, SWC-113, SWC-105, and SCWE-028.
- The system will refuse to generate content (`INSUFFICIENT_EVIDENCE`) for vulnerability topics outside this approved catalog.
- Expanding coverage to new topics requires human curation and authorized domain-expert review of new canonical propositions and directional relations.

### 1.3 Local Engineering Qualification vs Commercial Publication Authority
- **Local Qualification Status:** Demonstrates that the software pipeline reliably selects evidence-supported units, verifies plan conformance, blocks adversarial inversions, and executes within workstation budgets.
- **Commercial Publication Boundary:** Does **NOT** constitute unmonitored automated social-media publishing authority. In production environments, enterprise policies should retain `require_human_approval_for_ship = true` for compliance and legal sign-off.

### 1.4 Residual Realization Semantic Drift Risk
- Moving fact selection upstream eliminates the majority of historical hallucination defects.
- However, natural-language realization retains a residual risk: phrasing, rhythm, or metaphorical hooks could theoretically introduce subtle ambiguity or register shifts.
- The plan-to-text conformance verifier and independent reviewer must remain active gates in production; they cannot be bypassed under the assumption that an evidence-first plan guarantees 100% faithful realization.

### 1.5 Workstation Hardware Boundary
- The system is architected for local workstations with ~16 GB RAM and ~4 GB VRAM.
- Ollama inference concurrency is strictly clamped to `max_concurrency = 1`. Attempting parallel model calls on this hardware profile will lead to VRAM exhaustion and inference failure.
