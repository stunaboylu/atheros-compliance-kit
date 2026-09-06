# AtherosAI licence service

One endpoint that mints a token, one that publishes the key to check it with.
That is the entire service, and keeping it that small is the point: it is the
only thing AtherosAI operates that a customer's build could, in principle,
depend on — so it is built so that it cannot be depended on.

```
POST /v1/activate   {licence_key, machine_fingerprint}  → a 90-day EdDSA token
GET  /v1/jwks                                           → the public keys
GET  /health · /health/ready
```

## The design decision that matters

**The Kit verifies offline.** The token it receives is a 90-day grace signed with
Ed25519 and checked against a public key compiled into the package. This service
being down, slow, unreachable, or gone does not stop a customer's CI. A licence
server that can break a build is a licence server that will, at the worst
possible moment, for a customer who is paying us.

Consequences, all deliberate:

- **No heartbeat.** The Kit never calls back to confirm a token is still valid.
- **No usage metering.** There is nothing here that counts a customer's runs.
- **The free tier never touches this service.** `guard`, `euact.classify` and the
  audit ledger need no activation at all, so an evaluating engineer never meets a
  licence check and we never learn they evaluated.

## What is stored

One row per licence: the key hash, the tier, the seat count, the account, and the
salted fingerprints that have activated. That is all.

**Not stored:** hostname, IP, repository name, project name, or anything about
what the customer assessed. The Kit does not send those and this service has
nowhere to put them. A vendor of AI-governance tooling that quietly builds a
picture of its customers' AI estates would deserve every question it got.

## Key rotation

A new signing key is generated, published in `/v1/jwks` alongside the current
one, and added to `TRUSTED_KEYS` in the Kit in the next release. The old key is
removed a release later. Both are trusted during the overlap, so a customer
running a version from either side keeps working — a rotation that invalidates
live tokens is an outage the customer did not schedule.

## Run

```bash
pip install -r requirements.txt
python -m app.keys generate > signing_key.pem      # once, then store it properly
export ATHEROS_SIGNING_KEY_PEM="$(cat signing_key.pem)"
export DATABASE_URL=postgresql+asyncpg://...
uvicorn app.main:app --reload
```

The private key belongs in a KMS or a secret manager, never in the image and
never in the repository. `app/keys.py` reads it from the environment so that
substituting a KMS-backed signer is one function, not a rewrite.
