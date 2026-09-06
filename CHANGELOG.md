# Changelog

All notable changes to the AtherosAI Developer Compliance Kit.

The format follows [Keep a Changelog](https://keepachangelog.com/). This project
adds one section type of its own:

> **Regulation** — a change to the versioned legal vocabulary. These change the
> ANSWERS without changing the code, so they get their own release type and their
> own heading. An assessment produced under one regulation version is not
> comparable to one produced under another, and every report records which it was.

## [Unreleased]

## [1.0.0] — 2026-09-06

First release.

### Added

**Module 1 — `atheros_kit.rag`**
- Vector-store connectors: in-memory, Chroma, pgvector, Pinecone, Milvus. Read-only
  by construction; there is no write path in the module.
- Chunk quality: empty/near-empty, exact and near duplicates, orphans (no vector),
  ragged embedding dimensions, size outliers, personal data in the corpus.
- Semantic drift: centroid shift, per-dimension PSI, volume change, with a
  sample-size-aware noise floor and an isotropy check.
- Bias: seven dimensions, representation (four-fifths rule) and contextual framing,
  composed harmonically into a Fairness Score.
- Remediation recipes, ordered by leverage. Emitted, never executed.

**Module 2 — `atheros_kit.guard`**
- `GuardedClient` wraps a callable, so it works with any provider.
- PII and custom-entity anonymisation with stable placeholders and a reversible
  in-memory vault; checksums (Luhn, IBAN mod-97, TCKN, BSN) to suppress false positives.
- Injection and jailbreak firewall, including encoded payloads, delimiter spoofing,
  and verdict manipulation. Signature-based, so it cannot itself be prompted.
- Token governance with budgets enforced before the call.
- Fallback triggers that are never silent.

**Module 3 — `atheros_kit.euact`**
- Classification against a versioned vocabulary, in statutory order, with grey-zone
  reporting rather than false confidence.
- Annex IV dossier generator that prints gaps as gaps.
- Art. 50 transparency: zero-width marking, verification, C2PA-shaped metadata.
- Parameterised intake tree.

**Module 4 — `atheros_kit.vendor`**
- 24 weighted criteria in 6 groups; `unknown` is penalised, not skipped.
- Data-residency verification with explicit DPF handling.
- Training opt-out enforcement distinguishing available / enabled / contractual.
- Seeded provider registry, dated, with a 180-day staleness rule.

**Cross-cutting**
- SHA-256 hash-chained audit ledger with independent verification in Python and
  in the browser.
- Model-tier abstraction: checks name a tier, the tier names a model, env overrides
  both. Unpinned model names are detected and warned about.
- CI gate with exit codes plus GitHub Actions and GitLab CI templates.
- Full CLI, offline, `NO_COLOR`-aware.
- **English and Turkish throughout** — findings, reasoning, obligations, limits,
  dossier, gate and CLI. Article citations and identifiers are never translated,
  in either language, so a bilingual evidence pack stays cross-referenceable.
- Expo Router console: six screens, static export, in-browser chain verification,
  language and theme toggles.

### Regulation
- Initial vocabulary at `EU-2024/1689:2024-07-12`, following the Official Journal
  numbering (transparency obligations are Art. 50; the proposal-era Art. 52 is
  carried as an alias).

### Fixed during development
These were defects in this codebase before first release. Each is now a named test,
because finding them once is luck.
- `harmonic_mean` filtered out zeros, so the worst possible dimension score was the
  only one with no effect on the composite.
- PSI was compared against fixed bands; at n=200 two identical corpora scored 0.104
  and were reported as drifting on every run.
- Centroid cosine was trusted on isotropic embeddings, where its direction is noise.
- `GuardPolicy.observe()` diverted blocked input, so the "measure, never interfere"
  policy interfered.
- The IBAN pattern could not match a real IBAN, and bare digit runs were logged as
  national identity numbers.
- The near-duplicate pass kept the wrong member of each exact-duplicate group.
- `init` wrote a YAML config the base install then refused to parse.
- Residency reported `non_compliant` for providers that declare SCCs — the finding
  contradicted its own wording, since SCCs are the mechanism for exactly that case.
  Found by running the Kit on the Kit.

### Known limits
- Streaming interception is not supported; `GuardedClient` wraps request/response.
- Bias lexicons are English-first. A non-English corpus under-reports on every
  dimension, and the report says so.
- Detection throughout is structural. A clean result means nothing recognisable was
  found, never that nothing is there.
