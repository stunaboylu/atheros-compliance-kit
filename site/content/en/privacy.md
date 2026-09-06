# Privacy
> What the Kit sends, what our services store, and how to check both yourself.

# Privacy

We sell a tool for governing AI systems. The least we can do is be able to answer the questions we ask other people's vendors.

## What the Kit sends: nothing

The library runs in your process. It has no telemetry on by default, no licence heartbeat, and no reporting endpoint. There is nowhere for a report to be uploaded to, because we do not operate one.

The only outbound calls the Kit can make are **your own model calls**, made through `GuardedClient`, on **your key**, to **your provider**. Those are optional: every module has a deterministic path that runs with no key and no network.

You do not have to take this on faith:

```
pip install atheros-compliance-kit
python -c "import sys, atheros_kit.core; print([m for m in sys.modules if 'requests' in m or 'http' in m])"
```

The core imports no third-party module at all. A CI job asserts it on every commit, because a single convenience import in a future pull request would break the promise silently.

## What the free tier requires: no activation

The guardrail wrapper, risk classification and the full audit ledger work with no licence key, no token, and no network call. We do not learn that you evaluated the product, because there is no mechanism by which we could.

## Optional telemetry

Off by default. `ATHEROS_TELEMETRY=1` sends this, once per run, and nothing else:

```json
{"version": "1.0.0", "python": "3.12", "os": "linux",
 "modules_used": ["guard", "euact"], "checks_run": 7,
 "duration_ms": 4210, "degraded": false, "license_tier": "team"}
```

No scores. No findings. No subject names. No provider names. No counts of anything you measured. The schema above is the whole schema, it is asserted by a test, and if it grows the test fails.

## The licence service

Two endpoints: one mints a token, one publishes the public key to check it with.

**It verifies offline.** The token is a 90-day grace signed with Ed25519 and checked against a key compiled into the package. This service being down, slow, unreachable, or gone does not stop your builds. A licence server that can break a build is one that will, at the worst moment, for a customer who is paying us.

**What it stores:** a hash of the licence key, the tier, the seat count, the account, and salted hashes of the machine fingerprints that have activated.

**What it does not store:** hostname, IP address, repository name, project name, or anything about what you assessed. The Kit does not send those and the schema has nowhere to put them. That absence is a design commitment — the cheapest way to be able to answer "you don't hold that" is to have nowhere to hold it.

The fingerprint is computed **on your machine** and salted before storage. The raw machine id never leaves it.

## Reports and the ledger

Reports and the audit chain are files in your repository. You own them, you can delete them, and we cannot read them.

Reports record **entity classes and counts, never values**. A masking log that stores the personal data it detected is the failure the masking exists to prevent — so redaction is enforced when the report is serialised, not left to whoever calls it.

## The console

A static export. It renders a JSON report you point it at. It has no server, no auth, no database, and no write path anywhere in its codebase — the language and theme toggles are the only things it stores, in your own browser.

## Sub-processors

For the licence and telemetry services: a container host and a managed Postgres instance, both in the EU (Amsterdam). Nothing else. We do not operate anything that receives customer report data, so there is no sub-processor that could.

## Contact

`privacy@atheros.ai`
