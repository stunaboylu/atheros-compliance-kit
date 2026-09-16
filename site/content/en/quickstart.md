# Quickstart
> From pip install to a hash-chained compliance report in five minutes, offline.

# Quickstart

No API key. No network. No vector store. Everything below runs on a laptop in a tunnel.

## Install

```
pip install atheros-compliance-kit
atheros-kit doctor
```

`doctor` prints what is installed, which model providers you hold keys for, and therefore which path each check will take. With no keys, everything runs its deterministic path — that is the supported default, not a broken state.

## 1. Classify a system

```
atheros-kit euact classify \
  --name TalentFlow --sector hr \
  --use-case "cv screening" --use-case "candidate ranking"
```

```
HIGH  TalentFlow   confidence 0.85   EU-2024/1689:2024-07-12
    · use case matches Annex III 4. Employment and worker management
    · deployed in a high-risk sector: hr
  articles: Annex III, Art. 6(2)
  basis:    indicator_matched
```

Add `--lang tr` for Turkish. Article citations stay `Art. 6(2)` in both languages, deliberately: a bilingual evidence pack whose citations change spelling cannot be cross-referenced.

## 2. Wrap your LLM client

`GuardedClient` wraps a **callable**, not an SDK — so it works with any provider, and keeps working when that provider changes its client object.

```python
from atheros_kit import GuardedClient, GuardPolicy, CustomEntity

client = GuardedClient(
    call=lambda prompt: openai_client.responses.create(...).output_text,
    policy=GuardPolicy(
        custom_entities=[CustomEntity("CODENAME", literals=["Project Northwind"])],
        static_fallback="We could not complete that request safely.",
    ),
    model_name="gpt-5-2025-08-07",
)

result = client.invoke("Summarise for ali@example.com, IBAN NL91ABNA0417164300")
result.text              # PII masked outbound, restored inbound
result.degraded          # True if anything fell back — never silent
result.masked_entities   # {"EMAIL": 1, "IBAN": 1} — classes and counts, never values
```

Start with `GuardPolicy.observe()`: it measures everything and blocks nothing, so you can see what a strict policy *would* have stopped before it stops it in production.

## 3. Audit a corpus

```python
from atheros_kit.rag import RAGAuditEngine

audit = RAGAuditEngine.from_store("chroma", collection_name="knowledge-base").run()
audit.fairness_score       # 0-100, harmonic across assessed dimensions
audit.quality_score        # duplicates, orphans, sizing, PII, mixed dimensions
audit.bias.unassessable    # ← read this one
print(audit.remediation_markdown())
```

No supported store? Read it yourself. That path is first-class, not a fallback:

```python
from atheros_kit.rag import RAGAuditEngine, Chunk
RAGAuditEngine(chunks=[Chunk(id, text, vector) for ...]).run()
```

The connection is read-only by construction. Remediation produces recipes for a human to run; the Kit never mutates your corpus.

## 4. Assess a vendor

```
atheros-kit vendor assess openai --region EU
```

Pass what your own contract and console actually show, rather than what the vendor's website says:

```python
from atheros_kit.vendor import assess
assess("openai", required_regions=["EU"],
       contract_flags={"training_optout_enabled": True,
                       "training_optout_contractual": True})
```

Available, enabled and contractual are three different facts. An opt-out that exists and is switched off protects nothing, and the report says which of the three you have.

## 5. Fail the build

```
atheros-kit init --ci github     # writes atheros.yml and a working workflow
atheros-kit ci gate              # exit 0 pass · 1 failed · 2 error
```

The workflow comments the summary on the pull request and uploads the evidence — including when the gate went red, which is when it matters.

## 6. Verify the ledger

```
atheros-kit audit verify
```

```
intact  8 entries in .atheros/audit_trail.jsonl
```

Edit one byte of that file and run it again. That is the whole demo.

## 7. Hand the ledger to an auditor

```
atheros-kit iso export --out ./evidence
```

```
wrote evidence/iso-42001-evidence.md, evidence/iso-42001-evidence.json
4 of 5 clauses hold records · 8 ledger entries
```

One document: every record under the ISO/IEC 42001 clause it evidences, the chain verification, the clauses holding **no** records, and the full list of what the Kit does not cover. It writes nothing that was not already in the chain.

The pack is a function of the ledger alone — no generation timestamp — so re-running it on an unchanged ledger produces a byte-identical file. That is how a reader checks it without trusting it. Break the chain first and the command exits 1 with the warning above the evidence, not beneath it.

## Next

- [What this tool does not tell you](honesty.html) — read before acting on any score
- [Modules](modules.html) — the full reference
- [CI gate](ci.html) — thresholds and templates
- [Privacy](privacy.html) — what we do not collect, and how to check
