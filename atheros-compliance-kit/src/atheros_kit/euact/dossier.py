"""Annex IV technical-documentation generator.

Art. 11 requires technical documentation drawn up *before* placing a high-risk
system on the market; Annex IV lists what it must contain. This produces that
document's structure, fills what the Kit's other modules can evidence, and —
the part that matters — **prints the gaps as gaps**.

A generator that emits plausible prose for every section produces a document that
looks complete and is not, which is the single worst artefact this product could
create: it would survive an internal review and fail an external one, at the
point where failing is expensive. So every section carries a `Coverage` value and
the summary leads with what is missing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ..core import i18n, license
from ..core.findings import Action, Coverage, Finding, Severity
from .classifier import RiskClassification

#: Annex IV, points 1–9. Titles are paraphrased for readability; `annex_ref`
#: carries the citation so the mapping to the legal text stays checkable.
SECTIONS: list[dict[str, str]] = [
    {"key": "general_description", "annex_ref": "Annex IV(1)",
     "title": "General description of the AI system",
     "needs": "Intended purpose, provider, version, how it interacts with hardware/software, "
              "deployment form, and the market it is placed on.",
     "title_tr": "Yapay zekâ sisteminin genel tanımı",
     "needs_tr": "Amaçlanan kullanım, sağlayıcı, sürüm, donanım/yazılımla etkileşimi, dağıtım biçimi ve sunulduğu pazar."},
    {"key": "development_process", "annex_ref": "Annex IV(2)(a-b)",
     "title": "Development process and system architecture",
     "needs": "Design specifications, system architecture, computational resources, "
              "and the methods and steps used to develop it.",
     "title_tr": "Geliştirme süreci ve sistem mimarisi",
     "needs_tr": "Tasarım şartnameleri, sistem mimarisi, hesaplama kaynakları ve geliştirmede kullanılan yöntem ve adımlar."},
    {"key": "data_requirements", "annex_ref": "Annex IV(2)(d)",
     "title": "Data and data governance",
     "needs": "Training, validation and testing datasets: provenance, scope, characteristics, "
              "labelling, cleaning, and the examination for possible biases (Art. 10).",
     "title_tr": "Veri ve veri yönetişimi",
     "needs_tr": "Eğitim, doğrulama ve test veri kümeleri: kaynak, kapsam, özellikler, etiketleme, temizleme ve olası önyargılara ilişkin inceleme (Art. 10)."},
    {"key": "human_oversight", "annex_ref": "Annex IV(2)(e)",
     "title": "Human oversight measures",
     "needs": "The oversight measures under Art. 14, including the technical measures that let "
              "output be interpreted, disregarded, or reversed.",
     "title_tr": "İnsan gözetimi tedbirleri",
     "needs_tr": "Art. 14 kapsamındaki gözetim tedbirleri; çıktının yorumlanmasını, göz ardı edilmesini ya da geri alınmasını sağlayan teknik tedbirler dâhil."},
    {"key": "performance_metrics", "annex_ref": "Annex IV(2)(g)",
     "title": "Accuracy, robustness and metrics",
     "needs": "Accuracy metrics and levels, robustness and cybersecurity measures, foreseeable "
              "unintended outcomes, and the limits of performance (Art. 15).",
     "title_tr": "Doğruluk, sağlamlık ve metrikler",
     "needs_tr": "Doğruluk metrikleri ve seviyeleri, sağlamlık ve siber güvenlik tedbirleri, öngörülebilir istenmeyen sonuçlar ve performansın sınırları (Art. 15)."},
    {"key": "risk_management", "annex_ref": "Annex IV(3)",
     "title": "Risk-management system",
     "needs": "The Art. 9 risk-management system: identified risks, mitigations adopted, and "
              "residual risk accepted.",
     "title_tr": "Risk yönetim sistemi",
     "needs_tr": "Art. 9 risk yönetim sistemi: tanımlanan riskler, benimsenen azaltımlar ve kabul edilen artık risk."},
    {"key": "lifecycle_changes", "annex_ref": "Annex IV(4)",
     "title": "Lifecycle changes",
     "needs": "Changes made to the system through its lifecycle, with versions and dates.",
     "title_tr": "Yaşam döngüsü değişiklikleri",
     "needs_tr": "Sistemin yaşam döngüsü boyunca yapılan değişiklikler, sürümleri ve tarihleriyle."},
    {"key": "standards_applied", "annex_ref": "Annex IV(5)",
     "title": "Harmonised standards applied",
     "needs": "Which harmonised standards were applied in full or in part, and where none were "
              "applied, the other solutions adopted to meet the requirements.",
     "title_tr": "Uygulanan uyumlaştırılmış standartlar",
     "needs_tr": "Hangi uyumlaştırılmış standartların tamamen ya da kısmen uygulandığı; hiçbiri uygulanmadıysa gereklilikleri karşılamak için benimsenen diğer çözümler."},
    {"key": "post_market_monitoring", "annex_ref": "Annex IV(8-9)",
     "title": "Post-market monitoring and logging",
     "needs": "The post-market monitoring plan (Art. 72) and the automatic logging described "
              "under Art. 12.",
     "title_tr": "Piyasaya arz sonrası izleme ve kayıt",
     "needs_tr": "Piyasaya arz sonrası izleme planı (Art. 72) ve Art. 12 kapsamında tanımlanan otomatik kayıt tutma."},
]

#: Which Kit module can evidence which section, and what it contributes. This is
#: the same spine as `vocabulary.OBLIGATIONS[...]["evidence_source"]`, read from
#: the other direction.
EVIDENCE_SOURCES: dict[str, list[str]] = {
    "data_requirements": ["rag.quality", "rag.bias", "rag.drift"],
    "human_oversight": ["guard.fallback", "guard.policy"],
    "performance_metrics": ["guard.injection", "rag.drift"],
    "risk_management": ["euact.classifier", "vendor.assess"],
    "post_market_monitoring": ["core.audit", "guard.ledger"],
    "development_process": ["core.models"],
}


@dataclass
class Section:
    key: str
    title: str
    annex_ref: str
    needs: str
    coverage: Coverage = Coverage.MISSING
    content: str = ""
    evidence: list[str] = field(default_factory=list)
    gap_note: str = ""
    #: Turkish forms. `annex_ref` deliberately has none — it is a citation, and a
    #: citation that changes shape between languages cannot be matched across two
    #: copies of the same dossier.
    title_tr: str = ""
    needs_tr: str = ""
    gap_note_tr: str = ""

    def title_in(self, locale: str = "en") -> str:
        return self.title_tr or self.title if locale == "tr" else self.title

    def needs_in(self, locale: str = "en") -> str:
        return self.needs_tr or self.needs if locale == "tr" else self.needs

    def gap_note_in(self, locale: str = "en") -> str:
        return self.gap_note_tr or self.gap_note if locale == "tr" else self.gap_note

    def to_dict(self) -> dict[str, Any]:
        return {"key": self.key, "title": self.title, "title_tr": self.title_tr,
                "annex_ref": self.annex_ref,
                "coverage": self.coverage.value, "content": self.content,
                "evidence": self.evidence, "gap_note": self.gap_note}


@dataclass
class Dossier:
    system: str
    classification: RiskClassification
    sections: list[Section]
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # ── coverage ─────────────────────────────────────────────────────────────
    @property
    def coverage(self) -> dict[str, Coverage]:
        return {s.title: s.coverage for s in self.sections}

    @property
    def completeness(self) -> float:
        """Percent, weighting `partial` at half. Reported, never rounded up."""
        if not self.sections:
            return 0.0
        pts = sum({Coverage.COVERED: 1.0, Coverage.PARTIAL: 0.5}.get(s.coverage, 0.0)
                  for s in self.sections)
        return round(pts / len(self.sections) * 100, 1)

    @property
    def gaps(self) -> list[Section]:
        return [s for s in self.sections if s.coverage in (Coverage.MISSING, Coverage.PARTIAL)]

    def to_findings(self) -> list[Finding]:
        out: list[Finding] = []
        for s in self.gaps:
            out.append(Finding(
                check=f"annex_iv_gap.{s.key}",
                severity=Severity.HIGH if s.coverage is Coverage.MISSING else Severity.MEDIUM,
                detail=f"{s.annex_ref} '{s.title}' is {s.coverage.value}: {s.gap_note}",
                module="euact",
                action=Action.FLAG,
                article="Art. 11 + " + s.annex_ref,
                evidence={"section": s.key, "coverage": s.coverage.value,
                          "evidence_sources": EVIDENCE_SOURCES.get(s.key, [])},
                remediation=s.needs,
                params={"annex_ref": s.annex_ref, "title": s.title,
                        "coverage": s.coverage.value, "note": s.gap_note},
            ))
        return out

    def to_dict(self, locale: str = "en") -> dict[str, Any]:
        return {
            "schema": "atheros.dossier/v1",
            "locale": i18n.resolve_locale(locale),
            "system": self.system,
            "generated_at": self.generated_at,
            "classification": self.classification.to_dict(),
            "completeness_pct": self.completeness,
            "sections": [s.to_dict() for s in self.sections],
        }

    def to_markdown(self, locale: str = "en") -> str:
        lo = i18n.resolve_locale(locale)
        t = lambda key, **kw: i18n.ui(key, lo, **kw)  # noqa: E731
        c = self.classification
        yes_no = ("evet — ", "hayır") if lo == "tr" else ("yes — ", "no")
        grey = (yes_no[0] + (c.grey_zone_reason_in(lo) or "")) if c.grey_zone else yes_no[1]
        lines = [
            f"# {t('dossier.title', system=self.system)}",
            "",
            f"_{t('dossier.subtitle', version=c.regulation_version, ts=self.generated_at)}_",
            "",
            f"## 0. {t('dossier.classification')}",
            "",
            "| | |", "|---|---|",
            f"| {t('dossier.risk_tier')} | **{c.tier}** |",
            f"| {t('dossier.confidence')} | {c.confidence:.2f} |",
            f"| {t('dossier.grey_zone')} | {grey} |",
            f"| {t('dossier.articles')} | {', '.join(c.articles) or '—'} |",
            f"| {t('dossier.annex_categories')} | {', '.join(c.annex_categories) or '—'} |",
            f"| {t('dossier.basis')} | `{c.evidence_basis}` |",
            "",
            f"**{t('dossier.reasoning')}**", "",
        ]
        lines += [f"- {r}" for r in c.reasoning_in(lo)]
        lines += [
            "",
            f"## 0.1 {t('dossier.completeness', pct=f'{self.completeness:.0f}')}",
            "",
            f"| Annex IV | {t('col.section')} | {t('report.coverage')} |", "|---|---|---|",
        ]
        for sec in self.sections:
            lines.append(f"| {sec.annex_ref} | {sec.title_in(lo)} | "
                         f"**{i18n.enum('coverage', sec.coverage.value, lo)}** |")
        if self.gaps:
            lines += ["", "> " + t("dossier.incomplete", gaps=len(self.gaps),
                                   total=len(self.sections))]
        for i, sec in enumerate(self.sections, start=1):
            lines += ["", f"## {i}. {sec.title_in(lo)}", "",
                      f"_{sec.annex_ref} · {t('report.coverage').lower()}: "
                      f"**{i18n.enum('coverage', sec.coverage.value, lo)}**_", ""]
            if sec.content:
                lines.append(sec.content)
            if sec.evidence:
                lines += ["", f"_{t('dossier.evidence')} "
                              f"{', '.join(f'`{e}`' for e in sec.evidence)}_"]
            if sec.coverage is not Coverage.COVERED:
                lines += ["", f"> {t('dossier.gap')} {sec.gap_note_in(lo)}",
                          "", f"> {t('dossier.required')} {sec.needs_in(lo)}"]
        if c.obligations:
            lines += ["", f"## {t('dossier.obligations')}", "",
                      f"| {t('col.article')} | {t('col.duty')} | {t('col.evidence_by')} |",
                      "|---|---|---|"]
            for o in c.obligations:
                duty = o.get("duty_tr", o["duty"]) if lo == "tr" else o["duty"]
                lines.append(f"| {o['article']} | {duty} | `{o['evidence_source']}` |")
        if c.gpai_obligations:
            lines += ["", f"### {t('dossier.gpai')}", "",
                      f"| {t('col.article')} | {t('col.duty')} |", "|---|---|"]
            for o in c.gpai_obligations:
                duty = o.get("duty_tr", o["duty"]) if lo == "tr" else o["duty"]
                lines.append(f"| {o['article']} | {duty} |")
        if c.limits:
            lines += ["", f"## {t('report.limits')}", ""] + [f"- {x}" for x in c.limits_in(lo)]
        lines += ["", "---", "", f"_{t('dossier.footer')}_"]
        return "\n".join(lines)


def generate(
    classification: RiskClassification,
    *,
    system: str | None = None,
    evidence: dict[str, Any] | None = None,
    narrative: dict[str, str] | None = None,
) -> Dossier:
    """Assemble the dossier.

    `evidence` maps a module name to whatever that module produced
    (`{"rag.bias": bias_report, "guard.ledger": summary, ...}`). A section is
    COVERED when narrative prose was supplied for it, PARTIAL when only machine
    evidence exists (evidence supports a section; it does not write one), and
    MISSING otherwise. That ladder is deliberate: automated evidence is necessary
    for Annex IV and nowhere near sufficient, and pretending otherwise is how a
    team discovers the gap during an audit rather than before it.
    """
    license.require("euact.dossier")
    evidence = evidence or {}
    narrative = narrative or {}
    sections: list[Section] = []

    for meta in SECTIONS:
        key = meta["key"]
        sources = EVIDENCE_SOURCES.get(key, [])
        present = [s for s in sources if s in evidence]
        sec = Section(key=key, title=meta["title"], annex_ref=meta["annex_ref"],
                      needs=meta["needs"], evidence=present,
                      title_tr=meta.get("title_tr", ""), needs_tr=meta.get("needs_tr", ""))

        if narrative.get(key):
            sec.content = narrative[key]
            sec.coverage = Coverage.COVERED if present or not sources else Coverage.PARTIAL
            if sec.coverage is Coverage.PARTIAL:
                sec.gap_note = (
                    f"Written up, but no machine evidence from {', '.join(sources)} was attached. "
                    f"The claim rests on the author's assertion alone."
                )
                sec.gap_note_tr = (
                    f"Yazılmış, ancak {', '.join(sources)} kaynağından makine kanıtı eklenmemiş. "
                    f"İddia yalnızca yazarın beyanına dayanıyor."
                )
        elif present:
            sec.coverage = Coverage.PARTIAL
            sec.content = _summarise_evidence(present, evidence)
            sec.gap_note = (
                f"Automated evidence is attached ({', '.join(present)}) but no description has "
                f"been written. Annex IV asks for an account of the system, which evidence "
                f"supports and does not replace."
            )
            sec.gap_note_tr = (
                f"Otomatik kanıt eklenmiş ({', '.join(present)}) ancak hiçbir açıklama "
                f"yazılmamış. Annex IV, sistemin bir anlatımını ister; kanıt bunu destekler, yerine "
                f"geçmez."
            )
        else:
            sec.coverage = Coverage.MISSING
            sec.gap_note = (
                "Nothing has been supplied for this section."
                + (f" The Kit can evidence part of it via {', '.join(sources)}." if sources
                   else " No Kit module produces this; it requires human authorship.")
            )
            sec.gap_note_tr = (
                "Bu bölüm için hiçbir şey sağlanmadı."
                + (f" Kit, bunun bir kısmını {', '.join(sources)} ile kanıtlayabilir." if sources
                   else " Hiçbir Kit modülü bunu üretmez; insan tarafından yazılması gerekir.")
            )
        sections.append(sec)

    # Section 0-equivalent: the classification itself always covers risk management
    # partially, because a tier and its obligations ARE the start of Art. 9.
    return Dossier(system=system or classification.system or "unnamed-system",
                   classification=classification, sections=sections)


def _summarise_evidence(sources: list[str], evidence: dict[str, Any]) -> str:
    """One line per attached artefact. Deliberately terse — this is not prose,
    and formatting it as prose would disguise that no prose exists."""
    lines = []
    for src in sources:
        item = evidence[src]
        if isinstance(item, dict):
            keys = ", ".join(list(item)[:6])
            lines.append(f"- `{src}` — attached ({keys}{'…' if len(item) > 6 else ''})")
        elif isinstance(item, list):
            lines.append(f"- `{src}` — attached ({len(item)} items)")
        else:
            lines.append(f"- `{src}` — attached")
    return "Attached machine evidence:\n\n" + "\n".join(lines)
