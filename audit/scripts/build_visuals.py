"""Create audit visualizations from inspected runtime data; no app writes."""
from __future__ import annotations

import html
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "audit/visuals"
DATA = json.loads((ROOT / "audit/evidence/fresh-week-inspection.json").read_text())
OUT.mkdir(exist_ok=True)


def esc(value):
    return html.escape(str(value), quote=True)


def node(key, x, y, w, h, title, lines, color):
    line_svg = "".join(f'<text x="{x+18}" y="{y+62+i*22}" class="sub">{esc(line)}</text>' for i, line in enumerate(lines))
    return f'''<g class="node" data-node="{esc(key)}" tabindex="0" role="button" aria-label="{esc(title)}">
      <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="#14243e" stroke="{color}" stroke-width="2"/>
      <rect x="{x}" y="{y}" width="{w}" height="7" rx="4" fill="{color}"/>
      <text x="{x+18}" y="{y+35}" class="title">{esc(title)}</text>{line_svg}</g>'''


def path(d, color="#7e95b5", label=None, lx=0, ly=0, dash=False):
    line = f'<path d="{d}" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#{"arrow-green" if color == "#3dd6a5" else "arrow-red" if color == "#ff7187" else "arrow-amber" if color == "#f7bb61" else "arrow-base"})"'
    if dash:
        line += ' stroke-dasharray="8 8"'
    line += '/>'
    if label:
        line += f'<text x="{lx}" y="{ly}" class="route" fill="{color}">{esc(label)}</text>'
    return line


style = '''<style>
 .title{font:700 20px system-ui,sans-serif;fill:#f3f8ff}
 .sub{font:15px system-ui,sans-serif;fill:#b8c9df}
 .route{font:700 15px system-ui,sans-serif}
 .section{font:700 16px system-ui,sans-serif;letter-spacing:2px;fill:#8da4c5}
 .node{cursor:pointer}
 .node:hover rect:first-child,.node:focus rect:first-child{stroke-width:4}
 </style>'''

defs = '''<defs>
 <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#091427"/><stop offset="1" stop-color="#101f38"/></linearGradient>
 <marker id="arrow-base" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M1 1 L11 6 L1 11" fill="none" stroke="#7e95b5" stroke-width="2"/></marker>
 <marker id="arrow-green" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M1 1 L11 6 L1 11" fill="none" stroke="#3dd6a5" stroke-width="2"/></marker>
 <marker id="arrow-red" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M1 1 L11 6 L1 11" fill="none" stroke="#ff7187" stroke-width="2"/></marker>
 <marker id="arrow-amber" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M1 1 L11 6 L1 11" fill="none" stroke="#f7bb61" stroke-width="2"/></marker>
 </defs>'''

parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1860 1100" role="img" aria-label="SanadSquad actual LangGraph architecture">{defs}{style}<rect width="1860" height="1100" fill="url(#bg)"/>',
         '<text x="50" y="68" font-family="system-ui,sans-serif" font-size="36" font-weight="800" fill="#f3f8ff">SanadSquad · Actual workflow</text>',
         '<text x="50" y="100" font-family="system-ui,sans-serif" font-size="17" fill="#a4bbd7">One weekly LangGraph fan-out, six isolated slots, one shared model instance per run</text>',
         '<text x="50" y="390" class="section">PER-SLOT INNER STATEGRAPH</text>']

