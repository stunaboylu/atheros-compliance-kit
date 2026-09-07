# Pricing
> €0 free tier with no activation and no expiry, €79 per developer per month for teams, from €1,150 per month for enterprise. Seats and entitlement — never metered usage.

:::<p class="eyebrow">Seats, not meters</p>

# What does the AtherosAI Compliance Kit cost?

<p class="lead">Three tiers. The free one needs no activation, no key and no network call, and it does not expire.</p>

:::<div class="tiers">
:::<div class="tier"><h3>Free</h3><p class="who">Evaluating, or running the guardrails in production without a compliance programme yet.</p><div class="price"><span class="amount">€0</span></div><p class="sub">No activation. No expiry. Commercial use allowed.</p><ul><li><code>guard</code> — PII masking and the {{injection_signatures}}-signature injection firewall</li><li><code>euact</code> risk classification, all {{annex_iii_categories}} Annex III categories</li><li>The <strong>complete</strong> hash-chained audit ledger</li><li>English and Turkish</li><li class="no">CI gate</li><li class="no">Annex IV dossier export</li><li class="no">Corpus audit and third-party vendor assessment</li><li class="no">ISO/IEC 42001 evidence pack</li></ul><a class="cta" href="quickstart.html">Start in five minutes</a></div>
:::<div class="tier featured"><span class="flag">Most teams</span><h3>Team</h3><p class="who">An engineering team that has been asked to show its work — usually after the first enterprise questionnaire.</p><div class="price"><span class="amount">€79</span><span class="unit">/ developer / month</span></div><p class="sub">Minimum 5 seats · €790 / developer / year (two months free)</p><ul><li>Everything in Free</li><li><strong>All four modules</strong> — corpus bias and quality, guardrails, classification, third-party vendor risk</li><li>CI gate with GitHub Actions and GitLab templates</li><li>Annex IV dossier export (Markdown, JSON)</li><li><strong>ISO/IEC 42001 evidence pack</strong> — the ledger grouped by clause, with the gaps and the non-coverage stated</li><li>All {{vector_stores}} vector-store connectors</li><li>Custom bias dimensions and custom entity masking</li><li>Email support, two business days</li></ul><a class="cta" href="mailto:sales@atheros.ai?subject=Team%20tier">Talk to us</a></div>
:::<div class="tier"><h3>Enterprise</h3><p class="who">A deal blocked on a security questionnaire, or an estate that has to run inside an air gap.</p><div class="price"><span class="amount">€1,150</span><span class="unit">/ month and up</span></div><p class="sub">Annual, quoted. Typically €13.8k–34k per year.</p><ul><li>Everything in Team</li><li><strong>Security-questionnaire support</strong> — usually the reason this tier is bought</li><li>Air-gap bundle with a CycloneDX SBOM</li><li>PDF dossier export and custom templates</li><li>Your own suppliers maintained in the vendor registry</li><li>Negotiated DPA and contract terms</li><li><strong>30-day regulation-version SLA</strong> with a written impact note</li><li>Named engineer, shared channel, four business hours</li></ul><a class="cta" href="mailto:sales@atheros.ai?subject=Enterprise">Request a quote</a></div>
:::</div>

## Why is usage not metered?

Because our marginal cost to serve you is effectively zero. The library runs in your process, on your compute, against your model key. We host no inference, ingest no reports and store no customer data, so there is no cost-per-run to pass on — and charging for one anyway would be rent, which a technical buyer recognises instantly.

:::<p class="note">It would also punish exactly the behaviour the product exists to encourage: running the gate on every commit. A price that makes you check less often is a price working against the thing you bought.</p>

## Why does the free tier include the whole audit ledger?

It would have been easy to gate tamper-evidence, and it would have been a mistake. The hash-chained ledger is what makes the free tier's output *evidence* rather than a demonstration, and it is the property that makes one engineer show a colleague. Gating it would have removed the reason any of this works.

The free tier requires no activation, so we do not learn that you evaluated the product — there is no mechanism by which we could.

## What is Enterprise actually for?

Not more features. It is for the team whose enterprise deal is stalled behind a ninety-question AI security questionnaire. For them the Kit is deal insurance, and the tier buys the questionnaire response, the negotiated DPA, the air-gap bundle and a named engineer — at a price that is a rounding error against the contract it unblocks.

## What are we charging for, if the source is readable?

The wheel is {{modules}} readable Python files: anyone who installs the package has the source. That is inherent to a pure-Python distribution and it is deliberate, because a compliance tool an auditor cannot inspect is one an auditor cannot accept.

What you are paying for is the work that has to keep happening:

- **Regulation maintenance.** The EU AI Act's implementing acts, harmonised standards and Annex III interpretations will move for years. Every move is a versioned vocabulary update reviewed by someone qualified. A competitor pricing this as pure software will under-invest in it and their answers will rot quietly.
- **The commitment behind the numbers.** The SLA, the support, and the fact that we run the tool on our own product every build and [publish the result](self-assessment.html) including its gaps.

## Questions

`sales@atheros.ai` · The Kit assesses and evidences. It does not certify.
