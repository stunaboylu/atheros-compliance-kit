# What this tool does not tell you
> Every score the Kit produces, what it establishes, and what it does not. The page we link from everywhere.

# What this tool does not tell you

Most compliance tooling is optimised to produce a reassuring number. This page exists because that is the failure mode, not the feature — and because a customer who cannot tell the difference between "we measured this and it was fine" and "we could not measure this" has been sold false assurance in a nicer typeface.

Everything below is enforced in code and covered by a test. None of it is a disclaimer appended to output; all of it is *in* the output.

## The contract

**1. A score of `None` is unmeasured. It renders grey, it fails the gate, and it is never a pass.**
A tool that shows an absent measurement as a passing one is a broken instrument. `Score.passed` returns `None` rather than `False`, so a caller writing `if not score.passed` cannot silently treat "we could not check" as "it failed" — or, worse, the reverse.

**2. "No indicator matched" is never "low risk".**
A `minimal` classification carries `evidence_basis: no_indicator_matched` and a limit saying so in full. The lexicon is structural; it recognises what it has been taught and nothing else.

**3. Absence of a detection means nothing recognisable was found.**
An email address has a shape. A person's name does not. Every PII count the Kit reports is a **floor**, never a total, and the report says that where the number appears rather than in a footnote.

**4. Ambiguity produces a grey zone, not a confident answer.**
Two Annex III categories, a sector-versus-use-case conflict, or GPAI plus a high-risk deployment lowers confidence, sets `grey_zone`, and names the conflict. A false confident tier is worse than an honest "a human decides this", because nobody re-examines it.

**5. Machine evidence makes an Annex IV section partial, never covered.**
Annex IV asks for an account of the system. Evidence supports one; it does not write one. A generator that emitted plausible prose for all nine sections would produce a document that looks complete and is not — which survives an internal review and fails an external one, at the point where failing is expensive.

**6. A fallback is never silent.**
Provider error, refusal, blocked output, exhausted budget: every degraded answer carries its trigger, and the score it produced is tagged `deterministic · degraded`. A silent low-quality fallback in a compliance product is worse than an outage, because an outage is visible.

**7. `unknown` on a vendor criterion is penalised, not skipped.**
An unanswered question earns 20% credit — not full credit, and not zero. Scoring only what a vendor volunteered rewards opacity: the supplier who answers nothing would otherwise score the same as the one who answers everything favourably.

**8. The ledger records classes and counts, never values.**
A compliance record that stores the personal data it detected is the failure it exists to prevent. This is enforced in `Report.to_dict()` rather than left to callers, because "the caller should have redacted it" is not a control.

**9. Every report names what it could not establish.**
`limits[]` is rendered as prominently as the findings, in both languages. What was not measured is as important as what was.

**10. The Kit assesses and evidences. It does not certify.**
Not in the product, not in the documentation, not on this website. A lint asserts that no generated artefact and no marketing page contains "certified", "fully compliant", "guaranteed compliant" or "no further action required" — in English or in Turkish. It runs in CI. Good intentions are not a control.

## Where the numbers come from, and where they stop

### Fairness Score
Harmonic mean across the dimensions that could be assessed. Harmonic, so one collapsed dimension is not averaged away by four good ones — a corpus that is fine on geography and catastrophic on gender is not "mostly fair".

**It stops at:** English-first lexicons, structural matching, and surface terms rather than people. `assessed_dimensions` and `unassessable` are separate fields all the way to the console, and a corpus where nothing could be measured scores `None` — not 100. Silence is not fairness.

### Semantic drift
Centroid shift plus per-dimension PSI, with two corrections most implementations skip:

- **PSI has a sample-size noise floor.** At 200 chunks with 10 buckets, two *identical* corpora score a mean PSI of about 0.09 — indistinguishable from the published 0.10 "stable" band. The bands are raised to clear the floor for the actual sample size, and the adjustment is printed in the limits. A drift monitor that fires on unchanged input gets muted, and a muted monitor is worse than none.
- **A near-zero centroid has a meaningless direction.** Where embeddings are close to isotropic, the angle between two centroids is noise: two samples from the *same* distribution score a cosine near zero and read as "shifted". The signal is measured for directionality and excluded when it carries none, and the exclusion is stated.

**It stops at:** geometry. A corpus can drift semantically in ways vectors do not capture, and a `stable` verdict is not a statement about content quality.

### EU AI Act classification
Statutory order — Art. 5 prohibition, then Annex I and Annex III for high risk, then Art. 50, then minimal — against a **versioned** vocabulary. Every classification records `regulation_version`, so two assessments that disagree can be explained.

**It stops at:** being a rule engine reading a description you wrote. It is not a legal opinion, it evaluates none of Art. 5's narrow exemptions, and it does not determine Art. 2 territorial scope.

### Vendor score
24 weighted criteria across six groups. Weights encode what protects a customer, not what is easy to verify: a signed DPA and enforceable SCCs outweigh a status page by an order of magnitude.

**It stops at:** what you told it. Seeded provider facts are dated and go stale after 180 days — the tool flags its own data as stale, in its own reports. They are a prompt for what to verify, not a substitute for verifying.

## The audit chain

Every module appends to a SHA-256 hash-chained JSONL ledger you own. `atheros-kit audit verify` recomputes every digest; the console recomputes them again, independently, in your browser — a verifier that shares code with the writer can only prove they agree with each other.

**What `intact` means:** deletion, reordering and editing are detectable.

**What it does not mean:** that the contents are true. The chain attests to what was recorded, not to whether the assessment behind the record was correct.

## Our own report

We run the Kit on the Kit every release, and the run is a release gate. It reports a `minimal` tier, 33% Annex IV completeness, and one red check we left red rather than raising a threshold until it passed — a threshold tuned until the gate goes green is a threshold that measures nothing.

Doing this found a genuine bug in our residency logic: it reported `non_compliant` for providers that declare Standard Contractual Clauses, when SCCs are precisely the mechanism for countries without an adequacy decision. The finding contradicted its own wording. It is fixed, it has a test, and it is in the changelog under the heading for defects we found in ourselves.