parts += [
    node("inputs", 50, 140, 230, 170, "Editable inputs", ["plan · brand · KB", "writer files · rubric", "registry · environment"], "#83a5ff"),
    node("orchestrator", 335, 140, 250, 170, "Week orchestrator", ["CLI validates + overrides", "LangGraph WeekState", "Send one worker / slot"], "#83a5ff"),
    node("fanout", 640, 120, 360, 210, "Six Send branches", ["thread_1  ·  post_1", "thread_2  ·  post_2", "thread_3  ·  post_3", "3 technical  ·  3 marketing"], "#83a5ff"),
    node("skill", 1060, 140, 300, 150, "Shared EvidenceLookup", ["Research selects KB topic", "Reviewer checks cited IDs", "Local excerpts + URLs"], "#b39aff"),
    node("limiter", 1415, 140, 390, 150, "Ollama service", ["qwen3.5:4b · ChatOllama", "1 active call per model instance", "Timeout + bounded transport retry"], "#b39aff"),
    node("research", 50, 455, 240, 150, "Research", ["Topic + source provenance", "Failure → isolated slot"], "#46c6e8"),
    node("writer", 345, 455, 240, 150, "Registered writer", ["Technical or marketing file", "Draft + claim IDs"], "#46c6e8"),
    node("validator", 640, 455, 240, 150, "Code validator", ["Length · brand · links", "Sentence + evidence IDs"], "#6be0c2"),
    node("reviewer", 935, 455, 240, 150, "Reviewer", ["Six rubric scores", "Reasons + support quotes"], "#46c6e8"),
    node("decision", 1230, 455, 240, 150, "Decision", ["Approved AND hard-valid?", "Attempt counter ≤ 2"], "#f7bb61"),
    node("visual", 1525, 455, 280, 150, "Visual Agent", ["Written image specification", "Accepted pieces only"], "#3dd6a5"),
    node("failed", 50, 775, 250, 125, "Failed slot", ["Agent/source exception", "Other slots continue"], "#ff7187"),
    node("revision", 365, 775, 265, 125, "One revision", ["Review feedback → writer", "No third draft"], "#f7bb61"),
    node("dropped", 690, 775, 265, 125, "Dropped slot", ["Second rejection", "Never reaches Visual/CSV"], "#ff7187"),
    node("aggregate", 1015, 775, 340, 125, "Deterministic collection", ["Results sorted by plan order", "Failures retained per slot"], "#3dd6a5"),
    node("artifacts", 1415, 775, 390, 155, "Run folder + export", ["JSON trail · drafts · reviews", "accepted-only posts.csv", "spec:visual_specs/<slot>.md"], "#83a5ff"),
]

parts += [
    path("M280 225 H335"), path("M585 225 H640"),
    path("M820 330 V375 H170 V455"),
    path("M290 530 H345"), path("M585 530 H640"), path("M880 530 H935"), path("M1175 530 H1230"),
    path("M1470 530 H1525", "#3dd6a5", "approve", 1475, 515),
    path("M1640 605 V750 H1185 V775", "#3dd6a5"),
    path("M1350 605 V680 H822 V775", "#ff7187", "second rejection", 880, 666),
    path("M1280 605 V700 H497 V775", "#f7bb61", "first rejection", 676, 687),
    path("M497 775 V665 H465 V605", "#f7bb61", "feedback", 375, 692),
    path("M170 605 V740 H175 V775", "#ff7187", "agent error", 55, 724),
    path("M175 900 V958 H1080 V900", "#ff7187"), path("M822 900 V982 H1215 V900", "#ff7187"),
    path("M1355 838 H1415", "#3dd6a5"),
    path("M1195 290 V360 H170 V455", "#b39aff", None, dash=True),
    path("M1250 290 V390 H1055 V455", "#b39aff", None, dash=True),
    path("M1550 290 V410 H465 V455", "#b39aff", None, dash=True),
    path("M1670 290 V420 H1055 V455", "#b39aff", None, dash=True),
    '<text x="50" y="1010" font-family="system-ui,sans-serif" font-size="17" fill="#9db5d2">Solid arrows: graph routes   ·   dashed purple: shared service access   ·   green: accepted   ·   amber: revision   ·   coral: drop/failure</text>',
    '<text x="50" y="1040" font-family="system-ui,sans-serif" font-size="15" fill="#7189aa">Architecture paths are implemented possibilities. The observed six-slot run took only the accepted route.</text>',
    '</svg>',
]
workflow_svg = "\n".join(parts)
(OUT / "workflow.svg").write_text(workflow_svg)

