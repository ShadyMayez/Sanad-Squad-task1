# SanadSquad V3 Requirements Traceability Matrix & Contract Reconciliation

**Directive:** `SANADSQUAD_V3_ADDITIONAL_REQUIREMENTS_01`  
**Baseline Release:** Evidence-First V2 (`sanadsquad-v2-final-distribution`, commit `45ded43`)  
**Implementation Branch:** `feat/v3-source-separation-marketing-research`  
**Rollback Tag:** `sanadsquad-v3-pre-implementation-baseline`  

---

## 1. Executive Summary

This matrix maps every requirement from the supplied documents:
1. *Multi-Agent Content Pipeline — Additional Requirements* (OCR specification)
2. *Marketing Guide* (`marketing-rules.md` specification)
3. *V3 Task Specification* (Directive `SANADSQUAD_V3_ADDITIONAL_REQUIREMENTS_01`)

It categorizes each requirement by component, implementation level (Code, Configuration, Prompt/Instruction), and test verification strategy.

---

## 2. Explicit Contract Conflict Resolutions

| Conflict ID | Conflicting Requirements | Resolution & Contract Decision |
|---|---|---|
| **CONFLICT-A** | Task contract: `marketing-post` = exactly 1 tweet.<br>Marketing Guide 4.6 describes a 3–7 tweet marketing thread. | **Hard Preservation of Single-Tweet Contract:** `marketing-post` remains strictly 1 tweet ($\le 280$ characters). Format 4.6 (Marketing Thread) is documented as a reserved future content type requiring explicit configuration; it is NEVER automatically emitted under `marketing-post`. Formats 4.1–4.5 are adapted to fit within 280 characters. |
| **CONFLICT-B** | V2 required an actionable review invitation on every marketing post.<br>Marketing Guide: CTAs in $\le 1/3$ of weekly marketing posts. | **New Policy Adopted with Taxonomy Distinction:** Marketing posts are NO LONGER required to have a CTA on every post. Weekly planner caps commercial solicitation CTAs at $\le 1/3$ of marketing posts (max 1 out of 3). Individual posts have at most 1 CTA. Explicit taxonomy separates commercial CTAs from educational security advice. |
| **CONFLICT-C** | Brand voice forbade external links (`allowed_links: []`).<br>Marketing Guide mandates source links for news reaction and learning resources. | **Run-Fetched Authorized Source Links Permitted:** Allow links in posts ONLY if the URL was retrieved and verified during the current run from an allowlisted domain. Arbitrary, promotional, or unretrieved URLs remain strictly banned. |
| **CONFLICT-D** | Docker container `--network none` cannot access web.<br>Marketing Guide requires current web research. | **Explicit Dual-Mode Research Architecture:** Typed `ResearchProvider` interface with `LiveResearchProvider` (requires network & API/HTTP) and `FixtureResearchProvider` (offline deterministic). Fixture runs are explicitly tagged as fixtures in logs; never falsely labeled as live research. |

---

## 3. Comprehensive Requirements Traceability Matrix

### Phase 1 — Source Separation

| Req ID | Requirement Description | Target File(s) | Change Type | Verification Test |
|---|---|---|---|---|
| **REQ-1.1** | Typed source authority contract selecting permitted research pathway by content type | `content_pipeline/source_authority.py`, `content_pipeline/schemas.py` | New Code | `tests/v3/test_source_separation.py` |
| **REQ-1.2** | Tech thread Strategy 1: KB entries cited by ID | `content_pipeline/source_authority.py`, `content_pipeline/graph.py` | Code Update | `test_tech_kb_strategy_accepted` |
| **REQ-1.3** | Tech thread Strategy 2: External technical resource cited by URL with resource brief | `content_pipeline/source_authority.py`, `content_pipeline/agents.py` | New Code | `test_tech_external_resource_strategy` |
| **REQ-1.4** | Marketing Writer barred from `kb.json` and proposition catalog by default | `content_pipeline/source_authority.py`, `content_pipeline/graph.py` | Code Update | `test_marketing_kb_access_blocked` |
| **REQ-1.5** | Marketing vulnerability-class exception: KB entry permitted only as supplemental citation | `content_pipeline/source_authority.py`, `content_pipeline/conformance.py` | Code Update | `test_vulnerability_class_kb_exception` |
| **REQ-1.6** | Fail-closed enforcement: tests prove no KB leakage via state, tools, fallbacks, or exports | `content_pipeline/graph.py`, `content_pipeline/export.py` | Code Update | `test_marketing_state_isolation` |

