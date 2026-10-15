# SanadSquad audit visuals

- Open `workflow_viewer.html` locally for the interactive architecture and execution views. It has no network or CDN dependency.
- `workflow.svg` and `workflow.png` are portable static renderings of the reconstructed code path. `workflow.mmd` is its Mermaid source.
- `execution_trace.svg` and `execution_trace.png` show the fresh six-slot run from `audit/evidence/fresh-week-inspection.json` and its saved artifacts.
- The run saved total elapsed time and token counts, but no per-slot duration or event timestamps. Those are labeled unavailable; layout positions are not timing measurements.
- Regenerate with `.venv/bin/python audit/scripts/build_visuals.py` from the repository root. PNG conversion requires ImageMagick `magick`.
