# ADR-0001 — Project foundation

- Status: Proposed
- Date: 2026-10-16
- Decision owner: Teacher / repository owner (wupojung)
- Related issue: https://github.com/wupojung/AIoT-DIC2-MultipleLR/issues/1

## Context
DIC-2 needs a small, reproducible starting point for two CRISP-DM exercises.
Issue #1 limits work to foundation and preserves the existing README contract.

## Decision
Propose separate Python analysis and a static HTML/CSS/JS Web presentation shell.
Use Python 3.11+ and standard library only for the initial smoke check. Add ML
dependencies when justified. Keep architecture, bilingual glossary and six phase
gates in docs; record consequential decisions in numbered ADRs.
Codex reads contracts, uses feature branches, follows BUILD → RUN → TEST → VERIFY
→ PASS and submits reviewable PRs. Human acceptance is required; no auto-merge.

## Alternatives
A React application or backend introduces dependencies without a foundation need.
A notebook-only repository would omit the requested Web shell and explicit boundaries.
Copying the prior project would import unverified assumptions and exceeds scope.

## Consequences
The foundation is easy to run offline and inspect but has no analysis or data
connection. Python/Web integration and artifact schemas need later work.
Browser versus backend custom CSV execution remains undecided; evaluate capability,
privacy, maintenance and deployment constraints in a future ADR. This proposal
does not authorize hosting or settle that decision.

## Supersession
None.
