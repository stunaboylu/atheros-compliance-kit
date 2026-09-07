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
   | Repository | `atherosai_compliance_kit` |
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

## Decided: the order is PyPI first, then a public repository

The repository stays **private until the package is published**, and goes public
immediately after. The sequence matters only because it should read as one
release rather than two half-ones: `pip install atheros-compliance-kit` starts
working and the source becomes browsable on the same day.

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

**Before flipping it public** (already verified once, re-run at the time):

```bash
git log --all --full-history -p | grep -inE \
  "^\+.*(BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9]{32,})"
git log --all --diff-filter=A --name-only --pretty=format: | sort -u \
  | grep -E "\.env$|\.pem$|\.key$|signing_key"
```

A secret that was ever committed stays readable in a public repository even after
it is deleted. As of the scan above the history is clean: no keys, no tokens, no
`.env` files, and the only addresses in the tree are synthetic test fixtures.

Then: rename the repository to `atheros-compliance-kit` (the underscore form is a
sixth spelling of a product that should have one name) and add topics —
`eu-ai-act`, `iso-42001`, `ai-governance`, `llm-guardrails`, `rag-evaluation`.

## Not yet done

- [ ] PyPI + TestPyPI trusted publishers registered (above)
- [ ] `pypi` environment with a required reviewer
- [ ] Tag `v1.0.0`, then make the repository public and rename it
- [ ] Licence service deployed, its public key added to `core/license.py`
      `TRUSTED_KEYS`, and `ENFORCED` flipped to `True` — until all three,
      `atheros-kit doctor` correctly reports that enforcement is off
- [ ] Legal sign-off on `LICENSE`, the report footer, and the banned-phrase list

---

## Vercel

The public site (marketing at `/`, console demo at `/demo`) deploys from this
repository. `vercel.json` carries the build command, the output directory and the
headers, so the only thing to set in the dashboard is:

| Setting | Value | Why |
|---|---|---|
| **Root Directory** | `./` (the repository root) | Vercel auto-detected `atheros-compliance-kit/` — the Python package — and ran the build from there, so `scripts/build_public.py` was not found. The build command now locates the repo root itself, but the output directory is still resolved relative to this setting. |
| Framework Preset | Other | There is no root `package.json`; the build is a Python script. |
| `SITE_URL` (env var) | the domain that actually serves the site | Canonicals and the sitemap are absolute. Pointing them at a domain that does not resolve tells every engine to attribute the content to a 404. The build prints a warning when this is unset. |

The build needs neither the Python package nor an installed toolchain beyond
Python 3 and Node: `site/facts.json` is committed, and CI fails if it goes stale.
`.vercelignore` therefore excludes the package, the services and the internal
artifacts — roughly 78 files that a static-site build container has no reason to
receive.

To verify the exact output locally before pushing:

```bash
python scripts/build_public.py     # → public/
cd public && python3 -m http.server 8099
```

CI builds the same output on every push and asserts it is servable: every
internal link resolves, no console asset kept an absolute path, the three
crawler files exist, and every page carries a canonical, an x-default hreflang,
JSON-LD and Open Graph.
