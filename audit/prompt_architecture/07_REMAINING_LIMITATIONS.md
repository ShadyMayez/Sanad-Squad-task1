# Remaining prompt limitations

Professional system instructions improve role clarity and keep source text out of the trusted instruction channel, but prompts alone do not enforce correctness. The local 4B model can still misread a causal relationship or omit a structured field. The semantic verifier's first pass falsely accepted one mitigation overclaim on the unchanged benchmark; a skeptical selected-span pass vetoed it. Both passes use the same model, so correlated errors remain possible. The Reviewer is a separate rubric decision but also uses that model; Python ultimately enforces deterministic and semantic hard gates.

The Reviewer once returned `approved=false` while assigning every criterion a passing score and then reasoned at length that no defect existed. Its task is now compact and gives measured tweet-array structure; one bounded consistency re-evaluation is allowed. Repeated contradiction fails the slot without forcing approval. A low score on a subtle quality issue can still be mistaken, so a single successful calibration and week cannot establish stable reviewer reliability.

The six injection probes show no false acceptance for those fixtures. They do not cover every attack style, all cross-agent paths, or model drift. Untrusted evidence, draft text, and reviewer feedback must remain in task messages. Tests assert that separation, and production instructions explicitly deny those strings operational authority.

Examples in production prompts are deliberately brief for the 4B context budget. They can bias content toward example phrasing, so accepted text needs editorial inspection for repetition or copying. The Visual Agent uses deterministic patterns based on accepted text; it may return a conservative neutral layout when a new topic is not recognized. No actual image is rendered.

The observed run and prompt results are documented separately in the end-to-end report. A single generated week cannot establish stable quality rates; repeated labeled trials and human assessment should precede publication or automation.
