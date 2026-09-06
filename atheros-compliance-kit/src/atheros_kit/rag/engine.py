"""`RAGAuditEngine` — one call that runs Module 1 end to end.

Composes quality + bias + (optionally) drift into a single `Report`, writes the
run to the audit chain, and produces the remediation plan. This is what the CLI
and the CI gate call; the individual functions stay public because a team that
only wants the bias scan should not have to run the rest.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from ..core import i18n, license
from ..core.audit import AuditTrail, default_trail, new_session_id
from ..core.findings import Coverage
from ..core.report import Report
from . import bias as bias_mod
from . import drift as drift_mod
from . import quality as quality_mod
from .connectors import Chunk, InMemoryConnector, VectorStoreConnector, get_connector
from .remediation import Recipe, recommend, to_markdown


@dataclass
class RAGAuditReport:
    report: Report
    quality: quality_mod.QualityReport
    bias: bias_mod.BiasReport
    drift: drift_mod.DriftReport | None
    recipes: list[Recipe] = field(default_factory=list)

    @property
    def fairness_score(self) -> float | None:
        s = self.bias.fairness_score
        return s.value if s else None

    @property
    def quality_score(self) -> float | None:
        s = self.quality.score
        return s.value if s else None

    def remediation_markdown(self, locale: str = "en") -> str:
        return to_markdown(self.recipes, locale)

    def to_dict(self, locale: str = "en") -> dict[str, Any]:
        return {
            **self.report.to_dict(locale=locale),
            "quality": self.quality.to_dict(),
            "bias": self.bias.to_dict(),
            "drift": self.drift.to_dict() if self.drift else None,
            "remediation": [r.to_dict() for r in self.recipes],
        }


class RAGAuditEngine:
    def __init__(
        self,
        connector: VectorStoreConnector | None = None,
        *,
        chunks: Sequence[Chunk] | None = None,
        baseline: Sequence[Chunk] | None = None,
        subject: str = "corpus",
        dimensions: Sequence[str] | None = None,
        extra_dimensions: dict[str, dict[str, list[str]]] | None = None,
        check_pii: bool = True,
        limit: int | None = None,
        trail: AuditTrail | None = None,
    ):
        if connector is None and chunks is None:
            raise ValueError("RAGAuditEngine needs either a connector or an explicit chunk list.")
        self.connector = connector or InMemoryConnector(list(chunks or []))
        self._explicit = list(chunks) if chunks is not None else None
        self.baseline = list(baseline) if baseline else None
        self.subject = subject
        self.dimensions = dimensions
        self.extra_dimensions = extra_dimensions
        self.check_pii = check_pii
        self.limit = limit
        self.trail = trail or default_trail()

    @classmethod
    def from_store(cls, kind: str, *, subject: str | None = None, **config: Any) -> RAGAuditEngine:
        """`RAGAuditEngine.from_store("chroma", collection_name="regulations")`."""
        connector = get_connector(kind, **config)
        return cls(connector, subject=subject or f"{kind}:{config.get('collection_name') or config.get('table') or config.get('index_name') or 'corpus'}")

    def run(self, *, log: bool = True) -> RAGAuditReport:
        license.require("rag")
        session = new_session_id()
        items = self._explicit if self._explicit is not None else list(self.connector.chunks(self.limit))

        q = quality_mod.assess_chunks(items, check_pii=self.check_pii)
        b = bias_mod.score_corpus(items, dimensions=self.dimensions,
                                  extra_dimensions=self.extra_dimensions)
        d = drift_mod.detect(self.baseline, items) if self.baseline else None

        report = Report(module="rag", subject=self.subject, session_id=session)
        report.add(*q.findings, *b.findings)
        if d:
            report.add(*d.findings)
        report.add_score(*[s for s in (q.score, b.fairness_score, d.score if d else None) if s])
        for text, text_tr in (*zip(b.limits, b.limits_tr), *(zip(d.limits, d.limits_tr) if d else ())):
            report.note_limit(text, text_tr)
        if not self.baseline:
            report.note_limit(*i18n.both("limit.no_baseline"))

        # Coverage answers "which Art. 10 questions did this run actually address?"
        # — separate from "did it pass", which is what the scores say.
        report.coverage = {
            "Art. 10 — chunk quality": Coverage.COVERED if q.total_chunks else Coverage.MISSING,
            "Art. 10 — bias examination": (
                Coverage.COVERED if len(b.assessed_dimensions) >= 3
                else Coverage.PARTIAL if b.assessed_dimensions else Coverage.MISSING
            ),
            "Art. 15 — corpus stability": Coverage.COVERED if d and d.verdict != "unmeasurable"
            else Coverage.MISSING,
        }
        report.metadata = {
            "connector": getattr(self.connector, "name", "unknown"),
            "chunks_scanned": len(items),
            "baseline_chunks": len(self.baseline) if self.baseline else 0,
            "assessed_dimensions": b.assessed_dimensions,
            "unassessable_dimensions": b.unassessable,
            "drift_verdict": d.verdict if d else "not_measured",
        }

        recipes = recommend(report.findings)

        if log:
            self.trail.log("rag", "corpus_audit", {
                "subject": self.subject,
                "chunks_scanned": len(items),
                "quality_score": q.score.value if q.score else None,
                "fairness_score": b.fairness_score.value if b.fairness_score else None,
                "drift_verdict": d.verdict if d else "not_measured",
                "findings": len(report.findings),
                "worst_severity": report.worst_severity.value if report.worst_severity else None,
                "recipes": [r.key for r in recipes],
            }, session_id=session)

        return RAGAuditReport(report=report, quality=q, bias=b, drift=d, recipes=recipes)