### Phase 2 — Marketing Research Subsystem

| Req ID | Requirement Description | Target File(s) | Change Type | Verification Test |
|---|---|---|---|---|
| **REQ-2.1** | Canonical `sources.json` covering 4 service lines (`web3-security`, `pentesting`, `agentic-security`, `agentic-payments`) with 5 groups (`blogs`, `docs`, `production`, `analysis`, `figures`) + `_deny` | `sources.json`, `content_pipeline/research/config.py` | Config + Code | `tests/v3/test_sources_config.py` |
| **REQ-2.2** | Verified starter domains: x402, Tempo/MPP, Stripe, Ethereum, Solana, OWASP, etc. | `sources.json` | Config | `test_sources_allowlist_validity` |
| **REQ-2.3** | Research interface: `LiveResearchProvider` & `FixtureResearchProvider` with explicit status | `content_pipeline/research/provider.py` | New Code | `tests/v3/test_research_providers.py` |
| **REQ-2.4** | Scoped search within allowlist; cross-service queries authorized against both lists | `content_pipeline/research/service.py` | New Code | `test_scoped_allowlist_search` |
| **REQ-2.5** | Full research logging: queries (even empty), URLs, status, checksum, timestamps | `content_pipeline/research/logging.py`, `schemas/research_log.schema.json` | Code Update | `test_research_log_completeness` |
| **REQ-2.6** | Fail-closed research behavior: unretrieved URL cannot appear in copy; failed slot isolated | `content_pipeline/research/service.py`, `content_pipeline/graph.py` | Code Update | `test_fail_closed_slot_isolation` |

### Phase 3 — Marketing Guide Policy

| Req ID | Requirement Description | Target File(s) | Change Type | Verification Test |
|---|---|---|---|---|
| **REQ-3.1** | Create `marketing-rules.md` covering positioning, 4 service lines, connective argument | `marketing-rules.md`, `content_pipeline/config.py` | Config + Code | `tests/v3/test_marketing_policy.py` |
| **REQ-3.2** | Supported formats: Short tip, Differentiation, Service overview, News reaction, Learning resource | `content_pipeline/marketing_format.py`, `content_pipeline/validation.py` | New Code | `test_marketing_formats_conformance` |
| **REQ-3.3** | Single-tweet platform limit ($\le 280$ chars) enforced across all marketing formats | `content_pipeline/validation.py`, `content_pipeline/schemas.py` | Code Update | `test_marketing_single_tweet_limit` |
| **REQ-3.4** | Required angles: Web3 post-audit drift, Web2 supply chain, Agentic security, x402 vs MPP | `instructions/marketing-post.md`, `content_pipeline/marketing_planner.py` | Instructions + Code | `test_required_editorial_angles` |
| **REQ-3.5** | Claims prohibitions: client names, unapproved stats, guaranteed security, named competitors | `content_pipeline/marketing_policy.py`, `content_pipeline/validation.py` | New Code | `test_claims_and_confidentiality` |
| **REQ-3.6** | `audits.json` intentionally empty with schema; 20 Accretion findings treated strictly as 3rd-party | `audits.json`, `schemas/audits.schema.json` | Config + Schema | `test_audits_json_empty_and_valid` |

### Phase 4 — Weekly Marketing Planner & Diversity Constraints

