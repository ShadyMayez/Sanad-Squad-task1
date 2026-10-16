# Visual specification: thread_1

Status: written specification, not rendered media.
Content type: tech-thread.
Main subject: Reentrancy.
Communication objective: reinforce the accepted takeaway: Using OpenZeppelin ReentrancyGuard prevents protected functions from executing recursively.
Verified claim references: SWC-107.
Technical diagram: Calling contract → external contract → possible call back before the first invocation finishes; show state changes before the external call only when named in the accepted text.
Labels: Calling contract; external contract; call back; first invocation.
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

