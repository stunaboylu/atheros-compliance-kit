# The CI gate
> Turning an assessment into a control your engineers do not disable.

# The CI gate

A governance number nobody enforces decays. The only enforcement point engineers respect is the one that fails the build — and the only gate they keep is one that does not lie to them.

## Configure

```yaml
# atheros.yml
audit_file: .atheros/audit_trail.jsonl
report_dir: .atheros/reports
locale: en          # or tr

fail_on:
  fairness_score_below: 70
  quality_score_below: 70
  vendor_score_below: 60
  drift_verdict_in: [shifted]
  risk_tier_in: [unacceptable]
  residency_verdict_in: [non_compliant]
  guard_blocks_above: 0
  chain_violation: true
```

`atheros-kit init --ci github` writes this file and a working workflow. On a base install with no YAML support it writes `atheros.json` instead and says why — a starter config the tool then refuses to parse is a broken first five minutes.

## Run

```
atheros-kit ci gate        # 0 pass · 1 failed · 2 error
```

## The two rules

**An unmeasured check fails.** A score of `None` means the measurement did not run or could not be computed. Treating that as a pass means the gate goes green at exactly the moment it should not — when the measurement itself broke.

**Every skipped check is printed.** If a module was not configured, the summary names it. A gate that hides what it did not check reads as full coverage, and the person reading the summary is usually the person least able to know the difference.

```
compliance gate — FAILED
  ⨯ fairness_score      fail       0.0    0.0 < 70
  ⨯ quality_score       fail       24.5   24.5 < 70
  ✓ corpus_drift        pass       stable
  ? corpus_drift        unmeasured        no baseline supplied
  – vendor              skipped           module not configured
  ✓ audit_chain         pass       intact
```

## GitHub Actions

The generated workflow installs the Kit (seconds — the core has no dependencies), runs the gate, comments the summary on the pull request, and uploads the evidence with a 90-day retention **even when the job failed**. An artefact that only exists on success is an artefact nobody reads.

No API key is required. Set `GEMINI_API_KEY` or `OPENAI_API_KEY` only if you want the optional narrative layer; every number is produced deterministically either way.

## GitLab CI

Ships in the same templates directory. Same contract, `artifacts: when: always`, and the report surfaced in the merge-request widget.

## Baselines

Drift needs two snapshots. Commit a baseline export alongside the code and pass it with `--baseline`; without one, the gate reports drift as **skipped** rather than as stable.

Promote a snapshot to a new baseline only when the change was intended. Promoting silently hides the drift permanently.

## What to measure first

Adopt in this order — each step earns the next:

- **The guard wrapper.** Day one, for a purely engineering reason: do not leak PII, do not get injected. No compliance argument required.
- **The gate on `chain_violation` and `risk_tier_in`.** Cheap, and it never false-positives.
- **The corpus audit.** Once someone asks about Art. 10.
- **Vendor assessments.** Once procurement sends the first questionnaire.
