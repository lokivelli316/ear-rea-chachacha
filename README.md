# EAR-REA-ChaChaCha

A first working slice of **Extract → Assemble → Rebuild → ChaChaCha**.
EAR is its own application. REA, Generator, and any multi-LLM boardroom remain
independent projects. Read [the founding principles](FOUNDING_PRINCIPLES.md) and
[implementation brief](CODEX_IMPLEMENTATION_BRIEF.md).

This release provides a Python CLI/library, an append-only feature register,
explicit consent decisions, fixed local capability adapters, bounded iteration,
and a runnable **Mosaic Desk** demonstration. It does not investigate arbitrary
applications automatically, install plugins, deploy, or integrate REA.

## Setup and first run

Requires Python 3.11+ on Linux/macOS (the register uses POSIX `flock`). No runtime
third-party dependencies, external service, credentials, or network are needed.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install .
ear --help
# From the checkout, python -m ear also works without installation.
python -m unittest discover -s tests -v
```

The default is a dry run. It records feature discovery and a plan, invokes **no
providers**, and grants no consent. Register appends are local side effects even
in dry run. Use a separate register path for isolated experiments.

```sh
ear --register .ear/demo.jsonl demo
ear --register .ear/demo.jsonl demo --execute --approve --operator "your-name"
ear --register .ear/demo.jsonl replay
ear capabilities
```

Every result is JSON on stdout. Exit codes: `0` successful or dry-run workflow,
`1` refused/cancelled/degraded/failed/limit-reached/empty-queue outcome,
`2` invalid input or register/I/O error. Argument parsing uses argparse's normal
stderr usage and exit code `2`. Receipts include actual provider outputs,
provenance, checksums, errors, limits, and iteration history. `verified` in the
demo means only its four explicit fixture checks passed.

## Two providers, third application

**WordLens** is an original whitespace word counter inspired by GNU `wc -w`'s
publicly documented capability. No GNU source is copied; this is not a full
`wc` clone (locale, bytes, files and line counting are outside its scope).
WordLens remains independently usable:

```sh
printf 'federate do not-fuse' | python -m ear.providers.wordlens
```

**CPython json.tool** is an independent existing application, connected through
`JsonToolAdapter`. The adapter invokes exactly the current Python interpreter
with `-I -m json.tool --sort-keys`, supplying JSON on stdin and collecting stdout.
There is no shell, configurable executable, downloaded code, or dynamic adapter
loading. It has a five-second timeout. `json.tool` remains independently usable:

```sh
printf '{"features":2,"project":"Mosaic Desk"}' | python -I -m json.tool --sort-keys
```

**Mosaic Desk** composes word-count and JSON-formatting outputs into a separate
report. `demo --execute --approve --operator NAME`:

1. Registers both features once, with source/license notes and test plans.
2. Records the operator's approval of these two bundled local capabilities.
3. Invokes each provider alone and saves verification receipts.
4. Invokes both through the engine and checks composition.
5. Disconnects json.tool, invokes both again, and confirms WordLens still works.
6. Appends a run receipt with exact fixture checks and an explicit REA `UNKNOWN`.

Repeated demos reuse stable feature IDs and append new decisions and receipts;
they never overwrite history. A conflicting feature ID is an error. Demo consent
covers these local operations only. Ordinary `run --execute` never grants consent.

Evidence sources:
[GNU wc manual](https://www.gnu.org/software/coreutils/manual/html_node/wc-invocation.html),
[Python json.tool interface](https://docs.python.org/3/library/json.html#command-line-interface).
The demo tests local interoperability with the installed CPython version, not
compatibility with every possible provider version.

## Register and custom queues

Create `feature.json` (metadata is data, never executable code):

```json
{
  "intent": "Count words in local text",
  "source": {"name": "WordLens", "version": "1", "license": "Original sample; repository license not yet selected"},
  "strategy": "rebuild",
  "adapter": "wordlens",
  "evidence": "Original implementation of whitespace splitting; no copied source",
  "test_plan": "Input 'one two' must produce words=2",
  "limitations": "No locale or byte-count compatibility claim"
}
```

Create `input.json` containing `{"text":"one two"}`, then:

```sh
ear add my.words --metadata feature.json
ear run --input input.json --feature my.words            # plan only
ear decide my.words --approve --operator "your-name"
ear run --input input.json --feature my.words --execute --permission local:compute --max-iterations 2
ear decide my.words --refuse --operator "your-name"        # revoke future execution
```

Global `--register PATH` belongs before the subcommand. Custom feature declarations
can select only the two built-in adapter IDs (`wordlens`, `json-tool`). An unknown
adapter produces an unavailable receipt; it cannot install or load anything.
Execution requires **both** the latest positive feature decision and its local
permission (`local:compute` or `local:subprocess`). Provider denial produces an
error receipt, not a fabricated result.

Library use:

```python
from ear.register import Register
from ear.engine import Engine
from ear.adapters import WordLensAdapter

