# Local verification evidence

Validated on 2026-10-15 with CPython 3.12.14 on Linux, against implementation
commit `511f597181fbefc867127c423ab95b03c281dd55`. The subsequent documentation/CI
commit adds this report, captured evidence and the workflow; it changes no
application code.

## Automated suite

Command: `python -m unittest discover -s tests -v`

Actual result: **18 tests, 18 passed, 0 failed, 0 errors, 0 skipped** in 0.520s.
The captured runner output is [tests.txt](evidence/tests.txt). Provider timeout
injection is one deliberate mocked boundary test; formatting, word counting,
CLI, concurrency and the two-provider demo exercise real local processes/code.

## Functional proof

The `ear.demo.demonstrate(Register(path), execute=True,
operator='local-validation')` library entry point was run against a new register.
Actual outcome: `verified`; all four checks true (`word_count`, `json_roundtrip`,
`composition`, `disconnect`). Both providers succeeded together. After json.tool
was disconnected, the engine returned `degraded`, WordLens still returned three
words, and json.tool returned a structured `disconnected` error.

- [Machine-readable demo receipt](evidence/demo-receipt.json)
- [Append-only register from that run](evidence/register.jsonl): 15 events,
  successfully replayed with all checksums intact.

Read-only replay: `python -m ear --register docs/evidence/register.jsonl replay`.
Use a new path for your own executions; preserve these captured receipts.

## Packaging and CLI

A fresh virtual environment was created at `/workspace/ear-validation-venv`.
`python -m pip install --no-deps .` successfully built and installed the package
(using isolated setuptools build dependencies). After the last source change,
the package was reinstalled and the installed `ear` executable was run **from
`/tmp`, outside the checkout**, with:

```sh
/workspace/ear-validation-venv/bin/ear --register /tmp/ear-last-installed.jsonl demo --execute --approve --operator installed-validation
```

Result: `verified`, all four checks true, provider version present in receipts.
The custom CLI `add`, `decide`, `run --execute --permission local:compute`, and
`capabilities` paths were also executed successfully. The custom fixture
`{"text":"one two"}` returned `words=2`, `characters=7`, and stopped after one
accepted iteration despite a limit of two.

`git diff --check` passed. `git diff --exit-code origin/main --
FOUNDING_PRINCIPLES.md` passed: the founding document is unchanged.

## Boundaries of this evidence

Only Python 3.12.14 was executed locally. The committed CI workflow targets
3.11/3.12/3.13; its remote outcomes are not yet verified. The repository license
remains unselected; no LICENSE was fabricated. REA external access, integration,
API compatibility, and credentials remain **UNKNOWN**, optional and unused.
No other repository was modified and nothing was deployed.
