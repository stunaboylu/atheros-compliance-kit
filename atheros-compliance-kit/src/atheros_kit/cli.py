"""`atheros-kit` — the command line.

Design notes:

- **Every command works offline.** No key, no network, no vector store required
  for the deterministic path; the exit code is the contract.
- **ANSI-16 only, `NO_COLOR` honoured, and the glyph carries the meaning.** CI
  logs mangle 256-colour, and a reader with no colour at all must lose nothing.
- **Exit codes:** 0 pass · 1 gate failed / findings above threshold · 2 error.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from .core import i18n
from .core.audit import AuditTrail, default_trail, set_default_trail
from .core.config import Config
from .core.errors import AtherosError

_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
_C = {"red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m", "blue": "\033[34m",
      "magenta": "\033[35m", "dim": "\033[2m", "bold": "\033[1m", "off": "\033[0m"}


def c(text: str, colour: str) -> str:
    return f"{_C[colour]}{text}{_C['off']}" if _COLOR else text


_GLYPH = {"critical": ("⨯", "red"), "high": ("▲", "red"), "medium": ("!", "yellow"),
          "low": ("·", "blue"), "info": ("✓", "green")}
_BAND = {"good": "green", "watch": "yellow", "poor": "red", "critical": "red",
         "unmeasured": "dim"}


def print_report(report, *, limit: int = 40, locale: str = "en") -> None:
    print(f"\n{c(report.module.upper(), 'bold')} — {report.subject}   "
          f"{c('session ' + report.session_id, 'dim')}")
    if report.degraded:
        print(c("  degraded run — at least one score used the deterministic fallback path", "magenta"))
    for s in report.scores:
        val = "—" if s.value is None else f"{s.value:6.1f}"
        verdict = i18n.ui({True: "verdict.pass", False: "verdict.fail",
                           None: "verdict.unmeasured"}[s.passed], locale).strip("*")
        band = i18n.enum("band", s.band, locale)
        print(f"  {c(val, _BAND[s.band])}  {s.name:22} {c(f'{band:11}', _BAND[s.band])} "
              f"{c(verdict, 'green' if s.passed else ('red' if s.passed is False else 'dim'))}")
    shown = sorted(report.findings, key=lambda f: -f.severity.rank)[:limit]
    for f in shown:
        glyph, colour = _GLYPH[f.severity.value]
        art = f" {c('[' + f.article + ']', 'dim')}" if f.article else ""
        sev = i18n.enum("severity", f.severity.value, locale)
        print(f"  {c(glyph, colour)} {c(f'{sev:9}', colour)} {f.check}{art}\n"
              f"      {f.detail_in(locale)}")
    if len(report.findings) > limit:
        print(c(f"  … {len(report.findings) - limit} more finding(s); see the JSON report", "dim"))
    for lim in report.limits_in(locale):
        print(c(f"  {'sınır' if locale == 'tr' else 'limit'}: {lim}", "dim"))


def _load_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _apply_global(args) -> Config:
    if getattr(args, "audit_file", None):
        set_default_trail(AuditTrail(args.audit_file))
    cfg = Config.load(getattr(args, "config", None))
    args.locale = i18n.resolve_locale(getattr(args, "lang", None) or cfg.get("locale"))
    return cfg


def _t(args, key: str, **kw) -> str:
    return i18n.ui(key, getattr(args, "locale", "en"), **kw)


# ── commands ──────────────────────────────────────────────────────────────────
def cmd_euact_classify(args) -> int:
    from .euact import SystemSpec, classify
    _apply_global(args)
    spec = SystemSpec.from_dict(_load_json(args.spec)) if args.spec else SystemSpec(
        name=args.name or "unnamed-system", sector=args.sector or "",
        use_cases=args.use_case or [], description=args.description or "")
    result = classify(spec)
    lo = args.locale
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return 0
    tier_colour = {"unacceptable": "red", "high": "red", "limited": "yellow",
                   "minimal": "green", "unknown": "dim"}[result.tier]
    conf_label = "güven" if lo == "tr" else "confidence"
    print(f"\n{c(result.tier.upper(), tier_colour)}  {spec.name}   "
          f"{conf_label} {result.confidence:.2f}   {c(result.regulation_version, 'dim')}")
    if result.grey_zone:
        label = "gri bölge" if lo == "tr" else "grey zone"
        print(c(f"  ? {label} — {result.grey_zone_reason_in(lo)}", "magenta"))
    for r in result.reasoning_in(lo):
        print(f"    · {r}")
    art_label = "maddeler" if lo == "tr" else "articles"
    basis_label = "dayanak " if lo == "tr" else "basis:   "
    print(f"  {art_label}: {', '.join(result.articles)}")
    print(f"  {basis_label} {c(result.evidence_basis, 'dim')}")
    if result.obligations:
        print(f"\n  {c(i18n.ui('dossier.obligations', lo).lower(), 'bold')}")
        ev_label = "kanıt: " if lo == "tr" else "evidence: "
        for o in result.obligations:
            duty = o.get("duty_tr", o["duty"]) if lo == "tr" else o["duty"]
            print(f"    {o['article']:20} {duty[:78]}")
            print(f"    {'':20} {c(ev_label + o['evidence_source'], 'dim')}")
    for lim in result.limits_in(lo):
        print(c(f"  {'sınır' if lo == 'tr' else 'limit'}: {lim}", "dim"))
    return 1 if result.tier == "unacceptable" else 0


def cmd_euact_dossier(args) -> int:
    from .euact import SystemSpec, classify, generate_dossier
    _apply_global(args)
    result = classify(SystemSpec.from_dict(_load_json(args.spec)))
    evidence = _load_json(args.evidence) if args.evidence else {}
    doc = generate_dossier(result, evidence=evidence)
    out = Path(args.out or f"{result.system}-annex-iv.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc.to_markdown(args.locale), encoding="utf-8")
    out.with_suffix(".json").write_text(
        json.dumps(doc.to_dict(args.locale), indent=2, ensure_ascii=False), encoding="utf-8")
    band = "green" if doc.completeness >= 80 else ("yellow" if doc.completeness >= 50 else "red")
    lo = args.locale
    print(("yazıldı: " if lo == "tr" else "wrote ") + f"{out}, {out.with_suffix('.json')}")
    print((f"tamlık: {c(f'%{doc.completeness:.0f}', band)}  "
           f"({len(doc.sections)} bölümden {len(doc.gaps)} tanesi eksik ya da kısmi)") if lo == "tr"
          else (f"completeness: {c(f'{doc.completeness:.0f}%', band)}  "
                f"({len(doc.gaps)} of {len(doc.sections)} sections missing or partial)"))
    return 0


def cmd_euact_questions(args) -> int:
    from .euact.decision_tree import as_schema
    print(json.dumps(as_schema(), indent=2, ensure_ascii=False))
    return 0


def cmd_rag_audit(args) -> int:
    from .rag import Chunk, RAGAuditEngine
    cfg = _apply_global(args)
    if args.chunks:
        raw = _load_json(args.chunks)
        chunks = [Chunk(id=str(d.get("id", i)), text=d.get("text", ""),
                        vector=d.get("vector"), metadata=d.get("metadata", {}))
                  for i, d in enumerate(raw)]
        engine = RAGAuditEngine(chunks=chunks, subject=args.subject or Path(args.chunks).stem)
    else:
        store_cfg = _load_json(args.store_config) if args.store_config else {}
        engine = RAGAuditEngine.from_store(args.store, subject=args.subject, **store_cfg)
    if args.baseline:
        raw = _load_json(args.baseline)
        engine.baseline = [Chunk(id=str(d.get("id", i)), text=d.get("text", ""),
                                 vector=d.get("vector")) for i, d in enumerate(raw)]
    audit = engine.run()
    if args.json:
        print(json.dumps(audit.to_dict(locale=args.locale), indent=2, ensure_ascii=False))
    else:
        print_report(audit.report, locale=args.locale)
        if audit.recipes:
            print(f"\n  {c(i18n.ui('remediation.title', args.locale).lower(), 'bold')}")
            for r in audit.recipes[:6]:
                print(f"    {r.title}  {c(f'impact {r.impact} / effort {r.effort}', 'dim')}")
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(
            json.dumps(audit.to_dict(locale=args.locale), indent=2, ensure_ascii=False),
            encoding="utf-8")
        Path(args.out).with_name("remediation.md").write_text(
            audit.remediation_markdown(args.locale), encoding="utf-8")
        print(f"\nwrote {args.out}")
    floor = cfg.get("fail_on.fairness_score_below", 70)
    fs = audit.fairness_score
    return 1 if (fs is None or fs < floor) else 0


def cmd_vendor_assess(args) -> int:
    from .vendor import assess, known_providers
    cfg = _apply_global(args)
    if args.list:
        print("\n".join(known_providers()))
        return 0
    overrides = _load_json(args.overrides) if args.overrides else None
    flags = _load_json(args.contract_flags) if args.contract_flags else None
    a = assess(args.provider, overrides=overrides, required_regions=args.region or ["EU"],
               contract_flags=flags, dpf_certified=args.dpf_certified)
    if args.json:
        print(json.dumps(a.to_dict(locale=args.locale), indent=2, ensure_ascii=False))
        return 0
    print_report(a.report, locale=args.locale)
    lo = args.locale
    if lo == "tr":
        print(f"\n  yerleşim:  {a.residency.verdict}  ({a.residency.mechanism})")
        print(f"  çıkma:     {a.optout.verdict}")
        print(f"  bilgiler {a.entry.as_of} tarihli"
              + (c("  ESKİ — yeniden doğrulayın", "yellow") if a.entry.stale else ""))
    else:
        print(f"\n  residency: {a.residency.verdict}  ({a.residency.mechanism})")
        print(f"  opt-out:   {a.optout.verdict}")
        print(f"  facts as of {a.entry.as_of}"
              + (c("  STALE — re-verify", "yellow") if a.entry.stale else ""))
    floor = cfg.get("fail_on.vendor_score_below", 60)
    return 1 if a.score.value is None or a.score.value < floor else 0


def cmd_audit_verify(args) -> int:
    _apply_global(args)
    lo = args.locale
    trail = AuditTrail(args.file) if args.file else default_trail()
    intact, violations = trail.verify_chain(locale=lo)
    entries = sum(1 for _ in trail.entries())
    if intact:
        print(f"{c(i18n.ui('chain.intact', lo), 'green')}  "
              + i18n.ui("chain.entries", lo, n=entries,
                        plural="y" if entries == 1 else "ies", path=trail.path))
        return 0
    print(f"{c(i18n.ui('chain.violated', lo), 'red')}  "
          + i18n.ui("chain.violations", lo, n=len(violations), path=trail.path))
    for v in violations[:20]:
        print(f"  {v}")
    if len(violations) > 20:
        print(c("  " + i18n.ui("chain.more", lo, n=len(violations) - 20), "dim"))
    return 1


def cmd_audit_show(args) -> int:
    _apply_global(args)
    trail = AuditTrail(args.file) if args.file else default_trail()
    for e in trail.entries():
        if args.module and e.get("module") != args.module:
            continue
        print(json.dumps(e, ensure_ascii=False) if args.json else
              f"{e['timestamp'][:19]}  {e['module']:8} {e['event_type']:20} "
              f"{c(e['hash'][:12], 'dim')}")
    return 0


def cmd_iso_export(args) -> int:
    """Collect the ledger into one ISO/IEC 42001 evidence pack.

    Exit 1 means the pack is not fit to hand to an auditor — a chain that does
    not verify, or a ledger with nothing in it. Both are states an operator must
    not discover after the document has already been sent.
    """
    from .iso import build_pack
    from .iso.export import write_pack

    cfg = _apply_global(args)
    lo = args.locale
    trail = AuditTrail(args.file) if args.file else default_trail()
    pack = build_pack(trail)

    if args.stdout:
        print(pack.to_markdown(lo))
    else:
        formats = ("md", "json") if args.format == "both" else (args.format,)
        out = args.out or cfg.get("report_dir", ".atheros/reports")
        written = write_pack(pack, out, lo, formats=formats)
        print(("yazıldı: " if lo == "tr" else "wrote ") + ", ".join(str(w) for w in written))

    total = len(pack.coverage)
    if lo == "tr":
        print(f"{total} maddenin {c(str(pack.evidenced), 'green' if pack.evidenced else 'yellow')} "
              f"tanesinde kayıt var · {pack.total_entries} defter kaydı")
    else:
        print(f"{c(str(pack.evidenced), 'green' if pack.evidenced else 'yellow')} of {total} "
              f"clauses hold records · {pack.total_entries} ledger entries")

    if not pack.chain_intact:
        print(c(i18n.ui("chain.violated", lo), "red") + "  "
              + ("kanıt paketi teslim edilebilir durumda değil"
                 if lo == "tr" else "this pack is not fit to hand over"))
        return 1
    if pack.total_entries == 0:
        print(c("defter boş — paket hiçbir kanıt içermiyor" if lo == "tr"
                else "the ledger is empty — the pack contains no evidence", "yellow"))
        return 1
    return 0


def cmd_ci_gate(args) -> int:
    from .cicd import gate
    cfg = _apply_global(args)
    kwargs: dict[str, Any] = {}
    if args.rag_report:
        kwargs["rag_audit"] = _ReportShim(_load_json(args.rag_report))
    if args.euact_report:
        kwargs["classification"] = _ClassificationShim(_load_json(args.euact_report))
    result = gate.run(cfg, write_to=args.out, locale=args.locale, **kwargs)
    print(result.to_markdown(args.locale) if args.markdown else _gate_text(result, args.locale))
    return result.exit_code


def _gate_text(result, locale: str = "en") -> str:
    icon = {"pass": (c("✓", "green"), "green"), "fail": (c("⨯", "red"), "red"),
            "unmeasured": (c("?", "yellow"), "yellow"), "skipped": (c("–", "dim"), "dim"),
            "error": (c("!", "red"), "red")}
    label = "uyum kapısı" if locale == "tr" else "compliance gate"
    lines = [f"\n{c(label, 'bold')} — "
             + (c(i18n.ui("gate.passed", locale), "green") if result.passed
                else c(i18n.ui("gate.failed", locale), "red"))]
    for o in result.outcomes:
        g, col = icon[o.status]
        label = i18n.ui(f"status.{o.status}", locale)
        lines.append(f"  {g} {label:11} {o.name:30} "
                     f"{'' if o.actual is None else o.actual}  {c(o.detail, 'dim')}")
    lines.append(c(f"  {i18n.ui('gate.artefacts', locale)} {', '.join(result.artefacts)}", "dim"))
    return "\n".join(lines)


class _ReportShim:
    """Adapts a previously written JSON rag report back to what the gate reads."""

    def __init__(self, d: dict):
        self._d = d
        self.fairness_score = ((d.get("bias") or {}).get("fairness_score") or {}).get("value")
        self.quality_score = ((d.get("quality") or {}).get("score") or {}).get("value")
        drift = d.get("drift")
        self.drift = type("D", (), {"verdict": drift["verdict"]})() if drift else None

    def to_dict(self) -> dict:
        return self._d


class _ClassificationShim:
    def __init__(self, d: dict):
        self._d = d
        self.tier = d.get("tier", "unknown")
        self.grey_zone = d.get("grey_zone", False)
        self.confidence = d.get("confidence")

    def to_dict(self) -> dict:
        return self._d


def cmd_init(args) -> int:
    """Write a starter config and, optionally, a CI workflow.

    The format follows what THIS install can read. Writing atheros.yml on a
    base install produces a config the tool then refuses to parse — correct
    behaviour from the loader (silently dropping a config file is worse), and a
    broken first five minutes. JSON is a subset of YAML, so the JSON form stays
    valid if the yaml extra is added later.
    """
    try:
        import yaml  # noqa: F401
        fmt = "yaml"
    except ImportError:
        fmt = "json"
    fmt = args.format or fmt

    settings = {
        "audit_file": ".atheros/audit_trail.jsonl",
        "report_dir": ".atheros/reports",
        "locale": "en",
        "mode": "enterprise",
        # A check that could not be MEASURED fails the gate. That is deliberate:
        # a gate which goes green when the measurement breaks is worse than none.
        "fail_on": {
            "fairness_score_below": 70,
            "quality_score_below": 70,
            "vendor_score_below": 60,
            "drift_verdict_in": ["shifted"],
            "risk_tier_in": ["unacceptable"],
            "residency_verdict_in": ["non_compliant"],
            "guard_blocks_above": 0,
            "chain_violation": True,
        },
    }

    cfg_path = Path("atheros.yml" if fmt == "yaml" else "atheros.json")
    if cfg_path.exists() and not args.force:
        print(f"{cfg_path} already exists (use --force to overwrite)")
        return 1
    if fmt == "yaml":
        body = (
            "# AtherosAI Compliance Kit\n"
            "# A check that could not be MEASURED fails the gate. That is deliberate:\n"
            "# a gate which goes green when the measurement breaks is worse than none.\n"
            "audit_file: .atheros/audit_trail.jsonl\n"
            "report_dir: .atheros/reports\n"
            "locale: en\n"
            "mode: enterprise\n"
            "\n"
            "fail_on:\n"
            "  fairness_score_below: 70\n"
            "  quality_score_below: 70\n"
            "  vendor_score_below: 60\n"
            "  drift_verdict_in: [shifted]\n"
            "  risk_tier_in: [unacceptable]\n"
            "  residency_verdict_in: [non_compliant]\n"
            "  guard_blocks_above: 0\n"
            "  chain_violation: true\n"
        )
    else:
        body = json.dumps(settings, indent=2) + "\n"
    cfg_path.write_text(body, encoding="utf-8")
    print(f"wrote {cfg_path}")
    if fmt == "json":
        print(c("  (JSON, because PyYAML is not installed here — it is fully supported. "
                "Install the [yaml] extra if you would rather write atheros.yml.)", "dim"))

    if args.ci:
        src = Path(__file__).parent / "cicd" / "templates" / (
            "github-actions.yml" if args.ci == "github" else "gitlab-ci.yml")
        dest = Path(".github/workflows/atheros-compliance.yml") if args.ci == "github" \
            else Path("atheros-gitlab-ci.yml")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"wrote {dest}")
    return 0


def cmd_doctor(args) -> int:
    """What is installed, what is configured, what will therefore run."""
    from . import __version__
    from .core import models
    print(f"{c('atheros-compliance-kit', 'bold')} {__version__}   python "
          f"{sys.version.split()[0]}")
    print(f"\n{c('optional dependencies', 'bold')}")
    for pkg, extra, purpose in [("yaml", "yaml", "atheros.yml config"),
                                ("numpy", "rag", "faster vector maths"),
                                ("chromadb", "rag", "Chroma connector"),
                                ("psycopg2", "rag", "pgvector connector"),
                                ("weasyprint", "pdf", "PDF export")]:
        try:
            __import__(pkg)
            print(f"  {c('✓', 'green')} {pkg:14} {c(purpose, 'dim')}")
        except ImportError:
            print(f"  {c('–', 'dim')} {pkg:14} {c(f'absent — pip install ...[{extra}] for {purpose}', 'dim')}")
    providers = models.configured_providers()
    print(f"\n{c('model providers', 'bold')}")
    print(f"  keys present: {', '.join(providers) if providers else c('none', 'dim')}")
    if not providers:
        print(c("  every check runs its deterministic path; scores will be marked degraded "
                "only where a model was configured and unavailable", "dim"))
    floating = models.floating_models()
    if floating:
        print(c(f"  unpinned model names: {', '.join(floating)} — 'which model produced this' "
                f"cannot be answered later", "yellow"))
    from .core import license as lic_mod

    lic = lic_mod.status()
    print(f"\n{c('licence', 'bold')}")
    print(f"  tier: {lic['tier']}"
          + (f"  ({lic['account']}, {lic['seats']} seats, expires {lic['expires']})"
             if lic.get("account") else ""))
    print(c(f"  {lic['reason']}", "dim"))
    print(c(f"  {lic['note']}", "dim" if lic["enforced"] else "yellow"))

    trail = default_trail()
    intact, violations = trail.verify_chain()
    print(f"\n{c('audit chain', 'bold')}\n  {trail.path}: "
          + (c("intact", "green") if intact else c(f"{len(violations)} violation(s)", "red")))
    return 0


# ── parser ────────────────────────────────────────────────────────────────────
def _global_flags() -> argparse.ArgumentParser:
    """Flags accepted BEFORE or AFTER the subcommand.

    argparse puts a top-level option before the subcommand, and nobody types it
    there — `atheros-kit euact classify --lang tr` is what a person writes, and
    rejecting it teaches them the tool is fussy. Attaching the same parser as a
    parent to every leaf command makes both positions work.
    """
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", help="path to atheros.yml (default: nearest one found)")
    common.add_argument("--audit-file", help="path to the hash-chained audit trail")
    common.add_argument("--lang", choices=list(i18n.SUPPORTED),
                        help="output language (default: ATHEROS_LOCALE, then the config, then "
                             "en). Article citations and identifiers are never translated.")
    return common


def build_parser() -> argparse.ArgumentParser:
    common = _global_flags()
    p = argparse.ArgumentParser(
        prog="atheros-kit",
        parents=[common],
        description="AtherosAI Compliance Kit — AI governance evidence, "
                    "generated by the system that needs it.")
    sub = p.add_subparsers(dest="group", required=True)

    # euact
    e = sub.add_parser("euact", help="EU AI Act classification and dossier").add_subparsers(
        dest="cmd", required=True)
    ec = e.add_parser("classify", parents=[common], help="classify a system")
    ec.add_argument("--spec", help="JSON file describing the system")
    ec.add_argument("--name")
    ec.add_argument("--sector")
    ec.add_argument("--description")
    ec.add_argument("--use-case", action="append", help="repeatable")
    ec.add_argument("--json", action="store_true")
    ec.set_defaults(func=cmd_euact_classify)
    ed = e.add_parser("dossier", parents=[common], help="generate Annex IV technical documentation")
    ed.add_argument("--spec", required=True)
    ed.add_argument("--evidence")
    ed.add_argument("--out")
    ed.set_defaults(func=cmd_euact_dossier)
    eq = e.add_parser("questions", parents=[common], help="print the intake question tree as JSON")
    eq.set_defaults(func=cmd_euact_questions)

    # rag
    r = sub.add_parser("rag", help="RAG corpus quality, drift and bias").add_subparsers(
        dest="cmd", required=True)
    ra = r.add_parser("audit", parents=[common], help="audit a corpus")
    ra.add_argument("--store", default="memory", help="chroma | pgvector | pinecone | milvus")
    ra.add_argument("--store-config", help="JSON file of connector kwargs")
    ra.add_argument("--chunks", help="JSON array of {id,text,vector} — no store needed")
    ra.add_argument("--baseline", help="JSON array for drift comparison")
    ra.add_argument("--subject")
    ra.add_argument("--out")
    ra.add_argument("--json", action="store_true")
    ra.set_defaults(func=cmd_rag_audit)

    # vendor
    v = sub.add_parser("vendor", help="third-party provider risk").add_subparsers(
        dest="cmd", required=True)
    va = v.add_parser("assess", parents=[common], help="assess a provider")
    va.add_argument("provider", nargs="?", default="")
    va.add_argument("--region", action="append", help="required processing region (repeatable)")
    va.add_argument("--overrides", help="JSON file of your own verified facts")
    va.add_argument("--contract-flags", help="JSON file: what your signed DPA and console show")
    va.add_argument("--dpf-certified", action="store_true", default=None)
    va.add_argument("--list", action="store_true", help="list seeded providers")
    va.add_argument("--json", action="store_true")
    va.set_defaults(func=cmd_vendor_assess)

    # audit
    a = sub.add_parser("audit", help="the hash-chained ledger").add_subparsers(
        dest="cmd", required=True)
    av = a.add_parser("verify", parents=[common], help="recompute every digest")
    av.add_argument("--file")
    av.set_defaults(func=cmd_audit_verify)
    ash = a.add_parser("show", parents=[common], help="print entries")
    ash.add_argument("--file")
    ash.add_argument("--module")
    ash.add_argument("--json", action="store_true")
    ash.set_defaults(func=cmd_audit_show)

    # iso
    iso = sub.add_parser("iso", help="ISO/IEC 42001 evidence export").add_subparsers(
        dest="cmd", required=True)
    ix = iso.add_parser("export", parents=[common],
                        help="collect the ledger into one auditor-facing evidence pack")
    ix.add_argument("--file", help="ledger to read (default: the configured trail)")
    ix.add_argument("--out", help="output directory (default: report_dir from the config)")
    ix.add_argument("--format", choices=["md", "json", "both"], default="both")
    ix.add_argument("--stdout", action="store_true",
                    help="print the Markdown instead of writing files")
    ix.set_defaults(func=cmd_iso_export)

    # ci
    ci = sub.add_parser("ci", help="the regression gate").add_subparsers(dest="cmd", required=True)
    cg = ci.add_parser("gate", parents=[common], help="evaluate thresholds and set the exit code")
    cg.add_argument("--rag-report")
    cg.add_argument("--euact-report")
    cg.add_argument("--out")
    cg.add_argument("--markdown", action="store_true")
    cg.set_defaults(func=cmd_ci_gate)

    # init / doctor
    i = sub.add_parser("init", parents=[common], help="write a starter atheros.yml (and a CI workflow)")
    i.add_argument("--ci", choices=["github", "gitlab"])
    i.add_argument("--format", choices=["yaml", "json"],
                   help="default: yaml if PyYAML is installed, otherwise json")
    i.add_argument("--force", action="store_true")
    i.set_defaults(func=cmd_init, cmd="init")
    d = sub.add_parser("doctor", parents=[common], help="what is installed and what will therefore run")
    d.set_defaults(func=cmd_doctor, cmd="doctor")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except AtherosError as exc:
        print(f"{c('error', 'red')}: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"{c('error', 'red')}: {exc.filename} not found", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