| Req ID | Requirement Description | Target File(s) | Change Type | Verification Test |
|---|---|---|---|---|
| **REQ-4.1** | 6-slot plan: 3 tech threads, 3 marketing posts with rich slot metadata | `content_pipeline/planner.py`, `plan.json` | Code Update | `tests/v3/test_weekly_planner.py` |
| **REQ-4.2** | Weekly constraint 1: No service line > 1 without breaking news exception | `content_pipeline/planner.py` | New Code | `test_service_line_diversity` |
| **REQ-4.3** | Weekly constraint 2: At least 1 post with authorized link | `content_pipeline/planner.py`, `content_pipeline/export.py` | Code Update | `test_weekly_link_requirement` |
| **REQ-4.4** | Weekly constraint 3: At least 1 post without link | `content_pipeline/planner.py`, `content_pipeline/export.py` | Code Update | `test_weekly_no_link_requirement` |
| **REQ-4.5** | Weekly constraint 4: Formats must differ, no format > 2 | `content_pipeline/planner.py` | New Code | `test_format_diversity` |
| **REQ-4.6** | Weekly constraint 5 & 6: CTAs in $\le 1/3$ of marketing posts; max 1 CTA per post | `content_pipeline/planner.py`, `content_pipeline/validation.py` | New Code | `test_cta_weekly_cap` |
| **REQ-4.7** | Deduplication: similar topics re-resolved or dropped; parallel safety without race conditions | `content_pipeline/planner.py`, `content_pipeline/graph.py` | New Code | `test_topic_deduplication` |

### Phase 5 — Deterministic Human Writing Quality

| Req ID | Requirement Description | Target File(s) | Change Type | Verification Test |
|---|---|---|---|---|
| **REQ-5.1** | Editable `writing-quality-rules.json` policy file | `writing-quality-rules.json`, `content_pipeline/writing_quality.py` | Config + Code | `tests/v3/test_writing_quality.py` |
| **REQ-5.2** | Banned characters: em dash (`—`), en dash separator (`–`), curly quotes (`“”‘’`), emoji | `content_pipeline/writing_quality.py` | New Code | `test_banned_characters_unicode` |
| **REQ-5.3** | Banned vocabulary: word-boundary matching on 14+ buzzwords without substring false positives | `content_pipeline/writing_quality.py` | New Code | `test_banned_vocabulary_boundaries` |
| **REQ-5.4** | Banned constructions: negative parallelism, copula avoidance ("serves as"), filler openers | `content_pipeline/writing_quality.py` | New Code | `test_banned_constructions` |
| **REQ-5.5** | Repeated rhetorical pattern: Rule of three heuristic with positive & counterexamples | `content_pipeline/writing_quality.py` | New Code | `test_rule_of_three_heuristic` |
| **REQ-5.6** | Hedging density metric with configurable threshold; sentence-length variance logged | `content_pipeline/writing_quality.py` | New Code | `test_hedging_and_variance_metrics` |
| **REQ-5.7** | Execution order: Draft $\to$ Deterministic checks $\to$ Conformance $\to$ Reviewer $\to$ Export | `content_pipeline/graph.py`, `content_pipeline/export.py` | Code Update | `test_validation_pipeline_order` |

### Phase 6 — Security & Trust Boundaries

| Req ID | Requirement Description | Target File(s) | Change Type | Verification Test |
|---|---|---|---|---|
| **REQ-6.1** | Webpage input untrusted: HTTPS only, allowlist verified before fetch and after redirect | `content_pipeline/research/fetcher.py` | New Code | `tests/v3/test_security_boundaries.py` |
| **REQ-6.2** | SSRF protection: block private RFC1918 IPs, loopback, link-local, cloud metadata | `content_pipeline/research/fetcher.py` | New Code | `test_ssrf_and_private_network_block` |
| **REQ-6.3** | Safe fetch controls: response size cap (1MB), timeout (8s), max 3 redirects, sanitization | `content_pipeline/research/fetcher.py` | New Code | `test_fetch_resource_limits` |
| **REQ-6.4** | Prompt injection resilience: adversarial instructions in pages cannot hijack policy or format | `content_pipeline/research/fetcher.py`, `content_pipeline/agents.py` | New Code | `test_prompt_injection_immunity` |
| **REQ-6.5** | Zero credential logging: strip authorization headers and API tokens from logs/artifacts | `content_pipeline/research/logging.py` | New Code | `test_no_credentials_logged` |

