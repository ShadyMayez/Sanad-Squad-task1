"""Regenerate the read-only final workflow viewer from a saved real run."""
from __future__ import annotations

import html
import json
import os
import subprocess
from pathlib import Path

from audit.semantic.inspect_new_run import inspect

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "audit/visuals"
RUN = ROOT / os.environ.get("SANADSQUAD_VIEWER_RUN", "output/semantic-release-week")
DATA = inspect(RUN)

STAGES = [
    ("inputs", "Validated inputs", "plan · brand · KB · registry", "#81a6ff"),
    ("fanout", "LangGraph fan-out", "one Send per slot", "#81a6ff"),
    ("research", "Research", "shared EvidenceLookup", "#56c9e8"),
    ("writer", "Registered Writer", "paraphrase pinned evidence", "#56c9e8"),
    ("extract", "Claim extraction", "atomic facts · qualifiers", "#f6bd69"),
    ("provenance", "Pinned provenance", "hash · quote · offsets", "#f6bd69"),
    ("context", "Source context", "bounded pinned windows", "#f6bd69"),
    ("roles", "Evidence-role classification", "normative · causal · descriptive", "#f6bd69"),
    ("relation", "Claim-relation verification", "entailment · syntax veto", "#56c9e8"),
    ("skeptic", "Skeptical evaluation", "independent second pass", "#56c9e8"),
    ("evaluate", "Rules + Reviewer approval", "hard gates · six scores", "#56c9e8"),
    ("decision", "Approval decision", "one revision maximum", "#f6bd69"),
    ("visual", "Visual specification", "accepted content only", "#44d6ad"),
    ("aggregate", "Plan-order results", "isolated slot failures", "#81a6ff"),
    ("acceptance", "Final acceptance gate", "relation recheck · review", "#44d6ad"),
    ("export", "Audit + accepted CSV", "spec: path · no publishing", "#44d6ad"),
]

DETAILS = {
    "inputs": "Schema validation loads the six-slot plan, brand rules, pinned knowledge base, and content-type registry before fan-out.",
    "fanout": "LangGraph emits an independent PieceState per slot. The shared model limit allows one local Ollama call at a time by default.",
    "research": "Deterministic topic selection uses EvidenceLookup. Missing or unsupported focus fails only its own slot.",
    "writer": "The registered Writer receives a trusted SystemMessage and untrusted pinned evidence. It may paraphrase while preserving factual meaning, scope, conditions, and certainty.",
    "extract": "Python segments every public sentence into atomic propositions and checks exact Writer mappings. Unsupported coverage blocks approval.",
    "provenance": "Python verifies source snapshot path, SHA-256, exact quote, and offsets before semantic evaluation.",
    "context": "Python retrieves bounded, hash-checked surrounding source context for exact spans. A selected quotation alone may not establish its asserted meaning.",
    "roles": "The model records source relationship types while Python stores auditable syntax hints for normative, causal, and descriptive spans. Labels are not proof.",
    "relation": "The semantic verifier compares each atomic claim's asserted relationship with its selected source spans. Python vetoes contradictory structured positives and normative-only root-cause inferences.",
    "skeptic": "An independent prompt checks the claim and same selected spans against pinned context. It may veto support; Python rechecks its relation fields.",
    "evaluate": "Python checks format and brand rules. The independent Reviewer receives its own trusted rubric SystemMessage and untrusted JSON task data, then returns scores, reasons, and corrections.",
    "decision": "Approval requires no hard errors, all final atomic verdicts SUPPORTED, rubric thresholds, and an approved Review. One rejected draft may be revised once; the next rejection drops it.",
    "visual": "The deterministic Visual Agent reads the accepted text and verified claims to write a content-aware specification. Rejected or failed work cannot reach it.",
    "aggregate": "Branch results are collected and restored to plan order. A failed worker does not terminate unrelated slots.",
    "acceptance": "The exporter rechecks supported relation records, selected exact spans, provenance, Reviewer approval, and every mandatory claim before accepting a CSV row.",
    "export": "The exporter repeats the acceptance gate, writes JSON audit artifacts and accepted-only Post Text,Image CSV. Image values are written-spec references, not media.",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def svg() -> str:
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1530 960" role="img" aria-label="SanadSquad final LangGraph workflow">',
        '<rect width="1530" height="960" fill="#071321"/>',
        '<text x="34" y="46" fill="#e8f3ff" font-family="system-ui" font-size="28" font-weight="700">Six independent slots · one shared Ollama limit</text>',
        '<text x="34" y="75" fill="#afc6dc" font-family="system-ui" font-size="15">Trusted instructions remain separate from dynamic evidence. Dashed paths are conditional.</text>']
    for index, (key, title, subtitle, color) in enumerate(STAGES):
        row, col = divmod(index, 4)
        x, y = 34 + col * 375, 112 + row * 172
        parts += [f'<g data-node="{key}" tabindex="0" role="button" aria-label="{esc(title)}">',
            f'<rect x="{x}" y="{y}" width="340" height="113" rx="17" fill="#12283e" stroke="{color}" stroke-width="2"/>',
            f'<rect x="{x}" y="{y}" width="340" height="7" rx="4" fill="{color}"/>',
            f'<text x="{x+18}" y="{y+46}" fill="#f2f8ff" font-family="system-ui" font-size="19" font-weight="700">{esc(title)}</text>',
            f'<text x="{x+18}" y="{y+77}" fill="#b8cfe2" font-family="system-ui" font-size="14">{esc(subtitle)}</text></g>']
        if col < 3:
            parts.append(f'<path d="M{x+344} {y+56} H{x+370}" stroke="#7b9bb7" stroke-width="3" marker-end="url(#arrow)"/>')
        elif row < 3:
            parts.append(f'<path d="M{x+170} {y+116} V{y+167} H204" fill="none" stroke="#7b9bb7" stroke-width="3" marker-end="url(#arrow)"/>')
    parts += ['<defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0 0 L8 4.5 L0 9" fill="none" stroke="#7b9bb7" stroke-width="2"/></marker></defs>',
        '<path d="M1329 574 H1515 V170 H1504" fill="none" stroke="#f6bd69" stroke-width="3" stroke-dasharray="9 7"/>',
        '<text x="1170" y="854" fill="#f6bd69" font-family="system-ui" font-size="15">first rejection → one revision</text>',
        '<text x="36" y="912" fill="#ff899b" font-family="system-ui" font-size="15">Second rejection → dropped; agent error → failed. Both aggregate without a visual spec or CSV row.</text>',
        '<text x="36" y="940" fill="#b9c9dc" font-family="system-ui" font-size="15">SystemMessage: versioned instructions · HumanMessage: untrusted source quotations and task data</text>',
        '</svg>']
    return ''.join(parts)


