"""Chunk-quality assessment for a RAG corpus.

What this measures and why each one earns its place:

- **Length distribution.** Chunks far below the median retrieve as noise; chunks
  far above it blow the context budget and bury the answer. Both are invisible
  until someone plots them.
- **Empty and near-empty.** A PDF page that extracted to whitespace still occupies
  a retrieval slot. It is the cheapest bug in RAG and the most common.
- **Exact duplicates.** Re-ingestion without a purge. Duplicates crowd out the
  top-k and inflate every recall number a team reports.
- **Near duplicates.** Boilerplate headers and footers, template contracts. Same
  effect, invisible to a hash.
- **Orphans (no vector).** A chunk with no embedding is unreachable. It is in the
  corpus and it is not in the index — the gap between "we ingested it" and "it
  can be retrieved" is where RAG failures live.
- **Ragged dimensions.** Two embedding models wrote into one collection. Cosine
  distance across them is meaningless, so every retrieval is subtly wrong.
- **Personal data in the corpus.** Reuses the guard detectors — a knowledge base
  full of unredacted PII is an Art. 10 finding regardless of how good retrieval is.

Everything here is deterministic. No model call, no key, no network.
"""
from __future__ import annotations

import statistics
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field

from ..core.findings import (
    Action,
    Finding,
    Method,
    Score,
    Severity,
    harmonic_mean,
    score_from_ratio,
)
from ..guard.pii import detect_categories
from .connectors import Chunk

#: Below this, a chunk carries no retrievable meaning on its own.
NEAR_EMPTY_CHARS = 40
#: Jaccard overlap on 5-word shingles above which two chunks are the same passage.
NEAR_DUP_THRESHOLD = 0.85
#: Sampling cap for the O(n²) near-duplicate pass. Stated in the report, never
#: silently applied: a truncated check that reads as a full one is a lie.
NEAR_DUP_SAMPLE = 2000


@dataclass
class QualityReport:
    total_chunks: int = 0
    empty: list[str] = field(default_factory=list)
    near_empty: list[str] = field(default_factory=list)
    exact_duplicates: dict[str, list[str]] = field(default_factory=dict)
    near_duplicate_pairs: list[tuple[str, str, float]] = field(default_factory=list)
    orphans: list[str] = field(default_factory=list)
    dimension_histogram: dict[int, int] = field(default_factory=dict)
    length_stats: dict[str, float] = field(default_factory=dict)
    outliers_short: list[str] = field(default_factory=list)
    outliers_long: list[str] = field(default_factory=list)
    pii_chunks: dict[str, list[str]] = field(default_factory=dict)
    near_dup_sampled: bool = False
    findings: list[Finding] = field(default_factory=list)
    score: Score | None = None

    @property
    def duplicate_chunk_count(self) -> int:
        """Redundant copies, not distinct texts: three identical chunks are two
        wasted retrieval slots, not three."""
        return sum(len(ids) - 1 for ids in self.exact_duplicates.values())

    def to_dict(self) -> dict:
        return {
            "total_chunks": self.total_chunks,
            "empty": len(self.empty),
            "near_empty": len(self.near_empty),
            "duplicate_groups": len(self.exact_duplicates),
            "duplicate_chunks": self.duplicate_chunk_count,
            "near_duplicate_pairs": len(self.near_duplicate_pairs),
            "orphans": len(self.orphans),
            "dimension_histogram": self.dimension_histogram,
            "length_stats": self.length_stats,
            "outliers_short": len(self.outliers_short),
            "outliers_long": len(self.outliers_long),
            "pii_chunks": len(self.pii_chunks),
            "pii_categories": sorted({c for cats in self.pii_chunks.values() for c in cats}),
            "near_dup_sampled": self.near_dup_sampled,
            "score": self.score.to_dict() if self.score else None,
        }