### Phase 7 & 8 — Integration, Tests & Qualification

| Req ID | Requirement Description | Target File(s) | Change Type | Verification Test |
|---|---|---|---|---|
| **REQ-7.1** | 100% preservation of all 170 existing tests | `tests/` | Regression | `pytest tests/ audit/tests/` (170/170 pass) |
| **REQ-7.2** | Comprehensive new test suite covering Phases 1–6 | `tests/v3/` | New Tests | `pytest tests/v3/` |
| **REQ-8.1** | Evaluation A: Offline fixture execution (6 slots) | `output/v3-offline-qualification` | Verification | Full 6-slot run check |
| **REQ-8.2** | Evaluation B: Live research qualification or explicit documented blocker | `output/v3-live-qualification` | Verification | Live execution / blocker log |
| **REQ-8.3** | Evaluation C: Adversarial test suite | `tests/v3/test_adversarial.py` | Verification | Hostile inputs rejected |

### Phase 9 & 10 — Docker, Documentation & Final Report

| Req ID | Requirement Description | Target File(s) | Change Type | Verification Test |
|---|---|---|---|---|
| **REQ-9.1** | Update Dockerfile & entrypoint with offline fixture mode & opt-in live search | `Dockerfile`, `docker/entrypoint.sh` | Build Update | Docker build & offline test |
| **REQ-9.2** | Update documentation: README, ARCHITECTURE, ACCEPTANCE_MATRIX, LIMITATIONS | Root markdown files | Documentation | Doc reviews |
| **REQ-10.1** | Consolidated final implementation report | `SANADSQUAD_V3_ADDITIONAL_REQUIREMENTS_IMPLEMENTATION_REPORT.md` | Report | Final delivery sign-off |

### Phase 11 — Commercial Contact Configuration & Marketing CTA Integration (Directive SANADSQUAD_V3_CONTACT_CTA_CLOSURE_01)

| Req ID | Requirement Description | Target File(s) | Change Type | Verification Test |
|---|---|---|---|---|
| **REQ-11.1** | Structured editable `company-contact.json` schema and configuration | `company-contact.json`, `schemas/company-contact.schema.json`, `content_pipeline/contact_config.py` | Config + Code | `test_company_contact_json_loads_and_validates_against_schema` |
| **REQ-11.2** | Zero invented contact information & approval gate (`approved: false` default) | `company-contact.json`, `content_pipeline/contact_config.py`, `content_pipeline/marketing_policy.py` | Code Update | `test_unapproved_contact_info_rejected`, `test_missing_required_contact_fields_rejected` |
| **REQ-11.3** | Contextual marketing CTA generation across 4 service lines without banned unicode punctuation | `content_pipeline/contact_config.py::build_contextual_cta` | New Code | `test_build_contextual_cta_service_lines`, `test_cta_avoids_banned_unicode_characters` |
| **REQ-11.4** | Weekly marketing CTA ceiling ($\le 1$ across 3 posts) & per-post CTA cap | `content_pipeline/marketing_planner.py`, `content_pipeline/export.py` | Code Update | `test_weekly_marketing_plan_enforces_single_cta`, `test_multiple_ctas_in_single_post_rejected` |
| **REQ-11.5** | Technical thread prohibition: zero commercial CTAs or contact details | `content_pipeline/marketing_policy.py`, `content_pipeline/export.py` | Code Update | `test_technical_thread_forbids_ctas_and_contact_details` |
| **REQ-11.6** | Exact email and phone byte-match verification | `content_pipeline/marketing_policy.py::validate_contact_cta` | Code Update | `test_exact_email_and_phone_match_enforced` |
| **REQ-11.7** | Single-tweet platform limit ($\le 280$ chars) post-contact insertion | `content_pipeline/marketing_policy.py`, `content_pipeline/content_planning.py` | Code Update | `test_280_character_limit_with_contact_cta` |
| **REQ-11.9** | Permanent regression test suite & complete 3-post marketing demonstration | `tests/v3/test_contact_cta.py`, `tests/v3/test_v3_e2e.py`, `output/v3_marketing_cta_demo/` | Tests + Deliverable | `pytest tests/v3/test_contact_cta.py`, `test_three_post_marketing_sample_demonstration` |

