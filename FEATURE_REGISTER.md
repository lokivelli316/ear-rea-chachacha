# EAR-REA-ChaChaCha — Feature Register

**Append-only.** New entries go at the bottom. Existing entries are never edited or deleted; a correction is a new dated line under the entry it corrects.

Each **Cha** is one pass through the loop (investigate → choose → build or connect → verify). An entry's iteration history lists its Chas in order.

Evidence words, borrowed from the Generator interop contract:

- **PASS**: reproduced mechanically
- **NOT RUN**: not executed yet
- **ENVIRONMENT BLOCKED**: a missing dependency, runtime or source prevented execution
- **PARTIAL**: required behavior only partly reproduced

A test that was not executed is never counted as PASS. No entry certifies itself.

---

## EAR-0001 — Bounded coding lane

| Field | Record |
| --- | --- |
| Feature ID | EAR-0001 |
| Logged | 2026-10-15 |
| Operator intent | A coding helper that plans, edits and tests code inside a sealed workspace, with risky actions held for operator approval. |
| Source and version | Generator v0.4.3.6 (`GENERATOR_v0.4.3.6_SCOPE_LOCK_A1A2_20260920T015514Z.tar.gz`), operator-owned software |
| License / source constraints | Operator's own work; no third-party reversing required |
| Evidence | Read from the v0.4.3.6 package source (not executed): `hands_workspace.py` (contained job folders, preserved originals, diff and restore), `hands_authority.py` (commands classed safe / gated / denied; commit gated, push denied), `agent_stack.py` + `agent_jobs.py` (OpenCode job runner with Ultra, Builder and Auditor seats), `INTEROP_CONTRACT_v1.md` (actors, grants, receipts, evidence vocabulary) |
| Observed mechanism | An operator submits a job; Generator stages sources into a contained workspace, the Builder seat edits, commands pass the safe/gated/denied gate, and the result returns as changed files, a diff against the preserved originals, and receipts. |
| Chosen strategy | **Connect**, not rebuild. Generator stays an independent program; EAR calls it through a documented adapter. |
| Adapter or implementation | Not yet written. Proposed capability ID: `coding.agent.generator-hands` |
| Permissions | Safe commands run inside the job root; gated commands wait for operator confirmation; denied commands are refused. Push is denied. |
| Returns | Changed files, before/after diff, receipts |
| Test plan | 1. EAR sends one small coding job to Generator. 2. Check the diff and the receipt. 3. Stop Generator and confirm EAR fails cleanly (graceful degradation). |
| Test results | NOT RUN |
| Known limitations | In the v0.4.3.6 seat bindings, the Ultra and Auditor seats both use `nvidia/nemotron-3-ultra-550b-a55b:free`. Generator's own OpenCode config builder requires three distinct models to prevent an echo chamber. The Auditor seat should get a different model before this capability is qualified. |
| Operator approval | Logging approved by operator 2026-10-15. Integration not yet approved. |
| Artifact hashes | Generator package SHA-256: `0f19d41beea01253b68f9fb24bd0cedb43d4cbca277d27e3bf702c4f47234dec` |

**Iteration history**

- Cha 1 (2026-10-15): Investigated from package source. Strategy chosen: connect. Adapter not written. Tests NOT RUN.
