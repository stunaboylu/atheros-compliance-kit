# PLAYBOOK — AtherosAI Compliance Kit

> The operating manual: how to run the product, what to do first, what to measure, and what will
> go wrong.

## 0. Where everything is

```
projects/atherosai-compliance-kit/
├── BRAND_KIT.md                  design tokens · CLI + report + Console surfaces
├── PLAYBOOK.md                   this file
├── RELEASING.md                  PyPI, the site on atherosai.com, the licence service
├── SELF_ASSESSMENT.md            the Kit's report on the Kit — regenerated in CI
├── atheros-compliance-kit/       THE PRODUCT — Python package — see site/facts.json
│   ├── src/atheros_kit/{core,rag,guard,euact,vendor,cicd}
│   ├── tests/                    pytest — no network, no key, under a second
│   ├── pyproject.toml            extras: rag · llm · pdf · yaml · all · dev
│   └── README.md
├── console/                      Expo Router universal app (web primary)
│   ├── app/                      6 screens + not-found
│   ├── components/ui.tsx  theme/tokens.ts  lib/{types,data,store}
│   └── data/                     bundled sample — REAL toolkit output
├── site/                         landing page + docs, EN + TR, with the copy lint
├── services/license-api/         the one service we operate — verified offline by the Kit
└── scripts/                      self-assessment, console fixtures, the public build
```

## 1. Run it, right now

```bash
cd atheros-compliance-kit
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'
.venv/bin/pytest -q                     # 102 passed
.venv/bin/atheros-kit doctor            # what is installed → what will therefore run

# The whole product in four commands
.venv/bin/atheros-kit init --ci github
.venv/bin/atheros-kit euact classify --name TalentFlow --sector hr --use-case "cv screening"
.venv/bin/atheros-kit rag audit --chunks corpus.json --baseline baseline.json
.venv/bin/atheros-kit vendor assess openai --region EU
.venv/bin/atheros-kit ci gate                    # exit 1 on a breach
.venv/bin/atheros-kit audit verify               # intact / violated
```

```bash
cd console && npm install && npm run web         # http://localhost:8081
npm run build:web                                # → dist/, 8 pre-rendered routes
python ../scripts/generate_console_fixtures.py   # regenerate the sample from the real Kit
```

---

## 2. The five decisions that define this product

Everything else is downstream. Do not relitigate them without new evidence.

1. **It runs in the customer's process.** No ingestion, no upload, no hosted anything. This is the
   one claim a governance SaaS cannot copy, and every roadmap item that erodes it is a competitor's
   product wearing our name.
2. **The core is stdlib-only.** `pip install` in a locked-down CI image must never fail on a driver
   the customer was not going to use.
3. **Unmeasured is never a pass.** A `None` score renders grey, fails the gate, and says so. Every
   competitor's dashboard is all green; that is the opening.
4. **Numbers are deterministic; only prose is LLM-generated.** A metric that changes because a
   model was in a different mood is not evidence.
5. **It does not certify.** Enforced by a CI lint over generated artefacts and marketing copy, not
   by good intentions.

---

## 3. Design rules that were paid for, and are not up for debate

Each of these was learned the hard way — some in earlier in-house tooling, some while building
this — and each is enforced by a test, so that learning it once is enough.

| Rule | Where it lives | Why it is a rule |
|---|---|---|
| The audit chain head is read **from disk, under a lock** | `core/audit.py` | A chain head held in a module global forks the chain the moment a second worker writes. The file is the truth; memory is a cache. |
| Writer and verifier share **one** `_chained_payload` definition | `core/audit.py` | If the two hash different field sets, an intact file and a forged one verify identically — the ledger becomes theatre. One function, imported by both, tested against a tampered file. |
| BLOCK and FLAG are different actions, never collapsed | `guard/injection.py`, `guard/fallback.py` | Collapsing them yields either a nuisance (everything blocks) or a rubber stamp (everything flags). BLOCK vs FLAG *is* the control. |
| Injection signatures cover the black-box wrapper case | `guard/injection.py` | Encoded payloads, delimiter spoofing, tool smuggling — the attacks a third-party LLM boundary sees that an in-house pipeline never did. |
| Assurance overreach is a BLOCK | `guard/fallback.py` | "Fully compliant" from a model, reaching a report, is the failure with legal consequences. In this product it stops the output; a flag would be read as a pass. |
| Checks name a tier; the tier names a model; env overrides both | `core/models.py` | A check that names a model is pinned to a vendor's release calendar. Pinned-vs-floating is detected and warned at load. |
| One shared `find_indicators` matcher for every entry point | `euact/` | Two copies of a matcher drift, and the same system then classifies differently depending on which command was run. One matcher, one vocabulary, one version string in every output. |
| Grey-zone honesty | `euact/classifier.py` | Ambiguity lowers confidence and names the conflict. It never resolves to a confident wrong tier. |
| Four-fifths scoring with harmonic composition | `rag/bias.py` | `score_from_ratio` / `score_from_diff`; the harmonic mean punishes the worst dimension rather than averaging it away. |
| Semantic colours map 1:1 to enums | `BRAND_KIT.md`, `console/theme` | A risk colour is data, not style. Two reports with the same tier look the same in every surface. |

