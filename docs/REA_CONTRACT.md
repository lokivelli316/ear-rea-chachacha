# Proposed external REA boundary — not implemented or verified

EAR and morluto/rea are independent projects. No claim is made that REA implements
this proposed interface, supports a particular API, or is compatible with EAR.
Status of endpoint, version, authentication, licensing compatibility, and runtime
interoperability: **UNKNOWN**. The local demo does not use REA.

Before implementing a connector:

1. An operator identifies an exact REA release/commit and lawful inspection target,
   checks that release's license/terms, and supplies evidence of its supported API.
2. Record target, intent, source attribution, limits, requested operations, and
   permissions as feature/evidence events. Obtain explicit operator consent for
   the destination, data disclosure and operation before making any external call.
   Discovery and a successful local demo grant no external authority.
3. Use an authenticated, documented transport with TLS verification, an explicit
   destination allowlist, a timeout, bounded payloads/retries and cancellation.
   Secure environment settings hold credentials; never register their values.
4. A request should carry a request ID, source identity/version, capability name,
   JSON input, evidence references and maximum iteration/time limits. A response
   should carry that request ID, provider identity/version, output schema/version,
   observations with provenance, artifact SHA-256 hashes and ownership, limitations,
   and a structured error if unavailable/refused/cancelled/failed.
5. Treat returned content as untrusted data. Do not execute returned code, commands
   or installers. Rebuilding or connecting a new feature requires separate review,
   license checks, consent and verification; a provider cannot certify itself.
6. Prove health, schema/version mismatch, refusal, timeout, cancellation and
   disconnect behavior against the actual provider; save real receipts. EAR must
   continue working locally when REA is absent.

An eventual connector should implement EAR's capability adapter protocol without
changing provider identity or lifecycle. This document is a reviewable contract
proposal, not a fabricated adapter or evidence of external interoperability.
