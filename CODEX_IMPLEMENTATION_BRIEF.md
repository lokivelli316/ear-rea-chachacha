# EAR-REA-ChaChaCha — Codex implementation brief

Read [FOUNDING_PRINCIPLES.md](FOUNDING_PRINCIPLES.md) first. This repository is EAR, not REA, Generator, or a multi-LLM boardroom.

## Mission
Ship a verifiable, minimal working slice of Extract → Assemble → Rebuild → ChaChaCha, without claiming integration that has not been tested.

## Acceptance criteria
1. Runnable Python 3.11+ CLI and importable library; standard library first, optional dependencies justified.
2. Append-only JSONL feature/evidence/decision/verification register; stable feature IDs, timestamps, source attribution, license notes, operator intent and consent, checksums, failures and iteration limits.
3. Feature queue and bounded iteration planner with cancellation, deterministic test fixtures and dry-run default. Never execute downloaded code or arbitrary shell commands.
4. Capability adapter protocol with input/output schema, health/disconnect behavior, provenance, permissions and error receipts.
5. Two distinct local sample providers: one capability independently rebuilt, the other connected through an explicit documented adapter. Assemble them into a third, separately named demo. Show each alone, both together, and graceful degradation after disconnecting one.
6. REA is optional and external; document a safe, explicit integration contract without falsely claiming REA is wired or operational.
7. README with setup, CLI examples, safety boundaries, architecture and limitations. LICENSE only after checking existing files and license choice.
8. Automated tests for all acceptance paths including failure, replay, duplicate handling, permission refusal, disconnect and corrupted register. CI GitHub Actions tests.
9. Emit machine-readable run receipts; include exact test commands and results. No PASS without running tests.
10. Do not edit FOUNDING_PRINCIPLES.md, silently modify other repositories, deploy, or install adapters.

## Working method
Inspect repository and existing branches/artifacts first; reuse valid code rather than replacing it. Implement on this branch in small auditable commits. Document missing external credentials or APIs as UNKNOWN. Request operator approval for external integrations. Prefer a single simple coherent package to premature architecture. Do not invent acceptance results.

## Operator constraints
Federate, don't fuse. Feature is not identity. Rebuild is not connect. Discovery is not permission. Underpromise, overbuild, fix forever. Keep source identity, licensing, evidence and receipts explicit.