diagram = svg()
(OUT / "workflow.svg").write_text(diagram)
subprocess.run(["magick", "-background", "none", str(OUT / "workflow.svg"), str(OUT / "workflow.png")], check=True)
(OUT / "workflow.mmd").write_text('''flowchart LR
  I[Validated inputs] --> F[LangGraph Send per slot]
  F --> R[Research / EvidenceLookup] --> W[Registered Writer]
  W --> X[Atomic claim extraction] --> P[Pinned source provenance]
  P --> C
  subgraph SemanticNode[One LangGraph semantic node]
    C[Bounded pinned context] --> ROL[Evidence-role classification] --> REL[Claim-relation verification and veto] --> K[Independent skeptical audit]
  end
  K --> Q[Hard rules + Reviewer]
  Q --> D{Approved, valid, supported?}
  D -->|yes| V[Content-aware visual spec] --> A[Plan-order aggregation]
  D -->|first rejection| W
  D -->|second rejection| Drop[Dropped] --> A
  R -->|error| Fail[Failed slot] --> A
  P -->|source error| Fail
  REL -->|verifier error| Fail
  K -->|verifier error| Fail
  Q -->|review error| Fail
  V -->|visual error| Fail
  A --> G[Final acceptance relation recheck] --> E[JSON audit + accepted-only CSV]
  T[[Trusted SystemMessage instructions]] -.-> W
  T -.-> REL
  T -.-> K
  T -.-> Q
  U[[Dynamic HumanMessage task and untrusted sources]] -.-> W
  U -.-> REL
  U -.-> K
  U -.-> Q
  L[[Shared bounded Ollama]] -.-> W
  L -.-> REL
  L -.-> K
  L -.-> Q
''')

height = 200 + 98 * len(DATA["slots"])
trace = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1510 {height}" role="img" aria-label="Observed six-slot final run">',
    f'<rect width="1510" height="{height}" fill="#071321"/>',
    '<text x="35" y="45" fill="#f2f8ff" font-family="system-ui" font-size="27" font-weight="700">Observed local Ollama execution</text>',
    f'<text x="35" y="73" fill="#b8cfe2" font-family="system-ui" font-size="15">{esc(DATA["run"])} · {DATA["summary"]["elapsed_seconds"]} s total · per-slot duration unavailable</text>']
