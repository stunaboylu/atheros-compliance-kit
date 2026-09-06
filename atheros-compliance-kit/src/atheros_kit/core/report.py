"""Report assembly and rendering — JSON, Markdown, HTML, (PDF via extra).

One `Report` object per module run. The CI gate, the CLI and the Console all
consume the JSON form; the Markdown form is what lands in a PR comment; the HTML
form is what a compliance lead prints.

Redaction is enforced here, not left to callers: `Report.to_dict()` walks the
tree and strips any key named in `SENSITIVE_KEYS` when `redact` is on. A report
that leaks the PII it detected is the exact failure the product exists to
prevent, and "the caller should have redacted it" is not a control.
"""
from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import i18n
from .errors import MissingDependencyError
from .findings import Coverage, Finding, Score, Severity, worst

#: Keys whose values never survive into a rendered report.
#:
#: This is a name-based blocklist, so a key name that is both generic and
#: legitimate will collide. `value` did: `Score.value` is the measured number —
#: the entire point of the report — and it was being replaced with «redacted» in
#: every JSON document the product emitted. The Console only looked right because
#: it read the scores by a different path, and the Markdown renderer only looked
#: right because it reads the objects rather than the dict.
#:
#: The fix is not to shorten the list. It is `_is_redactable` below: redaction
#: exists to stop DETECTED TEXT escaping, and detected text is always a string.
#: A float, an int, a bool, or None cannot carry a masked email address, so
#: leaving them alone loses no protection and stops the blocklist eating the
#: measurements.
SENSITIVE_KEYS = frozenset({
    "value", "values", "raw", "raw_text", "text", "prompt", "response", "content",
    "matched_text", "secret", "token", "api_key", "vault", "sample_text",
})

_REDACTED = "«redacted»"


def _is_redactable(value: Any) -> bool:
    """Whether a value could carry detected content.

    Strings can. Numbers, booleans and None cannot, and neither can an empty
    container. A list is redactable when it holds any string.
    """
    if isinstance(value, str):
        return bool(value)
    if isinstance(value, (list, tuple, set)):
        return any(isinstance(v, str) and v for v in value)
    if isinstance(value, dict):
        return bool(value)
    return False


def _redact(node: Any, enabled: bool) -> Any:
    if not enabled:
        return node
    if isinstance(node, dict):
        return {
            k: (_REDACTED if k in SENSITIVE_KEYS and _is_redactable(node[k])
                else _redact(v, enabled))
            for k, v in node.items()
        }
    if isinstance(node, list):
        return [_redact(v, enabled) for v in node]
    return node


