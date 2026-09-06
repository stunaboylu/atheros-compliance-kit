# Pricing
> Seats and entitlement, not usage. Our marginal cost to serve you is effectively zero, so metering your runs would be rent.

# Pricing

**We do not meter usage.** The library runs in your process, on your compute, against your model key. We host no inference, ingest no reports, and store no customer data, so there is no cost-per-run for us to pass on — and metering it would be rent, which a technical buyer recognises instantly.

It would also punish exactly the behaviour we want: running the gate on every commit.

## Tiers

| | Free | Team | Enterprise |
|---|---|---|---|
| Price | €0 | €79 / developer / month, min 5 seats | from €1,150 / month |
| Annual | — | €790 / developer / year | quoted |
| Modules | `guard` + `euact` classify | all four | all four |
| CI gate | – | yes | yes |
| Annex IV dossier export | – | Markdown, JSON | + PDF, custom template |
| Vector connectors | in-memory | all four | + a supported custom connector |
| Vendor registry | 3 providers | all seeded | + your own suppliers, maintained by us |
| Audit chain | **full** | full | + signed release attestation |
| Support | GitHub issues | 2 business days | 4 business hours, shared channel, named engineer |
| Air-gap bundle + SBOM | – | – | yes |
| Security-questionnaire support | – | – | yes |
| Regulation-version SLA | best effort | within 60 days | within 30 days, with a written impact note |

## Why the free tier includes the whole audit chain

It would be easy to gate tamper-evidence. It would also be a mistake: the chain is what makes the free tier's output *evidence* rather than a toy, and it is the property that makes an engineer show a colleague. Gating it would remove the reason any of this works.

The free tier does not expire, needs no activation, and can be used commercially by any number of people.

## What Enterprise is actually for

Not more features. It is for the customer whose enterprise deal is blocked on a 90-question AI security questionnaire — for them the Kit is deal insurance, and the tier buys the questionnaire response, the negotiated DPA, the air-gap bundle, and a named engineer.

## The cost we do carry

Regulatory maintenance. The EU AI Act's implementing acts, harmonised standards and Annex III interpretations will move for years, and every move is a versioned vocabulary update reviewed by someone qualified. A competitor pricing this as pure software will under-invest in it and their answers will silently rot.

That is why the Enterprise tier carries an explicit regulation-version SLA: the SLA is what makes the maintenance fundable, and a stale legal vocabulary is worse than no tool at all.

## Questions

`sales@atheros.ai`
