# Releasing

The pipeline is built and has been dry-run end to end. What remains is external
configuration that only an account owner can do.

## Before the first release — one-time, on PyPI

The release workflow publishes with **Trusted Publishing** (OIDC), so no API
token is stored anywhere and there is no long-lived credential to leak. That
requires the publisher to be registered on PyPI's side first — and until it is,
a tag push will reach the publish step and fail there.

**Do these in order:**

1. **Reserve the name on TestPyPI and PyPI.** The project does not exist yet on
   either. Create it at
   <https://test.pypi.org/manage/projects/> and <https://pypi.org/manage/projects/>
   as `atheros-compliance-kit`.

   *Or* skip creation and register a **pending publisher** instead (below) —
   PyPI will create the project on the first successful upload.

2. **Add the trusted publisher** on both, under the project's
   *Publishing* settings:

   | Field | Value |
   |---|---|
   | Owner | `stunaboylu` |
   | Repository | `atheros-compliance-kit` |
   | Workflow | `release.yml` |
   | Environment | `testpypi` (on TestPyPI) / `pypi` (on PyPI) |

3. **Create the two GitHub environments** — repo *Settings → Environments*:
   `testpypi` and `pypi`. Put a **required reviewer on `pypi`**. A wheel on PyPI
   cannot be replaced, only yanked, so the last gate before it is permanent
   should be a person.

## Cutting a release

```bash
# 1. The version in pyproject.toml is the source of truth; the workflow asserts
#    the tag matches it and stops if it does not.
grep '^version' atheros-compliance-kit/pyproject.toml

# 2. Everything green locally
cd atheros-compliance-kit && .venv/bin/pytest -q && .venv/bin/ruff check src tests
cd .. && python scripts/self_assessment.py --check   # must be committed, not stale

# 3. Changelog entry, then tag
git tag v1.0.0 && git push origin v1.0.0
```

The tag triggers: **build** (reproducible — two builds of one commit are
byte-identical) → **smoke** (installs the wheel in a clean `python:3.12-slim`
container with no repo and no extras, asserts the core is stdlib-only, and runs
every CLI command offline in both languages) → **TestPyPI** → **PyPI** with a
build-provenance attestation → **SBOM**.

The smoke job runs **before** anything is published, deliberately.

## Dry run, any time

```
Actions → Release → Run workflow → dry_run: true
```

Builds, smokes and produces the SBOM; both publish jobs are skipped. Use this
after touching the workflow — the first dry run caught a real defect that would
only have surfaced during an actual release.

## Regulation-version releases

A change to `euact/vocabulary.py` changes the **answers** without changing the
code. It gets its own section in the changelog under **Regulation**, and the
release notes must state it plainly: an assessment produced under one regulation
version is not comparable to one produced under another.

## Decided: the repository is public before the package is published

It went public on 2026-09-16, as a fresh repository with a rewritten history:
the internal planning documents (`artifacts/`, the GEO audit, the business
sections of the playbook) were removed from every commit first and live outside
the repository. The reason to go public *before* publishing is the `pypi`
environment's required reviewer — GitHub offers that gate on public repositories
without a paid plan, and a wheel on PyPI cannot be replaced, so the last step
before it is permanent should be a person.

**Making the repository public does not expose the source — publishing does.**
The wheel is 40 readable `.py` files: any customer who installs the package has
the complete source, including the comments. That is inherent to a pure-Python
distribution and it is not being worked around:

- Compiling with Cython or Nuitka would produce platform-specific wheels and end
  the "pure Python, zero runtime dependencies, runs anywhere" property that the
  `no-hidden-dependencies` CI gate exists to defend.
- Obfuscating would contradict the product's own argument. A compliance tool an
  auditor cannot inspect is one an auditor cannot accept, and the honesty page
  promises that every number says what it was computed from.

What protects the business is the licence (no redistribution, no sublicensing,
no hosted service), the regulation-vocabulary maintenance that has to keep
happening, and the support and SLA commitments — none of which a reader of the
source acquires.

A public repository under a commercial licence is a normal arrangement, and it
is what the GEO audit asks for: `external_corroboration` currently scores 0, and
engines cite a repository far more readily than a vendor's own marketing page.

**Before any further history-affecting change**, re-run the scan that was run
before going public:

```bash
git log --all --full-history -p | grep -inE \
  "^\+.*(BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9]{32,})"
git log --all --diff-filter=A --name-only --pretty=format: | sort -u \
  | grep -E "\.env$|\.pem$|\.key$|signing_key"
```

A secret that was ever committed stays readable in a public repository even after
it is deleted. As of the scan above the history is clean: no keys, no tokens, no
`.env` files, and the only addresses in the tree are synthetic test fixtures.

Topics on the repository: `eu-ai-act`, `iso-42001`, `ai-governance`,
`llm-guardrails`, `rag-evaluation`.

## Not yet done