@dataclass
class Report:
    module: str
    subject: str
    findings: list[Finding] = field(default_factory=list)
    scores: list[Score] = field(default_factory=list)
    coverage: dict[str, Coverage] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    session_id: str = "-"
    degraded: bool = False
    limits: list[str] = field(default_factory=list)
    #: Turkish limits, index-aligned with `limits`. A limit that exists in only
    #: one language would leave a reader of the other with the false assurance
    #: this field exists to prevent.
    limits_tr: list[str] = field(default_factory=list)

    # ── assembly ─────────────────────────────────────────────────────────────
    def add(self, *findings: Finding) -> Report:
        self.findings.extend(findings)
        return self

    def add_score(self, *scores: Score) -> Report:
        for s in scores:
            self.scores.append(s)
            if s.degraded:
                self.degraded = True
        return self

    def note_limit(self, text: str, text_tr: str | None = None) -> Report:
        """Record something this run could NOT establish.

        Printed in every rendering. The difference between 'we checked and found
        nothing' and 'we could not check' is the difference between an assessment
        and a false assurance.
        """
        if text not in self.limits:
            self.limits.append(text)
            self.limits_tr.append(text_tr or text)
        return self

    def limits_in(self, locale: str = "en") -> list[str]:
        if locale == "tr" and len(self.limits_tr) == len(self.limits):
            return self.limits_tr
        return self.limits

    # ── query ────────────────────────────────────────────────────────────────
    def score(self, name: str) -> Score | None:
        return next((s for s in self.scores if s.name == name), None)

    @property
    def worst_severity(self) -> Severity | None:
        return worst(self.findings)

    def by_severity(self, severity: Severity) -> list[Finding]:
        return [f for f in self.findings if f.severity is severity]

    # ── render ───────────────────────────────────────────────────────────────
    def to_dict(self, *, redact: bool = True, locale: str = "en") -> dict[str, Any]:
        locale = i18n.resolve_locale(locale)
        payload = {
            "locale": locale,
            "schema": "atheros.report/v1",
            "module": self.module,
            "subject": self.subject,
            "generated_at": self.generated_at,
            "session_id": self.session_id,
            "degraded": self.degraded,
            "worst_severity": self.worst_severity.value if self.worst_severity else None,
            "scores": [s.to_dict() for s in self.scores],
            "findings": [f.to_dict(locale) for f in self.findings],
            "coverage": {k: v.value for k, v in self.coverage.items()},
            "limits": self.limits_in(locale),
            "limits_tr": self.limits_in("tr"),
            "metadata": self.metadata,
        }
        return _redact(payload, redact)

    def to_json(self, *, redact: bool = True, indent: int = 2, locale: str = "en") -> str:
        return json.dumps(self.to_dict(redact=redact, locale=locale), indent=indent,
                          ensure_ascii=False)

    def to_markdown(self, *, redact: bool = True, locale: str = "en") -> str:
        lo = i18n.resolve_locale(locale)
        t = lambda key, **kw: i18n.ui(key, lo, **kw)  # noqa: E731
        lines = [
            f"# {self.module} — {self.subject}",
            "",
            f"_{t('report.generated', ts=self.generated_at, session=self.session_id)}_",
        ]
        if self.degraded:
            lines += ["", f"> {t('report.degraded')}"]
        if self.scores:
            lines += ["", f"## {t('report.scores')}", "",
                      f"| {t('col.score')} | {t('col.value')} | {t('col.band')} | "
                      f"{t('col.method')} | {t('col.threshold')} | {t('col.result')} |",
                      "|---|---:|---|---|---:|---|"]
            for s in self.scores:
                val = "—" if s.value is None else f"{s.value:.1f}"
                thr = "—" if s.threshold is None else f"{s.threshold:.0f}"
                res = t({True: "verdict.pass", False: "verdict.fail",
                         None: "verdict.unmeasured"}[s.passed])
                band = i18n.enum("band", s.band, lo)
                lines.append(f"| {s.name} | {val} | {band} | `{s.method.value}` | {thr} | {res} |")
        lines += ["", f"## {t('report.findings')}", ""]
        if self.findings:
            lines += [f"| {t('col.severity')} | {t('col.check')} | {t('col.article')} | "
                      f"{t('col.detail')} | {t('col.action')} |", "|---|---|---|---|---|"]
            for f in sorted(self.findings, key=lambda x: -x.severity.rank):
                detail = f.detail_in(lo).replace("|", "\\|")
                lines.append(
                    f"| {i18n.enum('severity', f.severity.value, lo)} | `{f.check}` | "
                    f"{f.article or '—'} | {detail} | "
                    f"{i18n.enum('action', f.action.value, lo)} |"
                )
        else:
            lines.append(t("report.no_findings"))
        if self.coverage:
            lines += ["", f"## {t('report.coverage')}", "",
                      f"| {t('col.section')} | {t('col.status')} |", "|---|---|"]
            for k, v in self.coverage.items():
                lines.append(f"| {k} | {i18n.enum('coverage', v.value, lo)} |")
        if self.limits:
            lines += ["", f"## {t('report.limits')}", ""]
            lines += [f"- {x}" for x in self.limits_in(lo)]
        lines += ["", "---", "", f"_{t('report.footer')}_"]
        return "\n".join(lines)

    def to_html(self, *, redact: bool = True, locale: str = "en") -> str:
        """Self-contained HTML — brand tokens inline, no external requests.

        Dual theme via `prefers-color-scheme`, matching BRAND_KIT.md.
        """
        rows_scores = "".join(
            f"<tr><td>{s.name}</td><td class='num'>{'—' if s.value is None else f'{s.value:.1f}'}</td>"
            f"<td><span class='band {s.band}'>{i18n.enum('band', s.band, i18n.resolve_locale(locale))}</span></td>"
            f"<td class='mono'>{s.method.value}</td></tr>"
            for s in self.scores
        )
        lo = i18n.resolve_locale(locale)
        rows_findings = "".join(
            f"<tr><td><span class='sev {f.severity.value}'>"
            f"{i18n.enum('severity', f.severity.value, lo)}</span></td>"
            f"<td class='mono'>{f.check}</td><td class='mono'>{f.article or '—'}</td>"
            f"<td>{f.detail_in(lo)}</td></tr>"
            for f in sorted(self.findings, key=lambda x: -x.severity.rank)
        )
        limits = "".join(f"<li>{x}</li>" for x in self.limits_in(i18n.resolve_locale(locale)))
        return f"""<!doctype html><html lang="{lo}"><meta charset="utf-8">
<title>{self.module} — {self.subject}</title>
<style>
:root {{ --bg:#FBFBFD; --surface:#fff; --surface-2:#F3F4F8; --border:#DFE2EA;
        --text:#111726; --muted:#525A6B; --accent:#2563EB;
        --good:#22C55E; --watch:#EAB308; --poor:#F97316; --critical:#DC2626;
        --unmeasured:#6B7488; --degraded:#A855F7; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#0B0F17; --surface:#161B26;
        --surface-2:#1E2534; --border:#2A3345; --text:#E6EAF2; --muted:#9AA4B8;
        --accent:#3B82F6; }} }}
body {{ background:var(--bg); color:var(--text); font:14px/1.5 Inter,system-ui,sans-serif;
        margin:0; padding:32px; }}
main {{ max-width:960px; margin:0 auto; }}
h1 {{ font-size:24px; line-height:1.35; margin:0 0 4px; }}
.meta {{ color:var(--muted); font-size:13px; margin-bottom:24px; }}
table {{ width:100%; border-collapse:collapse; background:var(--surface);
        border:1px solid var(--border); border-radius:10px; overflow:hidden; margin:0 0 24px; }}
th,td {{ text-align:left; padding:10px 14px; border-bottom:1px solid var(--border); font-size:13px; }}
th {{ background:var(--surface-2); font-weight:600; }}
tr:last-child td {{ border-bottom:none; }}
.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
.mono {{ font-family:'JetBrains Mono',ui-monospace,monospace; font-size:12px; }}
.band,.sev {{ display:inline-block; padding:2px 8px; border-radius:999px; font-size:11px;
        font-weight:600; text-transform:uppercase; }}
.good {{ color:var(--good); background:#22C55E1a; }} .watch {{ color:var(--watch); background:#EAB3081a; }}
.poor {{ color:var(--poor); background:#F973161a; }} .critical {{ color:var(--critical); background:#DC26261a; }}
.unmeasured {{ color:var(--unmeasured); background:#6B74881a; }}
.high {{ color:var(--poor); background:#F973161a; }} .medium {{ color:var(--watch); background:#EAB3081a; }}
.low,.info {{ color:var(--accent); background:#3B82F61a; }}
.banner {{ border-left:3px solid var(--degraded); background:var(--surface-2);
        padding:12px 16px; border-radius:6px; margin-bottom:24px; }}
footer {{ color:var(--muted); font-size:12px; border-top:1px solid var(--border);
        padding-top:16px; margin-top:32px; }}
</style><main>
<h1>{self.module} — {self.subject}</h1>
<p class="meta">Generated {self.generated_at} · session <span class="mono">{self.session_id}</span></p>
{'<div class="banner"><strong>Degraded run.</strong> At least one score used the deterministic fallback path rather than the configured model.</div>' if self.degraded else ''}
<h2>{i18n.ui("report.scores", lo)}</h2><table><tr><th>Score</th><th class="num">Value</th><th>Band</th><th>Method</th></tr>{rows_scores or '<tr><td colspan="4">{i18n.ui("report.no_scores", lo)}</td></tr>'}</table>
<h2>{i18n.ui("report.findings", lo)}</h2><table><tr><th>Severity</th><th>Check</th><th>Article</th><th>Detail</th></tr>{rows_findings or '<tr><td colspan="4">{i18n.ui("report.no_findings", lo)}</td></tr>'}</table>
{f'<h2>Limits of this assessment</h2><ul>{limits}</ul>' if limits else ''}
<footer>{i18n.ui("report.footer", lo)}</footer>
</main></html>"""

    def to_pdf(self, path: str | Path, *, redact: bool = True, locale: str = "en") -> Path:
        from . import license

        license.require("export.pdf")
        try:
            from weasyprint import HTML  # type: ignore
        except ImportError:
            raise MissingDependencyError("weasyprint", "pdf", "PDF export") from None
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        HTML(string=self.to_html(redact=redact, locale=locale)).write_pdf(str(out))
        return out

    def save(self, directory: str | Path, *, stem: str | None = None,
             formats: Iterable[str] = ("json", "md"), redact: bool = True,
             locale: str = "en") -> list[Path]:
        d = Path(directory)
        d.mkdir(parents=True, exist_ok=True)
        stem = stem or f"{self.module}-{self.subject}".lower().replace(" ", "-").replace("/", "-")
        written: list[Path] = []
        renderers = {"json": self.to_json, "md": self.to_markdown, "html": self.to_html}
        for fmt in formats:
            if fmt == "pdf":
                written.append(self.to_pdf(d / f"{stem}.pdf", redact=redact, locale=locale))
                continue
            if fmt not in renderers:
                continue
            p = d / f"{stem}.{fmt}"
            p.write_text(renderers[fmt](redact=redact, locale=locale), encoding="utf-8")
            written.append(p)
        return written