def assess_chunks(chunks: Iterable[Chunk] | Iterator[Chunk], *,
                  check_pii: bool = True,
                  near_dup_sample: int = NEAR_DUP_SAMPLE) -> QualityReport:
    items = list(chunks)
    rep = QualityReport(total_chunks=len(items))
    if not items:
        rep.score = Score("quality_score", None, Method.DETERMINISTIC,
                          basis={"reason": "empty corpus"})
        rep.findings.append(Finding(
            "empty_corpus", Severity.HIGH, "the connector returned no chunks",
            "rag", Action.FLAG, article="Art. 10",
            remediation="Check the collection name and namespace before trusting any retrieval metric.",
        ))
        return rep

    lengths: list[int] = []
    by_fingerprint: dict[str, list[str]] = {}

    for c in items:
        lengths.append(c.length)
        text = (c.text or "").strip()
        if not text:
            rep.empty.append(c.id)
        elif len(text) < NEAR_EMPTY_CHARS:
            rep.near_empty.append(c.id)
        if c.vector is None or len(c.vector) == 0:
            rep.orphans.append(c.id)
        else:
            d = len(c.vector)
            rep.dimension_histogram[d] = rep.dimension_histogram.get(d, 0) + 1
        if text:
            by_fingerprint.setdefault(c.fingerprint, []).append(c.id)
        if check_pii and text:
            cats = detect_categories(text)
            if cats:
                rep.pii_chunks[c.id] = cats

    rep.exact_duplicates = {fp: ids for fp, ids in by_fingerprint.items() if len(ids) > 1}

    # ── length distribution ──────────────────────────────────────────────────
    non_empty = [n for n in lengths if n > 0]
    if non_empty:
        median = statistics.median(non_empty)
        rep.length_stats = {
            "min": float(min(non_empty)), "max": float(max(non_empty)),
            "mean": round(statistics.fmean(non_empty), 1), "median": float(median),
            "stdev": round(statistics.pstdev(non_empty), 1) if len(non_empty) > 1 else 0.0,
        }
        # Ratio to the median rather than a standard-deviation band: chunk lengths
        # are not normally distributed — they are bimodal wherever two ingestion
        # paths feed one collection — and a σ band on a bimodal distribution
        # flags the wrong tail.
        for c in items:
            if c.length == 0:
                continue
            if c.length < median * 0.25:
                rep.outliers_short.append(c.id)
            elif c.length > median * 4:
                rep.outliers_long.append(c.id)

    # ── near duplicates ──────────────────────────────────────────────────────
    candidates = [c for c in items if (c.text or "").strip()]
    if len(candidates) > near_dup_sample:
        rep.near_dup_sampled = True
        step = len(candidates) / near_dup_sample
        candidates = [candidates[int(i * step)] for i in range(near_dup_sample)]
    # Keep ONE representative per exact-duplicate group and drop the rest. Keeping
    # all-but-the-first inverts the intent: twenty identical chunks then produce
    # 171 "near duplicate" pairs restating a finding already reported exactly once,
    # and the pair count — which an operator reads as breadth — becomes noise.
    already_reported = {cid for ids in rep.exact_duplicates.values() for cid in ids[1:]}
    shingles = [(c.id, c.shingles) for c in candidates if c.id not in already_reported]
    for i in range(len(shingles)):
        id_a, sh_a = shingles[i]
        if not sh_a:
            continue
        for j in range(i + 1, len(shingles)):
            id_b, sh_b = shingles[j]
            if not sh_b:
                continue
            union = len(sh_a | sh_b)
            if union == 0:
                continue
            jac = len(sh_a & sh_b) / union
            if jac >= NEAR_DUP_THRESHOLD:
                rep.near_duplicate_pairs.append((id_a, id_b, round(jac, 3)))

    _raise_findings(rep)
    rep.score = _score(rep)
    return rep


