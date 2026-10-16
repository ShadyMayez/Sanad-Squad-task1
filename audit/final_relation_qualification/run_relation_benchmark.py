"""Run the independently labeled held-out relation benchmark.

Supports both:
1. Deterministic Structural Gate evaluation (fast structural rule checks).
2. Real Local Model Semantic Entailment evaluation via Ollama (qwen3.5:4b).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
WORKSPACE = Path(__file__).resolve().parents[2]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from content_pipeline.config import load_kb, settings
from content_pipeline.claim_extraction import extract_sentence_relations_for_sentence
from content_pipeline.relation_integrity import verify_sentence_relation
from content_pipeline.semantic_verification import SemanticVerifier
from content_pipeline.llm import LocalModel
from content_pipeline.text_spans import source_span_options
from langchain_core.messages import SystemMessage
from content_pipeline.agents import instruction

HERE = Path(__file__).parent
FIXTURE = HERE / "fixtures/heldout_relation_benchmark.json"
OUT = HERE / "heldout-relation-benchmark-results.json"


async def evaluate_benchmark(use_model: bool = False):
    cases = json.loads(FIXTURE.read_text())
    kb = load_kb()
    evidence_map = {e.id: e for v in kb.vulnerabilities for e in v.evidence}
    eval_mode = "REAL_OLLAMA_MODEL" if use_model else "DETERMINISTIC_STRUCTURAL"

    print(f"Evaluating {len(cases)} cases in held-out relation benchmark [Mode: {eval_mode}]...", flush=True)

    verifier = None
    system_msg = None
    if use_model:
        cfg = settings()
        model = LocalModel(cfg["model"], cfg["base_url"], cfg["max_concurrency"], cfg["timeout"], cfg["transport_retries"])
        verifier = SemanticVerifier(model)
        system_msg = SystemMessage(content=instruction("instructions/semantic-verifier.md"))

    rows = []
    detected_count = 0
    correct_detection_type_count = 0
    correct_entailment_count = 0
    causal_rejection_target = 0
    causal_rejection_correct = 0

    started = time.monotonic()
    for c in cases:
        ev = evidence_map[c["evidence_id"]]
        spans = source_span_options(ev.source_quote or "")

        # 1. Detection
        rels = extract_sentence_relations_for_sentence(c["sentence"], 0, 1, 0, len(c["sentence"]), [c["evidence_id"]])
        detected = len(rels) > 0
        detected_rel = rels[0] if detected else None

        if detected:
            detected_count += 1
            if detected_rel.relation_type == c["expected_relation"]:
                correct_detection_type_count += 1

        # 2. Entailment / Verification
        if detected_rel:
            if use_model:
                verified_rel, _ = await verifier.verify_relation_semantic(detected_rel, [ev], system_msg)
                actual_verdict = verified_rel.semantic_verdict or "INSUFFICIENT_EVIDENCE"
                reason = verified_rel.justification or ""
            else:
                assessment = verify_sentence_relation(detected_rel, spans)
                actual_verdict = "SUPPORTED" if assessment.passed else "INSUFFICIENT_EVIDENCE"
                reason = assessment.reason
        else:
            actual_verdict = "DETECTION_FAILED"
            reason = "No relation detected by sentence pattern extractor"

        expected = c["expected_verdict"]
        correct_entailment = (actual_verdict == expected)
        if correct_entailment:
            correct_entailment_count += 1

        if expected != "SUPPORTED":
            causal_rejection_target += 1
            if actual_verdict != "SUPPORTED":
                causal_rejection_correct += 1

        row = {
            **c,
            "detected": detected,
            "detected_type": detected_rel.relation_type if detected_rel else None,
            "detected_connector": detected_rel.connector if detected_rel else None,
            "actual_verdict": actual_verdict,
            "correct_entailment": correct_entailment,
            "reason": reason,
        }
        rows.append(row)
        print(f"[{c['id']}] {c['category']}: detected={detected} ({row['detected_type']}) | expected={expected} actual={actual_verdict} -> {'PASS' if correct_entailment else 'FAIL'}")

    elapsed = round(time.monotonic() - started, 3)
    total = len(cases)
    detection_coverage = round(detected_count / total, 4)
    detection_type_acc = round(correct_detection_type_count / total, 4)
    entailment_accuracy = round(correct_entailment_count / total, 4)
    adverse_rejection_rate = round(causal_rejection_correct / causal_rejection_target, 4) if causal_rejection_target else 1.0

    metrics = {
        "evaluation_mode": eval_mode,
        "elapsed_seconds": elapsed,
        "total_cases": total,
        "relationship_detection_coverage": detection_coverage,
        "relationship_type_accuracy": detection_type_acc,
        "relationship_entailment_accuracy": entailment_accuracy,
        "correct_rejection_of_unsupported_assertions": adverse_rejection_rate,
        "supported_recall": round(sum(r["actual_verdict"] == "SUPPORTED" for r in rows if r["expected_verdict"] == "SUPPORTED") / sum(r["expected_verdict"] == "SUPPORTED" for r in rows), 4),
        "false_acceptance_rate": round(sum(r["actual_verdict"] == "SUPPORTED" for r in rows if r["expected_verdict"] != "SUPPORTED") / sum(r["expected_verdict"] != "SUPPORTED" for r in rows), 4),
        "historical_frozen_benchmark_note": "The older 64-case frozen semantic benchmark achieved 82.35% (28/34) supported recall, which failed the preset 85% target and remains formally recorded.",
    }

    result_payload = {"metrics": metrics, "rows": rows}
    OUT.write_text(json.dumps(result_payload, indent=2) + "\n")
    print(f"\n=== BENCHMARK METRICS [{eval_mode}] ===")
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", action="store_true", help="Run with real local Ollama model")
    args = parser.parse_args()
    asyncio.run(evaluate_benchmark(use_model=args.model))