for index, slot in enumerate(DATA["slots"]):
    y = 105 + index * 98
    counts = ', '.join(f'{k}: {v}' for k, v in slot["verdict_counts"].items()) or "no verdicts"
    color = {"accepted": "#44d6ad", "dropped": "#f6bd69", "failed": "#ff899b"}[slot["status"]]
    trace += [f'<rect x="34" y="{y}" width="1442" height="83" rx="14" fill="#12283e" stroke="{color}"/>',
        f'<text x="51" y="{y+32}" fill="#f2f8ff" font-family="system-ui" font-size="18" font-weight="700">{esc(slot["id"])} · {esc(slot["status"].upper())}</text>',
        f'<text x="51" y="{y+62}" fill="#b8cfe2" font-family="system-ui" font-size="14">{esc(slot["type"])} · {esc(slot["topic"])} · {esc(", ".join(slot["source_ids"]))}</text>',
        f'<text x="730" y="{y+33}" fill="#e7f1fa" font-family="system-ui" font-size="15">{slot["draft_count"]} drafts · {slot["revisions"]} revisions · {slot["final_atomic_claims"]} claims</text>',
        f'<text x="730" y="{y+62}" fill="#b8cfe2" font-family="system-ui" font-size="14">{esc(counts)} · {slot["verification_disagreements"]} disagreements</text>']
trace.append(f'<text x="35" y="{height-27}" fill="#b8cfe2" font-family="system-ui" font-size="14">Observed from saved JSON artifacts. Stage order follows code; individual stage timings and concurrent queue wait are unavailable.</text></svg>')
(OUT / "execution_trace.svg").write_text(''.join(trace))
subprocess.run(["magick", "-background", "none", str(OUT / "execution_trace.svg"), str(OUT / "execution_trace.png")], check=True)