- [x] PyPI + TestPyPI trusted publishers registered (2026-09-16)
- [x] `pypi` environment with a required reviewer
- [x] Repository public, under the product's one name
- [x] Tag `v1.0.0` — on PyPI 2026-09-16, approved by hand at the `pypi` gate
- [ ] Legal sign-off on `LICENSE`, the report footer, and the banned-phrase list

### Stage 2 — the paid tiers (deferred until Stripe goes live on atherosai.com)

The service is written and tested (`services/license-api`, CI job
`license-api`). What remains is operational, and none of it is needed for the
free tier, which never touches the service.

- [ ] **Deploy** — Cloud Run + Cloud SQL Postgres, EU region (`europe-west4`),
      `ATHEROS_SIGNING_KEY_PEM` and `ATHEROS_FINGERPRINT_SALT` from Secret
      Manager, never from the image. The Dockerfile is ready; not Firebase
      Functions (long-lived Postgres connection, two uvicorn workers).
- [ ] **Signing key** — `python -m app.keys generate` once, straight into Secret
      Manager. Record where it lives and who else can reach it: it is the only
      private key in the product and today one person holds everything.
- [ ] **One release flips three things together**: the public key hex into
      `core/license.py` `TRUSTED_KEYS`, `ENFORCED = True`, and a changelog entry
      saying so. Until then `atheros-kit doctor` correctly reports enforcement
      off — and every module is open to everyone, which means a Team purchase
      today buys support and SLA, not capabilities.
- [ ] **Issuing keys** — nothing creates a `licences` row yet; the service only
      activates rows that exist. Decide: Stripe webhook on atherosai.com → an
      admin endpoint here (`POST /v1/licences`, admin-token), or hand-issued
      rows for the first design partners (reasonable for five). This must exist
      before the first card payment, or money is taken and no key is sent.
- [ ] Runbook for the three likely incidents: key rotation (README has the
      procedure), a customer over the activation ceiling, database restore.

---

## The site: a path on atherosai.com

The public site (marketing, docs, console demo) is served at
**`https://atherosai.com/compliance-kit/`** by the same Firebase Hosting site as
the rest of atherosai.com — repository `aetheros-trinity-hub`, Firebase project
`atherosaiweb`. Nothing in this repository deploys; that site's build copies
this output into place:

```bash
# in aetheros-trinity-hub
npm run build:firebase      # runs scripts/build-compliance-kit.mjs, which calls
                            # ../…/atherosai-compliance-kit/scripts/build_public.py
                            # --out dist/static/client/compliance-kit
firebase deploy --only hosting
```

Why a path and not a subdomain or a second host: purchase happens on
atherosai.com, the pricing card there links here, and a product page that
inherits the company domain's history is cited sooner than a fresh subdomain.
A path can only be served by the host that serves the domain — so Firebase, not
a second provider.

What the output needs from the host — all in `aetheros-trinity-hub/firebase.json`:

| Setting | Value | Why |
|---|---|---|
| `SITE_URL` | `https://atherosai.com/compliance-kit` (the default in `site/build.py`) | Canonicals, the sitemap, the console's asset and router base, and the robots `Disallow` all derive from it. |
| Headers on `/compliance-kit/**` | CSP `default-src 'self'; connect-src 'self'` (+ Google Fonts), HSTS, nosniff, referrer and permissions policies | `connect-src 'self'` is the privacy page enforced by the browser: the console makes no network calls, and devtools can confirm it. |
| `X-Robots-Tag: noindex, nofollow` on `/compliance-kit/demo/**` only | | The demo is synthetic findings for an invented company; indexed, they read as real. The rest of the site must be indexable — an earlier config put `noindex` on everything. |
| Root `robots.txt` | `Disallow: /compliance-kit/demo/` and `Sitemap: https://atherosai.com/compliance-kit/sitemap.xml` | A robots file is only honoured at the domain root, so the one this build writes is documentation; the effective one is the company site's. |
| Cache | `immutable` on `/compliance-kit/demo/_expo/static/**`; `max-age=0, must-revalidate` on HTML | Content-hashed bundle vs. pages that change on every release. |

URLs carry no `.html` and every internal link is root-absolute under
`/compliance-kit` — both because of the host: `cleanUrls: true` 301s any
request that says `.html`, and `trailingSlash: false` serves the locale home at
`/compliance-kit/en`, where a relative link would resolve one directory too
high. A plain file server cannot preview this. Preview through the host's own
emulator, from the company site's checkout, so what is checked is what ships:

```bash
# in aetheros-trinity-hub
npm run build:firebase && firebase emulators:start --only hosting
# → http://localhost:5000/compliance-kit
```

CI builds the same output on every push and asserts it is servable: every
internal link resolves, every root-absolute reference in the demo sits under
`/compliance-kit/demo/`, the three crawler files exist, and every page carries a
canonical, an x-default hreflang, JSON-LD and Open Graph.
