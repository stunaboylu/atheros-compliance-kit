# Modules
> The four modules, what each measures, and where each one stops.

# Modules

Four modules over one core. Use one or all four. `core` imports nothing from them, and they import nothing from each other except a shared finding vocabulary — which is what lets you install one module's extras and not the rest.

## M1 · `atheros_kit.rag` — corpus quality and bias

Measures the **corpus**, not the model. That is the gap: teams evaluate answers and never look at the knowledge base those answers are drawn from, and in a RAG system bias enters through the corpus far more often than through the weights.

| Capability | Output |
|---|---|
| Connectors | in-memory, Chroma, pgvector, Pinecone, Milvus — read-only by construction |
| Chunk quality | empty, near-empty, exact and near duplicates, orphans, ragged dimensions, size outliers, PII |
| Semantic drift | centroid shift, per-dimension PSI, volume change — with a sample-size noise floor and an isotropy check |
| Bias | seven dimensions, representation (four-fifths rule) and contextual framing → Fairness Score |
| Remediation | ordered recipes, emitted and never executed |

**Where it stops:** lexicons are English-first and structural. `assessed_dimensions` and `unassessable` are separate fields, and a corpus nothing could be measured on scores `None`, not 100.

## M2 · `atheros_kit.guard` — third-party API guardrails

The isolation layer between your application and an external model. Provider-agnostic: it wraps a callable, because every provider has a different client object and they all change, but `str -> str` does not.

| Capability | Detail |
|---|---|
| PII and custom entities | Stable placeholders (`⟦EMAIL_1⟧`) so the model can still tell two people apart. Reversible in-memory vault, or `reversible=False` for unrecoverable-by-construction. |
| Checksums | Luhn, IBAN mod-97, TCKN, BSN — so an order number is not logged as a national identity number |
| Injection firewall | Instruction override, prompt exfiltration, jailbreak personas, verdict manipulation, delimiter spoofing, tool smuggling, and **encoded payloads** that are decoded and re-scanned |
| Token governance | Budgets enforced *before* the call — a budget checked afterwards is a report, not a control |
| Fallback | Retry → secondary → static, every step recorded, never silent |

Three presets: `observe()` measures and blocks nothing; `standard()` masks and blocks the critical signatures; `strict()` drops the vault entirely and raises on anything suspicious.

**Where it stops:** the firewall is signature-based on purpose — a classifier that can be prompted is not a control. An LLM judge is available as a second opinion and never as the only one. Streaming interception is not supported in v1.

## M3 · `atheros_kit.euact` — classification and Annex IV

| Capability | Detail |
|---|---|
| Classification | Statutory order: Art. 5 → Annex I / Annex III → Art. 50 → minimal, against a versioned vocabulary |
| Grey zone | Multiple Annex III matches, sector conflicts, or GPAI plus high-risk lower confidence and name the conflict |
| Obligations | Each duty carries the module that produces its evidence — the spine that makes four modules one product |
| Dossier | Annex IV sections 1–9, each `covered` / `partial` / `missing`, gaps printed as gaps |
| Transparency | Art. 50 zero-width marking, verification, C2PA-shaped metadata |

**Where it stops:** it is a rule engine reading a description you wrote. It evaluates none of Art. 5's narrow exemptions and does not determine Art. 2 territorial scope.

## M4 · `atheros_kit.vendor` — third-party and vendor risk

| Capability | Detail |
|---|---|
| 24 criteria | Certifications, data protection, retention and training, security, AI transparency, operations — weighted |
| `unknown` | Penalised at 20% credit, not skipped. A vendor cannot score well by declining to answer. |
| Residency | Adequacy, SCCs, BCRs; the EU–US framework requires the *recipient's* certification, checked explicitly |
| Opt-out | Available ≠ enabled ≠ contractual — three facts, reported separately |
| Registry | Seeded provider facts, dated, stale after 180 days and flagged as such by the tool itself |

**Where it stops:** the seed registry is public documentation, which describes what a vendor offers — not what is configured on your account or written into your contract. Pass your own answers via `overrides=`.

## `atheros_kit.cicd` — the gate

Compares what you measured to configured thresholds, writes `atheros-report.json` and a Markdown summary, and sets the exit code. Templates ship for GitHub Actions and GitLab CI.

Two rules: **an unmeasured check never passes**, and **every skipped check is printed**. Silent partial coverage reads as full coverage.

## `atheros_kit.iso` — the ISO/IEC 42001 evidence pack

```
atheros-kit iso export --out ./evidence
```

Collects the hash-chained ledger into one document an auditor can read: the records grouped under the clause each one evidences, the chain verification, the clauses that hold **no** records, and the full list of what the Kit does not cover. It generates nothing — every row traces back to a ledger line by its digest.

Three properties make it usable as evidence rather than as marketing. It is a **pure function of the ledger**: no generation timestamp, no run id, so an auditor who doubts the document re-runs the command and diffs it. A **broken chain is reported above the evidence**, not beneath it, and the command exits 1 — there is no flag to silence that, because a flag to suppress the warning becomes the way the warning is suppressed. And an **empty ledger is not a successful export**: a command that exits green while producing a pack with no evidence has failed the operator at the moment it mattered.

Clause 6.1.2 is labelled *input only* wherever it appears. An EU AI Act classification is a regulatory categorisation; the clause asks for your own risk criteria, analysis and evaluation. See [what this tool does not tell you](honesty.html).

## `atheros_kit.core` — the foundations

Stdlib-only. Hash-chained audit ledger, layered config, the model-tier abstraction, the shared finding vocabulary, and report rendering in English and Turkish with redaction enforced at serialisation rather than left to callers.