register = Register('.ear/register.jsonl')
# Register.add_feature(...) and Register.decide(...) append feature and consent events.
register.record('evidence', 'my.words', {'observation': 'fixture reviewed', 'uri': 'local:fixture'})
engine = Engine(register, {'wordlens': WordLensAdapter()})
receipt = engine.run({'text': 'one two'}, feature_ids=['my.words'])  # dry run
```

Register events are `feature`, `evidence`, `decision`, `verification`, `iteration`,
and `run`. Each has a sequence, UTC timestamp, previous-event hash, and SHA-256
checksum. Feature IDs are unique and immutable; decisions/evidence append rather
than mutate earlier events. Replay validates the full chain and refuses damaged,
reordered, duplicated, or incomplete lines before any further append. Writes use
an exclusive POSIX file lock and `fsync`. A failed partial write is reported as
corruption; the application never silently truncates or repairs history.

Checksums detect accidental damage; they are **not signatures**, and cannot prove
operator identity or prevent a file owner rewriting the chain or removing its
suffix. Keep independent backups/anchors for adversarial audit requirements.
Receipts contain input-derived outputs; do not feed secrets into this sample.

## ChaChaCha engine and adapter contract

`ear/engine.py` derives an ordered queue from registration order (or explicit
`--feature` selection). Iteration limits must be integers in `1..100`. Dry-run
returns a plan without invoking an adapter. Execution checks current decisions
before each iteration, checks cancellation between calls, records each provider
result, and stops on:

- `accepted`: every selected capability call succeeded;
- `degraded`: some succeeded and some failed, preserving useful outputs;
- `limit_reached`: all failed through the requested bound;
- `cancelled`: cancellation requested, preserving prior receipts;
- `permission_refused` or `empty_queue`: nothing is executed.

`accepted` means successful capability calls, **not** operator acceptance or proof
of an arbitrary user test plan. The demonstration separately checks known output
values. This first planner retries the same deterministic input after a complete
failure; it does not generate code, invent fixes, change a strategy, or broaden
permissions. Callers can inspect receipts and start a new bounded run with revised
input. SIGINT cancels CLI `run` and `demo` at the next boundary; an in-flight
json.tool call is bounded by its timeout. No deployment or cross-project writes
exist. This is a cooperative in-process boundary, not an OS sandbox for untrusted
library adapters.

`CapabilityAdapter` in `ear/adapters.py` specifies descriptor metadata, input/output
schemas, operations, source/version/license provenance, permissions, ownership,
health, disconnect, and structured success/error receipts. Validation for the two
fixed schemas lives in the adapters; this is not a general JSON Schema runtime.
Disconnect is local to the adapter instance and must not stop the other provider.

## Optional REA integration: UNKNOWN

REA is credited to [morluto/rea](https://github.com/morluto/rea). No REA checkout,
API, credentials, invocation, or successful runtime integration was verified.
See [the proposed external integration contract](docs/REA_CONTRACT.md). REA is not
a mandatory dependency and no stub is presented as working interoperability.

## Validation, CI and limits

Run `python -m unittest discover -s tests -v`. Tests cover deterministic provider
outputs, CLI execution, dry run, explicit permission refusal, revocation, replay,
duplicates, corrupted/truncated/reordered history, concurrent appenders,
bounded failure, unavailable/broken/timed-out providers, cancellation and graceful
disconnect. [CI](.github/workflows/tests.yml) installs the package, runs tests,
and executes the demo on Python 3.11, 3.12 and 3.13. CI results must be observed
separately from local results; merely adding the workflow does not establish a pass.
See [recorded local validation](docs/VALIDATION.md).

This is a narrow local slice with no arbitrary source investigation, remote
provider transport, autonomous rebuilding, background daemon, or deployment.
There was no pre-existing LICENSE and no operator-selected project license, so
this change does not invent one. Upstream license notes are recorded as provenance;
contributors/users should resolve project licensing before redistribution.
