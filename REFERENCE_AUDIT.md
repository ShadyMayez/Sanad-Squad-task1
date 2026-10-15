# AutoPost AI reference audit

Upstream: `https://github.com/rayane-rhsn/autopost-ai.git`  
Pinned commit: `5fa0ba548dee97051f37688348ba08e99f69c184`  
License: MIT; notice retained in `reference-autopost-ai/LICENSE`.

The snapshot was inspected before adaptation. Its `main.py` is a sequential LangGraph `StateGraph`: history → trend research → planning → writing → image sourcing → scheduling → saved history → reporting → email. It has no reviewer or per-piece rejection gate. The original config requires Groq and optional Serper, Unsplash, and Gmail credentials; its tools can send email and write post history. Those side effects do not belong in the local assignment path. The original writer asks for hashtags and Unsplash queries, contrary to this brand and image-spec fallback. Its Pydantic schemas establish useful typed handoffs, but their shapes do not represent evidence, claims, revisions, or slot outcomes.

| Upstream module | Decision | Reason / replacement |
|---|---|---|
| `main.py` | Adapt graph pattern | Keep explicit `StateGraph` handoffs; replace sequential whole-week pipeline with per-slot `Send` branches and conditional review routing in `content_pipeline/graph.py`. |
| `models/schemas.py` | Adapt typed schema pattern | Define stricter Pydantic input, claim, review, and result contracts in `content_pipeline/schemas.py`. |
| `agents/trend_researcher.py`, `content_planner.py` | Replace | Offline KB selection and explicit plan input remove remote trend search and model-planned schedule. |
| `agents/writer.py` | Replace | File-driven technical and marketing instructions, claim mappings, and local Ollama structured output. |
| `agents/image_sourcer.py` | Replace | Written visual specifications run after approval only. |
| `agents/scheduler.py`, `reporter.py` | Remove from runnable path | Scheduling and email are outside the PDF; run summary and artifact export are deterministic code. |
| `tools/serper_tool.py`, `unsplash_tool.py`, `gmail_tool.py` | Remove from runnable path | No external service credentials or outbound publishing side effects. |
| `memory/content_store.py` | Replace | Per-run immutable audit artifacts replace mutable global history. |
| `utils.py`, `config.py` | Replace | Groq-specific retry/configuration replaced with bounded Ollama settings. |

No upstream Python module was copied verbatim into the adapted package. The reuse is its LangGraph orchestration and Pydantic handoff approach, with a pristine source snapshot for traceability. Keeping its original implementations would violate the assignment's review, grounding, and side-effect constraints.