mermaid = '''flowchart LR
  I[(plan.json, brand-voice.md, kb.json, registry, instructions, rubric)] --> O[CLI + LangGraph WeekState]
  O -->|Send × 6: 3 tech + 3 marketing| W[Independent slot worker]
  W --> R[Research / KB topic + evidence]
  R --> T[Registered technical or marketing Writer]
  T --> V[Deterministic validation]
  V --> Q[Reviewer / scored rubric + claim support]
  Q --> D{Approved and valid?}
  D -->|yes| X[Visual Agent / written spec]
  D -->|first no: one revision| T
  D -->|second no| DROP[Dropped]
  R -->|error| FAIL[Failed slot]
  T -->|error| FAIL
  Q -->|error| FAIL
  X --> A[Sort results by plan order]
  DROP --> A
  FAIL --> A
  A --> J[(JSON trail + accepted-only posts.csv)]
  S[[Shared EvidenceLookup]] -.-> R
  S -.-> Q
  L[[LocalModel semaphore / qwen3.5:4b]] -.-> T
  L -.-> Q
'''
(OUT / "workflow.mmd").write_text(mermaid)


def trace_svg(data):
    slots = data["slots"]
    h = 320 + len(slots) * 122
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1580 {h}" role="img" aria-label="Observed six-slot execution trace">{defs}{style}<rect width="1580" height="{h}" fill="url(#bg)"/>',
           '<text x="48" y="64" font-family="system-ui,sans-serif" font-size="34" font-weight="800" fill="#f3f8ff">Observed execution · fresh six-slot run</text>',
           '<text x="48" y="99" font-family="system-ui,sans-serif" font-size="17" fill="#a4bbd7">Saved artifacts: six accepted, zero revisions; per-slot durations unavailable</text>']
    headers = [(50, "SLOT / WRITER"), (280, "TOPIC / SOURCES"), (720, "DRAFT"), (900, "REVIEW"), (1090, "VISUAL"), (1280, "FINAL")]
    for x, label in headers:
        out.append(f'<text x="{x}" y="165" class="section">{esc(label)}</text>')
    for i, slot in enumerate(slots):
        y = 190 + i * 122
        out.append(f'<rect x="42" y="{y}" width="1490" height="105" rx="16" fill="#14243e" stroke="#29435e" stroke-width="2"/>')
        out.append(f'<rect x="42" y="{y}" width="7" height="105" rx="3" fill="#3dd6a5"/>')
        out.append(f'<text x="60" y="{y+36}" class="title">{esc(slot["id"])}</text>')
        out.append(f'<text x="60" y="{y+72}" class="sub">{esc("technical" if slot["type"]=="tech-thread" else "marketing")}</text>')
        out.append(f'<text x="280" y="{y+36}" class="title">{esc(slot["topic"])}</text>')
        out.append(f'<text x="280" y="{y+72}" class="sub">{esc(", ".join(slot["source_ids"]))}</text>')
        out.append(f'<text x="720" y="{y+36}" class="title">{slot["draft_count"]} draft</text>')
        out.append(f'<text x="720" y="{y+72}" class="sub">{slot["content_revisions"]} revisions</text>')
        out.append(f'<text x="900" y="{y+36}" class="title">Approved</text>')
        out.append(f'<text x="900" y="{y+72}" class="sub">{slot["review_count"]} review</text>')
        out.append(f'<text x="1090" y="{y+36}" class="title">Spec present</text>')
        out.append(f'<text x="1090" y="{y+72}" class="sub">written .md</text>')
        out.append(f'<text x="1280" y="{y+36}" class="title" fill="#3dd6a5">Accepted</text>')
        out.append(f'<text x="1280" y="{y+72}" class="sub">{slot["tweet_count"]} tweet(s)</text>')
    out.append(f'<text x="48" y="{h-65}" font-family="system-ui,sans-serif" font-size="18" fill="#d8e7f8">Run elapsed: {data["summary"]["elapsed_seconds"]:.3f}s · Prompt: {data["summary"]["prompt_tokens_recorded"]:,} · Completion: {data["summary"]["completion_tokens_recorded"]:,} · Peak saved counter: {data["summary"]["peak_simultaneous_ollama_calls"]}</text>')
    out.append(f'<text x="48" y="{h-33}" font-family="system-ui,sans-serif" font-size="15" fill="#8da4c5">Observed from persisted JSON. Stage order follows code; individual stage and slot timings were not recorded.</text></svg>')
    return "\n".join(out)

(OUT / "execution_trace.svg").write_text(trace_svg(DATA))

for name in ("workflow", "execution_trace"):
    subprocess.run(["magick", "-density", "150", str(OUT / f"{name}.svg"), str(OUT / f"{name}.png")], check=True)