payload = json.dumps({"run": DATA, "details": DETAILS}, ensure_ascii=False).replace("<", "\\u003c")
viewer = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SanadSquad · Final workflow</title>
<style>:root{color-scheme:dark;--bg:#071321;--panel:#102439;--border:#31516d;--text:#f2f8ff;--muted:#b8cfe2}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 10% 0%,#1b3650,var(--bg) 50%);font:16px/1.5 system-ui;color:var(--text)}header,main{max-width:1560px;margin:auto;padding:24px}h1{margin:0;font-size:clamp(28px,4vw,42px)}p{color:var(--muted)}.stats,.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}.stat,.card,.panel{background:var(--panel);border:1px solid var(--border);border-radius:16px;padding:17px}.stat strong{display:block;font-size:25px}.stat span,.small{color:var(--muted);font-size:13px}.tabs{display:flex;gap:9px;margin:22px 0}.tabs button{background:#193853;color:var(--text);border:1px solid var(--border);border-radius:9px;padding:9px 14px;cursor:pointer}.tabs button.active{background:#236a69}.view{display:none}.view.active{display:block}.canvas{overflow:auto}.canvas svg{display:block;width:100%;min-width:900px;height:auto}.canvas [data-node]{cursor:pointer}.canvas [data-node]:hover rect{stroke-width:4}.detail{min-height:65px;padding-top:12px;border-top:1px solid var(--border)}.card{border-left:5px solid #44d6ad}.card.dropped{border-left-color:#f6bd69}.card.failed{border-left-color:#ff899b}.card h3{margin:0}.card p{margin:7px 0}.status{font-weight:750}.note{margin-top:17px;font-size:14px}a{color:#83d7ee}footer{max-width:1560px;margin:auto;padding:20px;color:var(--muted);font-size:13px}</style></head><body><header><div class="small">Read-only · actual LangGraph application</div><h1>SanadSquad workflow</h1><p>Prompt trust boundary, atomic grounding, one-revision routing, and observed local run.</p></header><main><section id="stats" class="stats"></section><nav class="tabs" aria-label="Views"><button class="active" data-tab="architecture">Architecture</button><button data-tab="execution">Observed execution</button></nav><section id="architecture" class="view active"><div class="panel"><div class="canvas">DIAGRAM</div><div class="detail"><strong id="detail-title">Select a stage</strong><p id="detail-text">Click a stage to inspect its real responsibility and trust boundary.</p></div></div><p class="note">The diagram shows possible routing. The execution view shows only what happened in the saved run.</p></section><section id="execution" class="view"><div class="panel"><div class="canvas">TRACE</div></div><div class="cards" id="cards"></div><p class="note">All statuses, claim counts, and verdict counts come from the saved run. For full reasons, see its review, validation, and semantic JSON artifacts. A model SUPPORTED decision is fallible; inspect the cited spans before publishing.</p></section></main><footer>No network, backend, CDN, publishing action, or editable state. Written visual specifications are not image media.</footer><script type="application/json" id="data">PAYLOAD</script><script>const d=JSON.parse(document.getElementById('data').textContent),s=d.run.summary;for(const [k,v] of [['Planned',s.planned],['Shipped',s.shipped],['Dropped',s.dropped],['Failed',s.failed],['Elapsed',s.elapsed_seconds+' s']]){const e=document.createElement('div');e.className='stat';const a=document.createElement('strong');a.textContent=v;const b=document.createElement('span');b.textContent=k;e.append(a,b);document.getElementById('stats').append(e)}for(const b of document.querySelectorAll('[data-tab]'))b.onclick=()=>{for(const x of document.querySelectorAll('[data-tab]'))x.classList.toggle('active',x===b);for(const x of document.querySelectorAll('.view'))x.classList.toggle('active',x.id===b.dataset.tab)};for(const n of document.querySelectorAll('[data-node]')){const show=()=>{document.getElementById('detail-title').textContent=n.getAttribute('aria-label');document.getElementById('detail-text').textContent=d.details[n.dataset.node]};n.onclick=show;n.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();show()}}}for(const x of d.run.slots){const c=document.createElement('article');c.className='card '+x.status;const h=document.createElement('h3');h.textContent=x.id;const p=document.createElement('p');p.textContent=x.topic||'No selected topic';const t=document.createElement('div');t.className='small';t.textContent=x.type+' · '+x.source_ids.join(', ');const st=document.createElement('div');st.className='status';st.textContent=x.status.toUpperCase();const m=document.createElement('div');m.className='small';m.textContent=x.draft_count+' drafts · '+x.review_count+' reviews · '+x.final_atomic_claims+' final claims · '+JSON.stringify(x.verdict_counts);c.append(h,p,t,st,m);if(x.reason){const r=document.createElement('p');r.className='small';r.textContent=x.reason;c.append(r)}document.getElementById('cards').append(c)}</script></body></html>'''
viewer = viewer.replace("DIAGRAM", diagram).replace("TRACE", ''.join(trace)).replace("PAYLOAD", payload)
viewer = viewer.replace("Prompt trust boundary, atomic grounding, one-revision routing, and observed local run.",
    "Pinned evidence, meaning-preserving writing, context-aware semantic review, and observed local run.")
viewer = viewer.replace("c.append(h,p,t,st,m);if(x.reason)", '''c.append(h,p,t,st,m);
const detail=document.createElement('div');detail.className='small';
const selected=x.final_verdicts.flatMap(v=>v.supporting_span_ids?.length?v.supporting_span_ids:(v.initial_pass?.support_option_ids||[]));
detail.textContent='Selected evidence: '+(selected.join(', ')||'none')+' · relation gates passed: '+x.relation_pass_count+' · relation gates failed: '+x.relation_failure_count+' · context windows: '+x.context_decisions+' · skeptical disagreements: '+x.verification_disagreements+' · revisions: '+x.revisions;
c.append(detail);
for(const v of x.final_verdicts){const q=document.createElement('p');q.className='small';const spans=(v.supporting_spans?.length?v.supporting_spans:(v.proposed_supporting_spans||[]));q.textContent=v.claim_id+': '+v.verdict+' · claim roles '+(v.claim_relations||[]).join(', ')+' · evidence relation '+(v.evidence_relation||'unavailable')+' · relation gate '+(v.relation_integrity_passed?'passed':(v.relation_error||'not passed'))+' · initial '+(v.initial_pass?.verdict||'unavailable')+' · skeptic '+(v.skeptical_pass?.verdict||'not run')+' · selected '+spans.map(z=>z.evidence_id+': “'+z.quote+'”').join(' | ')+' · context '+(v.context_windows||[]).map(w=>w.evidence_id+'@'+w.start+'-'+w.end+(w.window_partial?' [partial]':'')+(w.truncated?' [budget limited]':'')).join(', ');c.append(q)}
if(x.final_tweets.length){const copy=document.createElement('p');copy.className='small';copy.textContent='Final draft: '+x.final_tweets.join(' / ');c.append(copy)}
if(x.reason)''')
(OUT / "workflow_viewer.html").write_text(viewer)
print(f"Rendered closure visuals from {RUN}")
