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

## Not yet done

- [ ] PyPI + TestPyPI trusted publishers registered (above)
- [ ] `pypi` environment with a required reviewer
- [ ] Licence service deployed, its public key added to `core/license.py`
      `TRUSTED_KEYS`, and `ENFORCED` flipped to `True` — until all three,
      `atheros-kit doctor` correctly reports that enforcement is off
- [ ] Legal sign-off on `LICENSE`, the report footer, and the banned-phrase list