node_detail = {
    "inputs": ["Data files", "Plan, brand policy, local KB, registry, agent instructions and rubric are loaded at runtime."],
    "orchestrator": ["Outer graph", "The CLI validates inputs, applies overrides, creates one LocalModel, and invokes a LangGraph WeekState."],
    "fanout": ["Six independent slots", "START emits one Send per slot. Each worker owns a separate PieceState; exporter sorts returned results by plan order."],
    "skill": ["Shared evidence skill", "Research selects a KB topic. Reviewer verifies IDs against the selected evidence list. The skill does not prove semantic support."],
    "limiter": ["Ollama", "ChatOllama uses qwen3.5:4b. Default semaphore limit is one per LocalModel instance, not process-global."],
    "research": ["Research Agent", "Empty focus selects KB[index]; explicit focus uses lexical matching. Topic, evidence IDs, excerpts and URLs are passed forward."],
    "writer": ["Registered Writer", "One Python writer class reads distinct technical or marketing instructions. It returns structured tweets and claim mappings."],
    "validator": ["Deterministic gate", "Code checks tweet count/length, brand terms, hashtags, links, sentence mappings and known evidence IDs."],
    "reviewer": ["Reviewer Agent", "The model assigns six rubric scores, reasons, corrections and claim-support quotes. Code verifies quote substring and score thresholds."],
    "decision": ["Conditional routing", "Approval requires no hard errors. First rejection returns feedback to Writer; second rejection drops the slot."],
    "visual": ["Visual Agent", "Only approved pieces reach this node. It writes an image specification, not a rendered image."],
    "failed": ["Isolated failure", "Research, writer, reviewer or unexpected worker errors produce a failed slot; other slots continue."],
    "revision": ["One revision", "The writer receives reasons and corrections. A successful second draft is the final allowed content attempt."],
    "dropped": ["Permanent drop", "A second rejection is retained in failures.json and never exported to posts.csv."],
    "aggregate": ["Deterministic aggregation", "The results reducer collects branches; exporter orders them to the original plan."],
    "artifacts": ["Run folder", "JSON trail, draft files, visual_specs, accepted-only posts.csv and summary. Raw model events and per-slot duration are unavailable."],
}

