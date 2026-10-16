#!/usr/bin/env bash
# Reproducible local evidence run. No model substitution or forced approvals.
set -u
cd /home/shady/sandsquad || exit 2
benchmark_pid="${1:-}"
while [[ -n "$benchmark_pid" ]] && kill -0 "$benchmark_pid" 2>/dev/null; do sleep 5; done
export PYTHONPATH=.
export SANADSQUAD_LEGACY_BENCHMARK_OUTPUT=audit/relation_grounding/historical-replay.json
".venv/bin/python" audit/semantic/run_benchmark.py > audit/relation_grounding/historical-replay.log 2>&1
printf 'historical_benchmark\t%s\n' "$?" >> audit/relation_grounding/integration-exit-codes.tsv
export SANADSQUAD_RELATION_BENCHMARK_OUTPUT=audit/relation_grounding/heldout-final-code-results.json
".venv/bin/python" audit/relation_grounding/run_heldout.py > audit/relation_grounding/heldout-final-code.log 2>&1
printf 'heldout_final_code_replay\t%s\n' "$?" >> audit/relation_grounding/integration-exit-codes.tsv
".venv/bin/python" run_piece.py --type tech-thread --topic reentrancy --output output/relation-grounding-tech > audit/relation_grounding/technical-run.log 2>&1
printf 'technical_piece\t%s\n' "$?" >> audit/relation_grounding/integration-exit-codes.tsv
".venv/bin/python" run_piece.py --type marketing-post --topic 'access control' --output output/relation-grounding-marketing > audit/relation_grounding/marketing-run.log 2>&1
printf 'marketing_piece\t%s\n' "$?" >> audit/relation_grounding/integration-exit-codes.tsv
".venv/bin/python" run_week.py --plan plan.json --output output/relation-grounding-week > audit/relation_grounding/week-run.log 2>&1
printf 'six_slot_week\t%s\n' "$?" >> audit/relation_grounding/integration-exit-codes.tsv