### Phase 12 — Service Research & Marketing Intelligence Enhancement (Directive SANADSQUAD_V3_MARKETING_RESEARCH_QUALITY_02)

| Req ID | Requirement Description | Target File(s) | Change Type | Verification Test |
|---|---|---|---|---|
| **REQ-12.1** | Canonical Service Research & Positioning Guide for all 4 service lines | `docs/marketing/SERVICE_RESEARCH_AND_POSITIONING.md` | Guide / Doc | `test_service_positioning_all_four_lines_documented` |
| **REQ-12.2** | 7-step Research-to-Marketing planning structure and guidance injection | `instructions/marketing-post.md`, `content_pipeline/content_planning.py` | Prompt + Code | `test_epistemic_separation_valid_marketing_piece` |
| **REQ-12.3** | Epistemic category separation (Fact, Interpretation, Positioning, CTA) | `instructions/marketing-post.md`, `content_pipeline/marketing_policy.py` | Policy + Code | `test_unverified_company_experience_rejected` |
| **REQ-12.4** | Engaging editorial rules & anti-overbranding guidelines | `instructions/marketing-post.md`, `brand-voice.md` | Instruction Update | Writing quality suite |
| **REQ-12.5** | Marketing Guide format taxonomy alignment (5 formats, thread disabled) | `content_pipeline/marketing_format.py`, `ARCHITECTURE.md` | Code Update | `test_corrected_format_taxonomy`, `test_format_link_constraints` |
| **REQ-12.6** | Complete banned vocabulary expansion (14 original + 9 retained = 23+ terms) | `writing-quality-rules.json`, `content_pipeline/writing_quality.py` | Config + Code | `test_complete_banned_vocabulary_all_terms`, `test_banned_vocabulary_word_boundaries_no_false_positives` |
| **REQ-12.7** | Five commercial offering types integrated with approved company contact | `content_pipeline/contact_config.py::build_contextual_cta` | Code Update | `test_five_commercial_offerings_supported`, `test_company_contact_approval_gating` |
| **REQ-12.8** | Rejection of unsupported superiority claims and unverified company experience | `content_pipeline/marketing_policy.py::validate_marketing_claims` | Code Update | `test_unsupported_superiority_claims_rejected`, `test_unverified_company_experience_rejected` |
| **REQ-12.9** | Evaluation of four service line scenarios under full rubric | `SANADSQUAD_V3_MARKETING_INTELLIGENCE_QUALIFICATION.md` | Evaluation Report | All 4 scenario pieces validated ($\le 280$ chars, 0 errors) |
| **REQ-12.10** | Comprehensive regression test suite (15 new tests; 262/262 total passing) | `tests/v3/test_marketing_intelligence.py` | Test Suite | `pytest tests/ audit/tests/` (262 passed in 5.59s) |
| **REQ-12.11** | Final Marketing Intelligence Qualification Report | `SANADSQUAD_V3_MARKETING_INTELLIGENCE_QUALIFICATION.md` | Qualification Doc | Comprehensive qualification document review |