def _raise_findings(rep: QualityReport) -> None:
    n = rep.total_chunks
    add = rep.findings.append

    if rep.empty:
        add(Finding("empty_chunks", Severity.MEDIUM,
                    f"{len(rep.empty)} chunk(s) contain no text but occupy a retrieval slot",
                    "rag", Action.FLAG, "Art. 10",
                    evidence={"count": len(rep.empty), "sample_ids": rep.empty[:10]},
                    remediation="Delete them, then re-check the extraction step that produced them.",
                    params={"count": len(rep.empty)}))
    if rep.near_empty:
        add(Finding("near_empty_chunks", Severity.LOW,
                    f"{len(rep.near_empty)} chunk(s) under {NEAR_EMPTY_CHARS} characters carry no "
                    f"standalone meaning",
                    "rag", Action.FLAG, "Art. 10",
                    evidence={"count": len(rep.near_empty), "sample_ids": rep.near_empty[:10]},
                    remediation="Merge with an adjacent chunk or drop; revisit the chunking boundary.",
                    params={"count": len(rep.near_empty), "threshold": NEAR_EMPTY_CHARS}))
    if rep.orphans:
        sev = Severity.HIGH if len(rep.orphans) > n * 0.02 else Severity.MEDIUM
        add(Finding("unembedded_chunks", sev,
                    f"{len(rep.orphans)} chunk(s) have no embedding and cannot be retrieved at all",
                    "rag", Action.FLAG, "Art. 10",
                    evidence={"count": len(rep.orphans), "sample_ids": rep.orphans[:10]},
                    remediation="Re-run embedding for these ids. They are in the corpus and absent "
                                "from the index — every recall figure computed over this collection "
                                "is optimistic by this amount.",
                    params={"count": len(rep.orphans)}))
    if len(rep.dimension_histogram) > 1:
        add(Finding("mixed_embedding_dimensions", Severity.CRITICAL,
                    f"chunks carry {len(rep.dimension_histogram)} different vector dimensions "
                    f"({', '.join(f'{d}: {c}' for d, c in sorted(rep.dimension_histogram.items()))})",
                    "rag", Action.BLOCK, "Art. 15",
                    evidence={"histogram": rep.dimension_histogram},
                    remediation="Two embedding models have written into one collection. Distances "
                                "across them are meaningless, so retrieval quality cannot be "
                                "assessed until the collection is re-embedded with one model.",
                    params={"count": len(rep.dimension_histogram),
                            "histogram": ", ".join(f"{d}: {c}" for d, c in sorted(rep.dimension_histogram.items()))}))
    if rep.duplicate_chunk_count:
        pct = rep.duplicate_chunk_count / n * 100
        add(Finding("duplicate_chunks", Severity.HIGH if pct > 10 else Severity.MEDIUM,
                    f"{rep.duplicate_chunk_count} redundant copies across "
                    f"{len(rep.exact_duplicates)} group(s) ({pct:.1f}% of the corpus)",
                    "rag", Action.FLAG, "Art. 10",
                    evidence={"groups": len(rep.exact_duplicates),
                              "redundant": rep.duplicate_chunk_count},
                    remediation="De-duplicate by content hash before the next ingestion, and make "
                                "the ingestion idempotent so this does not recur.",
                    params={"redundant": rep.duplicate_chunk_count,
                            "groups": len(rep.exact_duplicates), "pct": f"{pct:.1f}"}))
    if rep.near_duplicate_pairs:
        add(Finding("near_duplicate_chunks", Severity.MEDIUM,
                    f"{len(rep.near_duplicate_pairs)} chunk pair(s) exceed "
                    f"{NEAR_DUP_THRESHOLD:.0%} shingle overlap",
                    "rag", Action.FLAG, "Art. 10",
                    evidence={"pairs": len(rep.near_duplicate_pairs),
                              "sample": rep.near_duplicate_pairs[:5]},
                    remediation="Usually shared boilerplate. Strip headers and footers at ingestion "
                                "rather than deleting the documents.",
                    params={"pairs": len(rep.near_duplicate_pairs),
                            "threshold": f"{NEAR_DUP_THRESHOLD:.0%}"}))
    if rep.outliers_long:
        add(Finding("oversized_chunks", Severity.LOW,
                    f"{len(rep.outliers_long)} chunk(s) exceed 4× the median length",
                    "rag", Action.FLAG,
                    evidence={"count": len(rep.outliers_long), "sample_ids": rep.outliers_long[:10]},
                    remediation="Re-chunk these documents; an oversized chunk buries its answer.",
                    params={"count": len(rep.outliers_long)}))
    if rep.pii_chunks:
        add(Finding("personal_data_in_corpus", Severity.HIGH,
                    f"{len(rep.pii_chunks)} chunk(s) contain structurally recognisable personal "
                    f"data ({', '.join(sorted({c for v in rep.pii_chunks.values() for c in v}))})",
                    "rag", Action.FLAG, "Art. 10 / GDPR Art. 5(1)(c)",
                    evidence={"count": len(rep.pii_chunks),
                              "categories": sorted({c for v in rep.pii_chunks.values() for c in v}),
                              "sample_ids": list(rep.pii_chunks)[:10]},
                    remediation="Redact at ingestion. Note that these detectors are structural — "
                                "names and free-text identifiers are not caught, so this count is "
                                "a floor, never a total.",
                    params={"count": len(rep.pii_chunks),
                            "categories": ", ".join(sorted({c for v in rep.pii_chunks.values() for c in v}))}))


def _score(rep: QualityReport) -> Score:
    """Composite 0–100. Harmonic, so one collapsed dimension is not averaged away."""
    n = max(rep.total_chunks, 1)
    parts = {
        "content": score_from_ratio(1 - (len(rep.empty) + len(rep.near_empty)) / n, 1.0),
        "retrievable": score_from_ratio(1 - len(rep.orphans) / n, 1.0),
        "distinct": score_from_ratio(1 - rep.duplicate_chunk_count / n, 1.0),
        "sizing": score_from_ratio(1 - (len(rep.outliers_short) + len(rep.outliers_long)) / n, 1.0),
    }
    value = harmonic_mean(parts.values())
    # A mixed-dimension corpus cannot be scored honestly: the vectors do not
    # share a space, so "retrievable" means nothing. Cap it rather than emit a
    # number that reads as a passing grade.
    capped = len(rep.dimension_histogram) > 1
    if capped:
        value = min(value, 40.0)
    return Score(
        "quality_score", round(value, 1), Method.DETERMINISTIC, threshold=70.0,
        basis={**{k: round(v, 1) for k, v in parts.items()},
               "capped_for_mixed_dimensions": capped,
               "near_duplicate_check_sampled": rep.near_dup_sampled},
    )