payload = json.dumps({"run": DATA, "nodes": node_detail}).replace("<", "\\u003c")
viewer = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SanadSquad · Independent Workflow Audit</title>
<style>
:root{color-scheme:dark;--bg:#071120;--panel:#102039;--line:#29415e;--text:#f3f8ff;--muted:#adc1db;--green:#3dd6a5;--amber:#f7bb61;--red:#ff7187;--purple:#b39aff}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 12% 0%,#132949 0%,var(--bg) 48%);color:var(--text);font:16px/1.5 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
header{padding:34px clamp(20px,4vw,64px) 20px;display:flex;justify-content:space-between;align-items:start;gap:20px;flex-wrap:wrap}
.eyebrow{font-size:12px;letter-spacing:.2em;text-transform:uppercase;color:#86a8d6;font-weight:800}h1{margin:7px 0;font-size:clamp(30px,3vw,46px);letter-spacing:-.035em}p{margin:0;color:var(--muted)}
.stamp{border:1px solid #946b52;background:#332718;color:#f7d7b0;border-radius:999px;padding:9px 16px;font-size:13px;font-weight:800}
.shell{max-width:1900px;margin:auto;padding:0 clamp(20px,4vw,64px) 60px}.metrics{display:grid;grid-template-columns:repeat(5,minmax(130px,1fr));gap:12px;margin:20px 0}.metric{background:#11233d;border:1px solid var(--line);border-radius:15px;padding:16px}.metric strong{display:block;font-size:25px}.metric span{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.1em}
.tabs{display:flex;gap:9px;margin:27px 0 14px}.tabs button,.zoom button{border:1px solid #365475;background:#172c4b;color:#dcecff;border-radius:10px;padding:10px 15px;font:inherit;cursor:pointer}.tabs button.active{background:#204f62;border-color:#40c9bc;color:white}.tabs button:hover,.zoom button:hover{border-color:#6ca5d6}
.view{display:none}.view.active{display:block}.panel{background:#0d1c32;border:1px solid var(--line);border-radius:20px;box-shadow:0 22px 65px #02081688;overflow:hidden}.toolbar{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:14px 18px;border-bottom:1px solid var(--line);flex-wrap:wrap}.toolbar strong{font-size:15px}.toolbar small{color:var(--muted)}.zoom{display:flex;align-items:center;gap:9px}.zoom input{accent-color:#3dd6a5}
.canvas{overflow:auto;min-height:510px;max-height:750px}.canvas svg{display:block;width:100%;height:auto;transform-origin:top left;transition:transform .15s ease}.inspect{padding:18px 22px;min-height:91px;border-top:1px solid var(--line);display:grid;grid-template-columns:230px 1fr;gap:20px}.inspect b{color:#c4f8ec}.inspect p{font-size:14px}
.legend{display:flex;gap:18px;flex-wrap:wrap;margin:15px 0 28px;color:var(--muted);font-size:13px}.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}.cards{display:grid;grid-template-columns:repeat(3,minmax(240px,1fr));gap:14px;padding:18px}.card{background:#132741;border:1px solid #31516c;border-radius:16px;padding:18px;position:relative;overflow:hidden}.card:before{content:"";height:5px;background:var(--green);position:absolute;top:0;left:0;right:0}.card h3{margin:3px 0 4px;font-size:21px}.type{color:#83c6e3;font-size:12px;letter-spacing:.13em;text-transform:uppercase;font-weight:800}.topic{color:#d6e7fa;margin:10px 0}.chips{display:flex;flex-wrap:wrap;gap:7px;margin:12px 0}.chip{border:1px solid #3d617d;border-radius:999px;padding:4px 9px;color:#c7d9ec;font-size:12px}.ok{color:var(--green);font-weight:800}.meta{color:var(--muted);font-size:13px;margin-top:12px;border-top:1px solid #29445c;padding-top:11px}.note{padding:19px;color:#b7cce5;font-size:14px;border-top:1px solid var(--line)}a{color:#8bd5f1}footer{color:#7791b0;font-size:13px;margin-top:24px}
@media(max-width:1000px){.metrics{grid-template-columns:repeat(2,1fr)}.cards{grid-template-columns:repeat(2,1fr)}}@media(max-width:660px){.cards{grid-template-columns:1fr}.inspect{grid-template-columns:1fr}.canvas{min-height:320px}.metrics{grid-template-columns:1fr 1fr}}
</style></head><body><header><div><div class="eyebrow">Independent engineering audit · read only</div><h1>SanadSquad workflow</h1><p>Implemented graph, observed six-slot execution, and evidence boundaries.</p></div><div class="stamp">REQUIRES REMEDIATION · content grounding</div></header><main class="shell">
<section class="metrics" id="metrics"></section><nav class="tabs" aria-label="Visualization views"><button id="architecture-tab" class="active" type="button">Architecture</button><button id="execution-tab" type="button">Observed execution</button></nav>
<section id="architecture" class="view active"><div class="panel"><div class="toolbar"><div><strong>LangGraph routing and shared services</strong><br><small>Click a node for implementation detail · zoom and scroll to inspect</small></div><div class="zoom"><button id="zoom-out" type="button" aria-label="Zoom out">−</button><input id="zoom" type="range" min="50" max="190" value="100" aria-label="Diagram zoom"><button id="zoom-in" type="button" aria-label="Zoom in">+</button><span id="zoom-label">100%</span></div></div><div class="canvas" id="canvas">SVG_PLACEHOLDER</div><div class="inspect"><b id="detail-title">Select a node</b><p id="detail-text">The diagram shows code paths, including failure and revision routes. The observed run used the accepted path for all six slots.</p></div></div><div class="legend"><span><i class="dot" style="background:#46c6e8"></i>Agent</span><span><i class="dot" style="background:#f7bb61"></i>Decision / revision</span><span><i class="dot" style="background:#b39aff"></i>Shared service</span><span><i class="dot" style="background:#83a5ff"></i>Input / artifact</span><span><i class="dot" style="background:#3dd6a5"></i>Accepted route</span><span><i class="dot" style="background:#ff7187"></i>Drop / error route</span></div></section>
<section id="execution" class="view"><div class="panel"><div class="toolbar"><div><strong>Fresh real Ollama run · six independent slots</strong><br><small>Observed from persisted JSON and CSV; per-slot duration was not recorded</small></div><small id="run-elapsed"></small></div><div class="cards" id="cards"></div><div class="note">The six cards show saved outcomes, not a hypothetical trace. All final reviewers approved on the first pass. The separate scientific audit found five shipped claims unsupported or overbroad, so accepted here means the application accepted them, not editorial clearance. <a href="../04_SCIENTIFIC_AND_GROUNDING_AUDIT.md">Read the claim audit</a>.</div></div></section>
<footer>Local artifact · no backend, network request, CDN, publishing action, or editable state. Architecture and execution use the committed application and audit run evidence.</footer></main>
<script type="application/json" id="audit-data">JSON_PLACEHOLDER</script><script>
const payload=JSON.parse(document.getElementById('audit-data').textContent);const run=payload.run;
const metrics=[['Planned',run.summary.planned],['Accepted',run.summary.shipped],['Dropped',run.summary.dropped],['Failed',run.summary.failed],['Run time',run.summary.elapsed_seconds+' s']];
for(const [label,value] of metrics){const box=document.createElement('div');box.className='metric';const strong=document.createElement('strong');strong.textContent=value;const span=document.createElement('span');span.textContent=label;box.append(strong,span);document.getElementById('metrics').append(box)}
document.getElementById('run-elapsed').textContent='Prompt '+run.summary.prompt_tokens_recorded.toLocaleString()+' · Completion '+run.summary.completion_tokens_recorded.toLocaleString()+' · peak saved counter '+run.summary.peak_simultaneous_ollama_calls;
for(const slot of run.slots){const card=document.createElement('article');card.className='card';const type=document.createElement('div');type.className='type';type.textContent=slot.type;const title=document.createElement('h3');title.textContent=slot.id;const topic=document.createElement('p');topic.className='topic';topic.textContent=slot.topic;const chips=document.createElement('div');chips.className='chips';for(const source of slot.source_ids){const chip=document.createElement('span');chip.className='chip';chip.textContent=source;chips.append(chip)}const status=document.createElement('div');status.className='ok';status.textContent=slot.status.toUpperCase();const meta=document.createElement('div');meta.className='meta';meta.textContent=slot.draft_count+' draft · '+slot.content_revisions+' revisions · '+slot.review_count+' review · visual spec '+(slot.visual_spec?'present':'absent')+' · '+slot.tweet_count+' tweet(s) · duration unavailable';card.append(type,title,topic,chips,status,meta);document.getElementById('cards').append(card)}
for(const [tab,view] of [['architecture-tab','architecture'],['execution-tab','execution']]){document.getElementById(tab).addEventListener('click',()=>{for(const id of ['architecture','execution'])document.getElementById(id).classList.toggle('active',id===view);for(const id of ['architecture-tab','execution-tab'])document.getElementById(id).classList.toggle('active',id===tab)})}
const diagram=document.querySelector('#canvas svg');const zoom=document.getElementById('zoom');function setZoom(value){zoom.value=value;diagram.style.width=value+'%';document.getElementById('zoom-label').textContent=value+'%'}zoom.addEventListener('input',()=>setZoom(zoom.value));document.getElementById('zoom-in').addEventListener('click',()=>setZoom(Math.min(190,Number(zoom.value)+10)));document.getElementById('zoom-out').addEventListener('click',()=>setZoom(Math.max(50,Number(zoom.value)-10)));
for(const el of document.querySelectorAll('[data-node]')){const show=()=>{const detail=payload.nodes[el.dataset.node];if(!detail)return;document.getElementById('detail-title').textContent=detail[0];document.getElementById('detail-text').textContent=detail[1]};el.addEventListener('click',show);el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();show()}})}
</script></body></html>'''
viewer = viewer.replace("SVG_PLACEHOLDER", workflow_svg).replace("JSON_PLACEHOLDER", payload)
(OUT / "workflow_viewer.html").write_text(viewer)

print("Created workflow.mmd, workflow.svg/png, execution_trace.svg/png, workflow_viewer.html")
