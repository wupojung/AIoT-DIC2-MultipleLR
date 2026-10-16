# Architecture

## Implemented foundation
| Area | Responsibility |
| --- | --- |
| python/src | Standard-library environment check only |
| web | Responsive static shell, local tab navigation, disabled dataset selector |
| data | Source/ethics policy; no data |
| outputs | Ignored generated artifacts; tracked placeholder only |
| docs | CRISP-DM gates, glossary and architecture decisions |
| tests | Repeatable foundation integrity and smoke checks |

The Web has no dependency on Python execution and uses no external assets.

## Planned, not implemented
Python will own reproducible preparation, regression and evaluation, beginning
with 50 Startups then transferring the reviewed workflow to Boston Housing.
Web may display verified exports in future. No artifact schema or connection is
implemented. Dynamic custom CSV processing in browser versus Python backend
remains undecided and needs its own ADR. No API, hosting or deployment exists.
See [ADR-0001](adr/ADR-0001-project-foundation.md) and [CRISP-DM](CRISP_DM.md).
