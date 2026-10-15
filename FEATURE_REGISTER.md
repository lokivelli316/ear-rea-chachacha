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

---

## Sister Stack queue: EAR-0002 to EAR-0006

**Target project:** Sister Stack Android app (`lokivelli316/apksister-`, commit `0d711a1`, M1 foundation). Per its delivery report, the M1 app has the launcher, SOLO ALYRA / SOLO ELVIRA / DUAL, separate sister notes, worker slots and on-phone API key storage. Not yet built: chat with the sisters, the floating overlay, the VRM, voice.

**Logged:** 2026-10-15. Operator approved logging the queue ("Anything that helps is what I want").

**About the intent lines:** each one is drawn from goals the operator has stated in earlier sessions, not written in his own words for this register. Each is marked **INTENT: OPERATOR TO CONFIRM** until he rewrites or confirms it. A builder must not treat an unconfirmed intent line as final.

**Governance carried from the target app:** Alyra L1–L4 and Elvira L1–L3 remain frozen. No shared sister identity. Workers are not sovereign agents. Nothing self-certifies. Each piece is built and checked one at a time.

**Order:** chat first, because every later piece needs her able to answer in order to be tested.

### EAR-0002 — Chat: the sisters can talk

| Field | Record |
| --- | --- |
| Operator intent | Alyra and Elvira hold real conversations in the app, online, using the API keys already saved on the phone; each sister stays herself, with her own notes and no shared identity. **INTENT: OPERATOR TO CONFIRM** |
| Source | Operator's own multi-provider chat work (Generator, ShoggothBot) |
| License / source constraints | Operator-owned; no third-party reversing required |
| Chosen strategy | **Reuse** the operator's own provider-calling approach, rebuilt natively for Android |
| Depends on | M1 API key vault (`ApiKeyVault.kt`, `Providers.kt`) |
| Known open items | Qwen, Kimi and DeepSeek endpoints are still `TODO_VERIFY` in `Providers.kt` |
| Test plan | One message to Alyra, one to Elvira, DUAL shows both separately; airplane mode gives a clear "can't reach the provider" message, not a crash; no key ever appears in receipts |
| Test results | NOT RUN |

### EAR-0003 — Floating overlay: she sits on top of other apps

| Field | Record |
| --- | --- |
| Operator intent | Alyra floats over the phone screen while the operator talks to the AIs in other apps. **INTENT: OPERATOR TO CONFIRM** |
| Source | Open-source Android apps with floating chat bubbles (specific app to be chosen and logged at Cha 1) |
| License / source constraints | Pick an open-source source app; record its license before investigating |
| Chosen strategy | **REA it, rebuild**: learn how floating windows are created, moved and kept alive, then write an original version |
| Depends on | EAR-0002 (something to show in the bubble) |
| Test plan | Bubble stays over two other apps; can be dragged and dismissed; survives the screen turning off and on; the app asks for the "display over other apps" permission plainly |
| Test results | NOT RUN |

### EAR-0004 — Her VRM body

| Field | Record |
| --- | --- |
| Operator intent | Alyra appears as her own VRM model in the floating window, at her character rest: a subtle canonical smirk, fangs may show. **INTENT: OPERATOR TO CONFIRM** |
| Source | three-vrm by pixiv (open-source VRM viewer, MIT license) |
| License / source constraints | MIT: reuse allowed with the license notice kept |
| Chosen strategy | **Reuse** the viewer inside the app; the model and her look stay the operator's own |
| Depends on | EAR-0003 |
| Test plan | Model loads and shows inside the bubble; idle pose matches the character rest; memory use and battery drain recorded over 10 minutes |
| Test results | NOT RUN |

### EAR-0005 — Voice and lip sync

| Field | Record |
| --- | --- |
| Operator intent | Alyra speaks her replies and her mouth keeps up with her voice. Lip shapes are measured from the separate viseme rest (neutral mouth, no smirk), not from the character rest. **INTENT: OPERATOR TO CONFIRM** |
| Source | Open-source VRM and VTuber tools, plus the operator's own viseme work |
| License / source constraints | Record each source's license at Cha 1 |
| Chosen strategy | **REA it, rebuild** to the operator's two-rest rule |
| Depends on | EAR-0002, EAR-0004 |
| Test plan | Mouth starts and stops with the audio; returns to the viewer's rest after speaking; no smirk leaks into viseme measurement |
| Test results | NOT RUN |

### EAR-0006 — Seeing the screen

| Field | Record |
| --- | --- |
| Operator intent | Alyra can see what is on the operator's screen and react to it. **INTENT: OPERATOR TO CONFIRM** |
| Source | Android's documented screen-capture feature (MediaProjection) |
| License / source constraints | Platform API; follow Android's consent rules |
| Chosen strategy | **Build from the docs**; no reversing needed |
| Depends on | EAR-0002, EAR-0003 |
| Test plan | Android's own consent prompt appears every session; capture stops when the operator says stop; a captured screen is sent only when the operator asks her to look |
| Test results | NOT RUN |
| Note | What she may keep from what she sees, and for how long, is an operator decision. Not decided here. |

**Iteration history (all five)**

- Cha 0 (2026-10-15): Queued. Sources and strategies proposed. No investigation, build or test yet.

---

## 2026-10-15 — EAR-0002 intent confirmed by operator (correction line)

The EAR-0002 intent above was drafted, not the operator's words. The operator supplied his own intent on 2026-10-15. **This line supersedes the drafted one; the drafted line stays above for lineage.**

Operator's words, verbatim:

> "The chat should work with the connected api's with the brains that's connected and like the documents here say. It has import and export buttons for other files so which sister that's launched is capable of reading the file and capabilities to send a document or other file back when they are done with it. When one sister is launched I'm talking to her when both are launched I have the ability to talk to both or just 1. With proper buttons and customizable font due to the eye problems I have. Prefer to be able to have a voice to text as well as a typed in text box as well."

"The documents here" = `SISTER_STACK_COMPLETION_PLAN_v1.2` (counter-seat doctrine, 13 Oct 2026) and `Sister_Stack_Master_v2_0_Lower_Faculty_Architecture_2026-10-07`, both supplied by the operator in this session.

Requirements read from those words, for checking the build against:

| # | Requirement |
| --- | --- |
| R1 | Chat runs on the operator's connected APIs, through each sister's connected brains |
| R2 | Follows the v2.0 boundaries: separate selves, no merged conversation, upper brains frozen, receiving is not remembering |
| R3 | IMPORT button: the launched sister can read the file |
| R4 | EXPORT: the sister's finished document or file can be saved back out |
| R5 | Solo launch: the operator talks to that sister |
| R6 | Dual launch: the operator can talk to both, or to just one |
| R7 | Proper (large, clear) buttons |
| R8 | Customizable font, for the operator's eyes |
| R9 | Voice-to-text and a typed text box, both |

INTENT: **CONFIRMED BY OPERATOR** for EAR-0002.
