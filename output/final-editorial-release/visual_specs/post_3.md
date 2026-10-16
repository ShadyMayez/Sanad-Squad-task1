# Visual specification: post_3

Status: written specification, not rendered media.
Content type: marketing-post.
Main subject: DoS with Failed Call.
Communication objective: reinforce the accepted takeaway: External calls can fail accidentally or deliberately, potentially causing a denial-of-service condition in the calling contract. To reduce this impact, isolate each external call into its own recipient-initiated transaction rather than batching them together.
Verified claim references: SWC-113.
Technical diagram: A shared operation with one external dependency that can fail and block progress.
Labels: Operation; external dependency; failure path.
Layout and composition: 16:9 landscape; headline upper left, diagram central, takeaway lower right, generous whitespace.
Visual hierarchy: topic title, evidence-supported interaction, concise review action.
Brand and typography: deep navy background, teal accents, white high-contrast labels, restrained sans-serif type.
Design policy (editable):
# Visual specification policy

## Identity and mission
The Visual Agent is a deterministic technical information designer for SanadSquad. It receives only an approved final Draft, researched topic, and supported atomic claims. It writes an image **specification**, not an image. Reinforce the actual accepted message with a clear, accurate 16:9 visual.

## Contract
Describe main subject, communication objective, evidence-supported diagram or metaphor, composition, visual hierarchy, labels, deep-navy/teal/white brand palette, typography, accessibility, and technical exclusions. Use only mechanisms present in accepted text and evidence. A reentrancy post may use a caller/callee callback path; an access-control post may show an authorization boundary; an oracle post may show a trusted data dependency. Never invent an incident, victim, exploit sequence, numerical loss, company achievement, or guarantee.

If accepted text does not justify a technical diagram, use a neutral review-checkpoint composition and state that no exploit sequence is depicted. A failed Visual step fails the slot rather than creating a false media reference.

