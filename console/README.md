# AtherosAI Compliance Console

A read-only reader for the reports the [AtherosAI Developer Compliance Kit](../atheros-compliance-kit)
emits. Expo Router universal app — web is the primary target; iOS and Android come from the same
source.

```bash
npm install
npm run web          # http://localhost:8081
```

Point it at a real report:

```bash
EXPO_PUBLIC_REPORT_URL=https://ci.example.com/atheros-report.json npm run web
```

Static export for hosting next to the report itself:

```bash
npm run build:web    # → dist/  (8 pre-rendered routes, content included)
```

## What it is, and what it is not

The Console **renders artefacts**. It holds no connection to your models, your corpus, your
vendors, or your CI, and there is no write path anywhere in the codebase. That is a trust
property, not an unfinished feature: a governance viewer that can reach into a production process
is a new attack surface justified by convenience.

No auth, no server, no database. The artefact's hosting decides who sees it.

## Screens

| Route | Shows |
|---|---|
| `/` | Gate result, per-check status, headline scores |
| `/risk` | EU AI Act tier, grey zone, reasoning, each obligation → the module that evidences it |
| `/rag` | Fairness Score, per-dimension bias, drift, corpus quality, remediation plan |
| `/guard` | Invocations, tokens, masked entity **classes**, signatures triggered |
| `/vendor` | Score by group, residency verdict, opt-out status, all 24 criteria |
| `/ledger` | Ledger entries + independent in-browser hash-chain verification |

## The four rules every screen follows

1. **Never colour alone.** Every state carries a glyph or a word — the screen survives a
   colourblind reader, greyscale print, and a screenshot pasted into a ticket.
2. **Unmeasured is its own state.** `value === null` renders grey, dashed, and labelled
   *unmeasured*. Never a zero. Never a pass. `ScoreBar` enforces this so no screen can get it wrong.
3. **What could not be measured is as prominent as what was.** Unassessable bias dimensions,
   skipped gate checks, and every `limits[]` entry get a banner or a card — not a footnote.
4. **Degradation is visible.** A score computed on the deterministic fallback carries a
   `deterministic · degraded` tag in purple.

## Theming

`theme/tokens.ts` holds both palettes. The **semantic layer is theme-invariant** and identical to
the AtherosAI Platform's, so a screenshot from either product means the same thing — only base
surfaces swap. `system` by default; the header cycles `system → dark → light`.

Enum parity is load-bearing: `semantic.riskTier`, `.action`, `.severity` and `.coverage` map 1:1
onto `atheros_kit`'s Python enums. If one drifts, a colour stops meaning what the report says.

## Ledger verification

`/ledger` recomputes every SHA-256 digest in the browser via WebCrypto, independently of the
Python implementation that wrote them — a verifier sharing code with the writer can only prove
they agree with each other. It hashes the same field set (the event without `hash`/`previous_hash`,
keys sorted) to match `json.dumps(..., sort_keys=True)`.

The screen says plainly what *intact* means: deletion, reordering and editing are detectable. It
does not make the contents true.

## The bundled sample

`data/atheros-report.json` and `data/audit_trail.json` are **real toolkit output**, produced by
running all four modules over a synthetic hiring corpus. They are not hand-written — a demo that
cannot be reproduced by running the product is a promise the product has not made.

Regenerate them:

```bash
cd .. && python scripts/generate_console_fixtures.py
```

## Schema safety

`loadReport()` checks `schema === "atheros.gate/v1"`. On a mismatch it shows the bundled sample
**with a warning** rather than guessing at the mapping — stale fields under current labels is
exactly the lie this Console exists to avoid.

## Development

```bash
npm run typecheck    # strict TS
npm run web
npm run ios | npm run android
```
