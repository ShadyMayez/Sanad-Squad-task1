# SanadSquad audit visuals

- Open `workflow_viewer.html` locally for the interactive, read-only architecture and observed-execution views. It has no network or CDN dependency.
- `workflow.svg` and `workflow.png` render the implemented LangGraph path and trusted-instruction boundary. `workflow.mmd` is the Mermaid representation.
- `execution_trace.svg` and `execution_trace.png` summarize the six-slot run named by `RUN` in `audit/scripts/build_closure_visuals.py`. They are generated from saved JSON artifacts, not a simulated trace.
- `workflow_viewer_screenshot.png` is a browser-rendered check of the final local viewer; the interactive HTML is the primary artifact.
- The run records total elapsed time and token usage, but not individual slot duration or queue wait. Those values are labeled unavailable; layout positions do not encode timing.
- Regenerate from the repository root with `PYTHONPATH=. .venv/bin/python audit/scripts/build_closure_visuals.py`. PNG conversion requires ImageMagick `magick`.
- `workflow_viewer_baseline.html` preserves the preceding audit viewer for comparison. The current viewer adds source-provenance and atomic-semantic stages.