**Deliberately absent:** no database, no tenants, no server; stdlib-only core; dual-theme; every
LLM path degrades to a deterministic one and says so.

**Three defects were found and fixed during construction** — each is now a named test:

| Defect | Symptom | Fix |
|---|---|---|
| Residency ignored declared SCCs | Reported `non_compliant` for providers that declare SCCs — the finding contradicted its own wording, since SCCs are the mechanism *for* non-adequate countries. **Found by running the Kit on the Kit.** | A declared SCC yields `requires_scc` with a transfer-impact-assessment note |
| `harmonic_mean` dropped zeros | A dimension scoring 0 — the worst possible input — was the only one with no effect on the composite | Zero propagates: the harmonic mean of a set containing zero is zero |
| PSI compared against fixed bands | At n=200 two **identical** corpora scored PSI 0.104 and were reported as drifting, every run | Bands raised to clear the sample-size noise floor, and the adjustment is printed in `limits` |
| Centroid cosine on isotropic vectors | Two samples from the same distribution scored cosine ≈ 0 → "shifted" | Directionality is measured; an uninformative centroid is excluded from the verdict and said so |

Each was a metric that was **confidently wrong**, which is the failure mode this product exists to
prevent. They are in the test suite because finding them once is luck.

---

## 4. The honesty contract

Print this. It is the product.

1. A score of `None` is **unmeasured**. It renders grey, it fails the gate, and it is never a pass.
2. "No indicator matched" is **never** "low risk".
3. Absence of a detection means **nothing recognisable was found**, never that nothing is there.
4. Ambiguity produces a **grey zone** with the conflict named — never a confident wrong tier.
5. Machine evidence makes an Annex IV section **partial**, never covered. Evidence supports an
   account; it does not write one.
6. A fallback is **never silent**. Every degraded answer carries its trigger.
7. `unknown` on a vendor criterion is **penalised**, not skipped.
8. The ledger records **classes and counts, never values**.
9. Every report names **what it could not establish**.
10. The Kit **assesses and evidences**. It does not certify, and no asset may imply that it does.

---

## 5. Definition of done for v1.0.0

- [x] Four modules, working, with a deterministic path for each
- [x] Hash-chained ledger with independent verification (Python **and** in-browser)
- [x] CI gate with exit codes + GitHub/GitLab templates
- [x] CLI covering every module, offline, `NO_COLOR`-aware
- [x] Full test suite, no network, no key, under a second (count: site/facts.json)
- [x] Console: 6 screens, static export with real pre-rendered content, strict TS clean
- [x] Bundled sample regenerable from the product itself
- [x] Copy lint enforcing the non-certification rule as a test
- [x] Full English + Turkish across toolkit, reports, dossier, gate, CLI and console
- [x] `SELF_ASSESSMENT.md` committed, and a CI gate that fails if it goes stale
- [x] Release pipeline: reproducible build, clean-container smoke test before PyPI,
      Trusted Publishing, build-provenance attestation, CycloneDX SBOM
- [x] Licence service written; Ed25519 verification is pure-Python, so the core stays
      stdlib-only, and it is checked against the RFC 8032 vectors
- [x] Landing page + docs, both languages, with the copy lint running in CI
- [ ] PyPI project registered and the release workflow actually run
- [ ] Licence service deployed, public key published, `ENFORCED = True`
- [ ] Legal sign-off on report footer + LICENCE + banned-phrase list
- [ ] Five design partners running it in CI
