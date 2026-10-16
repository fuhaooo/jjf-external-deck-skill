# Changelog

## 1.0.4 — 2026-10-16

- Reorganize the repository and installable-package navigation; remove the stale v1.0.1 package title and obsolete ZIP/local-only status.
- Keep the existing skill discovery path and move detailed project commands into references/local-tools.md; keep project data outside the installed package.
- Make root VERSION and NOTICE the canonical metadata, with byte-preserved copies inside the standalone skill and an explicit synchronization helper.
- Reject mismatched package versions, stale overview titles, rights metadata and verification-report versions before publication.
- Add nine release-metadata regression tests and verify that a clean local installation includes the same version and refuses overwrites.

## 1.0.3 — 2026-10-16

- Add a shared typography contract for repeated page, chapter, website and service labels; preserve intentional cover hierarchy and explicit project references.
- Require normalization after image reconstruction and Canva assembly instead of copying AI-generated font drift.
- Add a standard-library audit of measured role inventories: font families, size, weight, spacing, alignment, normalized geometry, coverage and native-text status. Missing properties remain unknown.
- Document Canva font-family/letter-spacing limitations and preserve native labels when those controls are unavailable.
- Add 18 typography regression tests and a read-only independent scenario review. This does not establish live font-family normalization or full conversion fidelity.

## 1.0.2 — 2026-10-16

- Add three byte-preserved official SVG logos: primary, transparent white and white on black; retain the original PNG fallback and record source hashes.
- Define a consistent header lockup and disclose the difference between native text and outlined wordmarks.
- Add an existing-Canva editing route: scoped changes, ongoing authorization, automatic typo correction, transaction recovery and saved-state/non-target verification.
- Preserve unchanged pages' preview approvals when re-locking one page; conservatively migrate legacy deck-wide approval hashes.
- Carry the official primary SVG through project initialization and conversion handoff, and detect vector-asset tampering.
- Add six core regression/asset tests; correct existing-empty-repository publishing guidance and refresh local verification.

## 1.0.1 — 2026-10-16

Distribution packaging, not a new slide-generation engine.

- Adopt standard `skills/jjf-external-deck/SKILL.md` discovery layout.
- Add Chinese and English repository READMEs with install, usage, dependencies and limitations.
- Preserve official logo bytes, narrative templates, design rules and core scripts.
- Remove the historical Canva share URL/design ID from public provenance prose.
- Add repository privacy and publication guides, explicit-visibility dry-run publisher and checksum checks.
- Add 11 offline publication-safety tests; re-run the 19 core script tests.
- Preserve upstream-conversion and Canva end-to-end status as untested in this release.
- Do not select a new open-source or trademark license on the owner's behalf.

## 1.0.0 — 2026-10-16

Initial local JJF External Deck Skill package: brand assets, production workflow, OPC19 narrative baseline, reference statuses, prompts, templates, version guards and PPTX structural checks.
