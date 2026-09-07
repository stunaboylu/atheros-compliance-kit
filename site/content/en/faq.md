# Frequently asked questions
> Does data leave the process, is this a certification, what does unmeasured mean, which module evidences which article, and what does it cost.

# Frequently asked questions

### Does my data leave my process when I use this?

No. {{modules}} of the {{modules}} modules run as a library inside your own process, on your own
compute. There is no ingestion endpoint, no telemetry on by default, and no licence heartbeat —
the licence token is verified offline for 90 days against a key compiled into the package. The
only outbound calls the toolkit can make are your own model calls, through `GuardedClient`, on
your key, to your provider — and those are optional, because every module has a deterministic
path that runs with no key and no network. The core imports {{runtime_dependencies}} third-party
packages, and a CI job asserts it on every commit.

### Is this a certification, or does it make us compliant?

Neither. The AtherosAI Compliance Kit produces **assessments and evidence** — it assesses and
evidences, and it does not certify. It is not a conformity assessment within the meaning of
Regulation (EU) 2024/1689, and it is not legal advice.
Regulatory obligations rest with you and no output of this toolkit transfers them. A lint over
every generated report and every marketing page — in English and Turkish — fails the build if the
words "certified", "fully compliant", "guaranteed compliant" or "no further action required"
appear anywhere.

### What does "unmeasured" mean, and why does it fail my build?

A score of `unmeasured` means the measurement did not run or could not be computed — not that it
passed. It renders grey, never green, and it fails the CI gate. Treating it as a pass would mean
the gate goes green at exactly the moment it should not: when the measurement itself broke. This
is the single design decision the product rests on, and it is enforced in code rather than
documented as an intention.

### Which module evidences which EU AI Act article?

Each obligation names the module that produces its evidence.

| Article | Duty | Evidenced by |
|---|---|---|
| Art. 9 | Risk-management system | `euact.dossier` |
| Art. 10 | Data governance and bias examination | `rag.bias` + `rag.quality` |
| Art. 11 + Annex IV | Technical documentation | `euact.dossier` |
| Art. 12 | Automatic event logging | `core.audit` + `guard.ledger` |
| Art. 13 | Transparency and instructions for use | `euact.dossier` |
| Art. 14 | Human oversight | `guard.fallback` |
| Art. 15 | Accuracy, robustness, cybersecurity | `guard.injection` |
| Art. 17 | Quality-management system | `cicd.gate` |
| Art. 26 | Deployer duties | `guard.ledger` |
| Art. 50 | Transparency for generative systems | `euact.transparency` |
| ISO/IEC 42001 §9.1 | Monitoring records | `core.audit` |

### Which ISO/IEC 42001 clauses does this cover?

Four, and the toolkit is explicit about which. It produces **evidence toward** specific clauses — it does not automate an internal audit of the standard, and nothing here should be read as covering it end to end.

| Clause | What it asks for | Produced by |
|---|---|---|
| 8.3 Operational controls | Controls over the AI system in operation | `guard` — injection gate, masking, fallback |
| 8.4 Data for AI systems | Data used by the system is examined | `rag` — corpus quality and bias |
| 8.5 Third-party relationships | Suppliers are assessed | `vendor` — third-party due diligence |
| 9.1 Monitoring and measurement | Records of monitoring | `core.audit` — the hash-chained ledger |

**Not covered:** clauses 4–7 (context, leadership, planning, support) and 10 (improvement), the clause 9.2 internal audit programme, the clause 9.3 management review, the Statement of Applicability, and the 38 Annex A controls. Those are management-system work that a tool inside your CI cannot do for you, and a report that implied otherwise would be the failure this product exists to prevent.

### Does it work without an API key or a network connection?

Yes, and that is the supported default rather than a degraded mode. Every module has a
deterministic path. `atheros-kit doctor` prints which providers you hold keys for and therefore
which path each check will take. Where a model was configured and did not answer, the score is
tagged `degraded` and the report says so — a fallback is never silent.

### Is this a library or a governance platform?

A library and a CLI, plus a read-only console that renders the reports the library emitted. It
runs where your data is. A hosted platform structurally cannot make that claim, which is why the
console has no server, no database and no write path, and why there is no SaaS version planned.

### What does it cost, and how is it metered?

It is not metered. The toolkit runs on your compute against your model key, so there is no
cost-per-run to pass on — and metering it would punish the behaviour the product wants, which is
running the gate on every commit.

| Tier | Price | Includes |
|---|---|---|
| Free | €0, no activation, no expiry | Guardrails, risk classification, the full audit ledger |
| Team | €79 per developer per month, minimum 5 seats | All four modules, CI gate, dossier export |
| Enterprise | from €1,150 per month | Air-gap bundle, SBOM, security-questionnaire support, 30-day regulation-version SLA |

### Which vector stores are supported?

{{vector_stores}} connectors ship: Chroma, pgvector, Pinecone and Milvus. For anything else, read
the corpus yourself and pass the chunks in — that path is first-class rather than a fallback, and
it is why the assessment code never touches a driver. Every connection is read-only by
construction; remediation emits recipes for a human to run and never mutates your corpus.

### How can an auditor verify the audit chain independently?

Two independent implementations. `atheros-kit audit verify` recomputes every SHA-256 digest in
Python; the console recomputes the whole chain again in the browser using WebCrypto, sharing no
code with the writer — a verifier that shares code with the writer can only prove they agree with
each other. An intact chain makes deletion, reordering and editing detectable. It does not make
the contents true: the chain attests to what was recorded, not to whether the assessment behind
the record was correct.

### Does the free tier expire?

No. It requires no activation, no key and no network call, it may be used commercially by any
number of people, and it does not expire. It covers the guardrail wrapper, EU AI Act risk
classification and the complete hash-chained audit ledger. Gating the ledger would have been easy
and would have removed the reason the free tier is evidence rather than a toy.

### How do I know whether my system is high-risk under the EU AI Act?

Run `atheros-kit euact classify` with your sector and use cases. The engine evaluates in statutory
order — Art. 5 prohibitions first, then Annex I product safety and the
{{annex_iii_categories}} Annex III categories, then Art. 50 transparency, then minimal — against a
versioned vocabulary ({{regulation_version}}), and every classification records the version it ran
under. Where the inputs support more than one answer it reports a **grey zone** with the conflict
named rather than a confident tier, and a `minimal` verdict states that it rests on no indicator
matching, which is not the same as evidence of low risk.

### How much of an Annex IV file can be generated automatically?

Part of it, and the report tells you which part. The generator produces all
{{annex_iv_sections}} sections and marks each `covered`, `partial` or `missing`. Machine evidence
makes a section **partial**, never covered: Annex IV asks for an account of the system, which
evidence supports and does not replace. Our own self-assessment publishes a 33% completeness score
for our own product, incomplete, because a generator that emitted plausible prose for all nine
sections would produce a document that looks finished and is not — one that survives an internal
review and fails an external one.
