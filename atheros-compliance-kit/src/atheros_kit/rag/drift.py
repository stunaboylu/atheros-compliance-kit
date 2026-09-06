"""Semantic drift detection over a corpus's embedding space.

The question this answers: *has the knowledge base become a different knowledge
base since the last time anyone looked?* Teams monitor model drift and ignore
corpus drift, but in a RAG system the corpus is most of the behaviour — new
ingestions shift what gets retrieved long before any metric on the model moves.

Three complementary signals, because each is blind to something:

- **Centroid cosine shift** — has the corpus's centre of mass moved? Catches a
  wholesale topic change. Blind to a change that preserves the mean.
- **Per-dimension PSI** (population stability index) — has the *shape* of the
  distribution changed, dimension by dimension? Catches a split into two clusters
  that leaves the centroid where it was. The banking-standard bands (0.1 / 0.25)
  are used because they are the ones a risk function already argues about.
- **Volume and recency** — a corpus that doubled has drifted even if the geometry
  says otherwise, and one whose newest document is a year old has a different
  problem that no distance metric will report.

Pure stdlib. Vectors that a customer already has cost nothing to compare.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field

from ..core.findings import Action, Finding, Method, Score, Severity
from .connectors import Chunk, centroid, cosine

#: PSI bands, as used in credit-risk model monitoring. They assume a large
#: sample — which a corpus snapshot frequently is not, so see `psi_noise_floor`.
PSI_STABLE, PSI_MODERATE = 0.10, 0.25
#: Centroid cosine similarity below which the corpus centre has demonstrably moved.
CENTROID_STABLE, CENTROID_SHIFTED = 0.98, 0.90


#: Below this ratio of ||centroid|| to the mean vector norm, the corpus has no
#: coherent direction and the angle between two centroids is noise, not signal.
#: Real sentence embeddings sit in a narrow cone and score far above it; an
#: isotropic cloud scores near zero, and comparing the directions of two
#: near-zero vectors produces a confident, meaningless answer.
CENTROID_INFORMATIVE = 0.15


def _magnitude(v) -> float:
    return math.sqrt(sum(x * x for x in v)) if v else 0.0


def centroid_strength(vectors) -> float:
    """||centroid|| / mean(||v||) — how directional this set of vectors is."""
    if not vectors:
        return 0.0
    mean_norm = sum(_magnitude(v) for v in vectors) / len(vectors)
    return 0.0 if mean_norm == 0 else _magnitude(centroid(vectors)) / mean_norm


@dataclass
class DriftReport:
    verdict: str = "stable"                    # stable | drifting | shifted | unmeasurable
    centroid_similarity: float | None = None
    centroid_informative: bool = True
    psi_mean: float | None = None
    psi_max: float | None = None
    psi_noise_floor: float | None = None
    psi_stable_threshold: float | None = None
    psi_dimensions_unstable: int = 0
    dimensions: int = 0
    baseline_count: int = 0
    current_count: int = 0
    volume_ratio: float | None = None
    findings: list[Finding] = field(default_factory=list)
    score: Score | None = None
    limits: list[str] = field(default_factory=list)
    limits_tr: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "centroid_similarity": self.centroid_similarity,
            "centroid_informative": self.centroid_informative,
            "psi_mean": self.psi_mean,
            "psi_max": self.psi_max,
            "psi_noise_floor": self.psi_noise_floor,
            "psi_stable_threshold": self.psi_stable_threshold,
            "psi_dimensions_unstable": self.psi_dimensions_unstable,
            "dimensions": self.dimensions,
            "baseline_count": self.baseline_count,
            "current_count": self.current_count,
            "volume_ratio": self.volume_ratio,
            "limits": self.limits,
            "score": self.score.to_dict() if self.score else None,
        }


def _histogram(values: Sequence[float], edges: Sequence[float]) -> list[float]:
    """Proportion of `values` falling in each bucket defined by `edges`."""
    counts = [0] * (len(edges) + 1)
    for v in values:
        placed = False
        for i, edge in enumerate(edges):
            if v <= edge:
                counts[i] += 1
                placed = True
                break
        if not placed:
            counts[-1] += 1
    total = len(values) or 1
    return [c / total for c in counts]


def psi(baseline: Sequence[float], current: Sequence[float], buckets: int = 10) -> float:
    """Population stability index for one dimension.

    Buckets are cut on the BASELINE's quantiles, which is the definition — cutting
    on the combined sample makes the index compare each distribution to a moving
    target and understates every real shift.
    """
    if len(baseline) < buckets or not current:
        return 0.0
    ordered = sorted(baseline)
    edges = [ordered[int(len(ordered) * (i + 1) / buckets) - 1] for i in range(buckets - 1)]
    b_hist = _histogram(baseline, edges)
    c_hist = _histogram(current, edges)
    total = 0.0
    for b, c in zip(b_hist, c_hist):
        # Floor at a small epsilon: an empty bucket makes the log infinite, and a
        # drift index of infinity is not more informative than a large one.
        b, c = max(b, 1e-6), max(c, 1e-6)
        total += (c - b) * math.log(c / b)
    return round(total, 4)


def psi_noise_floor(n_baseline: int, n_current: int, buckets: int = 10) -> float:
    """Expected PSI between two samples drawn from the SAME distribution.

    PSI is a chi-square-like statistic, so its value under the null shrinks with
    sample size: roughly (k-1)/n per sample, and about twice that when both sides
    are sampled. The published 0.10 / 0.25 bands come from credit-risk monitoring,
    where n is in the tens of thousands and the floor is negligible.

    A corpus snapshot is often a few hundred chunks. At n=200 with 10 buckets the
    null PSI is ≈0.09 — indistinguishable from the "stable" band — so two
    identical corpora are reported as drifting, every run, forever. A drift
    monitor that fires on unchanged input is one that gets muted, and a muted
    monitor is worse than none.
    """
    n = max(1, min(n_baseline, n_current))
    return round(2 * (buckets - 1) / n, 4)


def js_divergence(p: Sequence[float], q: Sequence[float]) -> float:
    """Jensen-Shannon divergence between two discrete distributions (0–1, base 2)."""
    if not p or not q or len(p) != len(q):
        return 0.0

    def kl(a: Sequence[float], b: Sequence[float]) -> float:
        return sum(x * math.log2(x / y) for x, y in zip(a, b) if x > 0 and y > 0)

    m = [(x + y) / 2 for x, y in zip(p, q)]
    return round(0.5 * kl(p, m) + 0.5 * kl(q, m), 4)


def detect(baseline: list[Chunk], current: list[Chunk], *, psi_buckets: int = 10) -> DriftReport:
    rep = DriftReport(baseline_count=len(baseline), current_count=len(current))

    b_vecs = [list(c.vector) for c in baseline if c.vector]
    c_vecs = [list(c.vector) for c in current if c.vector]

    if not b_vecs or not c_vecs:
        rep.verdict = "unmeasurable"
        rep.limits.append(
            "One or both snapshots contain no embeddings, so geometric drift cannot be "
            "computed. This is not evidence of stability."
        )
        rep.limits_tr.append(
            "Anlık görüntülerin birinde ya da ikisinde gömme yok, bu nedenle geometrik kayma "
            "hesaplanamaz. Bu, kararlılık kanıtı değildir."
        )
        rep.findings.append(Finding(
            "drift_unmeasurable", Severity.MEDIUM,
            "no embeddings available in one or both snapshots",
            "rag", Action.FLAG, "Art. 15",
            remediation="Export vectors alongside text, or the corpus cannot be monitored.",
        ))
        rep.score = Score("drift_stability", None, Method.DETERMINISTIC,
                          basis={"reason": "no embeddings"})
        return rep

    dims = {len(v) for v in b_vecs} | {len(v) for v in c_vecs}
    if len(dims) > 1:
        rep.verdict = "unmeasurable"
        rep.limits.append(
            f"Snapshots contain vectors of {len(dims)} different dimensions ({sorted(dims)}). "
            f"They do not share a space, so no distance between them means anything."
        )
        rep.limits_tr.append(
            f"Anlık görüntüler {len(dims)} farklı boyutta vektör içeriyor ({sorted(dims)}). "
            f"Ortak bir uzayı paylaşmıyorlar, dolayısıyla aralarındaki hiçbir uzaklık anlam taşımaz."
        )
        rep.findings.append(Finding(
            "drift_dimension_mismatch", Severity.CRITICAL,
            f"baseline and current embeddings have different dimensions: {sorted(dims)}",
            "rag", Action.BLOCK, "Art. 15",
            remediation="Re-embed one snapshot with the other's model before comparing. Until "
                        "then every retrieval metric spanning these two is meaningless.",
            params={"dims": sorted(dims)},
        ))
        rep.score = Score("drift_stability", None, Method.DETERMINISTIC,
                          basis={"reason": "dimension mismatch"})
        return rep

    rep.dimensions = dims.pop()

    # ── 1. centroid shift ────────────────────────────────────────────────────
    rep.centroid_similarity = round(cosine(centroid(b_vecs), centroid(c_vecs)), 4)
    # …but only where a centroid means anything. If the vectors are spread evenly
    # around the origin, the centroid is a small residual and its direction is
    # noise: two independent samples from the SAME distribution then score a
    # cosine near zero and the corpus is reported as shifted when nothing changed.
    strength = min(centroid_strength(b_vecs), centroid_strength(c_vecs))
    rep.centroid_informative = strength >= CENTROID_INFORMATIVE
    if not rep.centroid_informative:
        rep.limits.append(
            f"The centroid signal was excluded: the embeddings are close to isotropic "
            f"(directionality {strength:.3f} < {CENTROID_INFORMATIVE}), so the angle between "
            f"two centroids carries no information. The verdict rests on PSI alone."
        )
        rep.limits_tr.append(
            f"Ağırlık merkezi sinyali dışlandı: gömmeler izotropiğe yakın (yönlülük "
            f"{strength:.3f} < {CENTROID_INFORMATIVE}), bu nedenle iki ağırlık merkezi "
            f"arasındaki açı bilgi taşımıyor. Karar yalnızca PSI'ya dayanıyor."
        )

    # ── 2. per-dimension PSI ─────────────────────────────────────────────────
    psis: list[float] = []
    for d in range(rep.dimensions):
        psis.append(psi([v[d] for v in b_vecs], [v[d] for v in c_vecs], buckets=psi_buckets))
    rep.psi_mean = round(sum(psis) / len(psis), 4) if psis else 0.0
    rep.psi_max = round(max(psis), 4) if psis else 0.0

    # Raise the bands to clear the sampling noise for THIS sample size. The
    # published thresholds are kept as the floor — a large corpus is judged by the
    # standard bands and a small one is not judged by noise.
    floor = psi_noise_floor(len(b_vecs), len(c_vecs), psi_buckets)
    rep.psi_noise_floor = floor
    psi_stable = max(PSI_STABLE, floor * 2)
    psi_moderate = max(PSI_MODERATE, floor * 3)
    rep.psi_stable_threshold = round(psi_stable, 4)
    rep.psi_dimensions_unstable = sum(1 for p in psis if p > psi_moderate)
    if psi_stable > PSI_STABLE:
        rep.limits.append(
            f"With {min(len(b_vecs), len(c_vecs))} embedded chunks per snapshot, two identical "
            f"corpora would score a mean PSI of about {floor:.3f} from sampling alone. The bands "
            f"were raised to {psi_stable:.3f} / {psi_moderate:.3f} accordingly — a real shift "
            f"smaller than that cannot be distinguished from noise at this sample size."
        )
        rep.limits_tr.append(
            f"Anlık görüntü başına {min(len(b_vecs), len(c_vecs))} gömülü parça ile, iki özdeş "
            f"külliyat yalnızca örnekleme nedeniyle yaklaşık {floor:.3f} ortalama PSI alırdı. "
            f"Bantlar buna göre {psi_stable:.3f} / {psi_moderate:.3f} seviyesine yükseltildi — "
            f"bundan küçük gerçek bir kayma, bu örneklem büyüklüğünde gürültüden ayırt edilemez."
        )

    # ── 3. volume ────────────────────────────────────────────────────────────
    rep.volume_ratio = round(len(current) / len(baseline), 3) if baseline else None

    if len(b_vecs) < psi_buckets * 5:
        rep.limits.append(
            f"The baseline holds {len(b_vecs)} embedded chunks. PSI over {psi_buckets} buckets "
            f"is unreliable below roughly {psi_buckets * 5}; treat the index as indicative."
        )
        rep.limits_tr.append(
            f"Referans {len(b_vecs)} gömülü parça içeriyor. {psi_buckets} kova üzerinden PSI, "
            f"kabaca {psi_buckets * 5} altında güvenilir değildir; indeksi gösterge sayın."
        )

    # ── verdict ──────────────────────────────────────────────────────────────
    cos_shifted = rep.centroid_informative and rep.centroid_similarity < CENTROID_SHIFTED
    cos_drifting = rep.centroid_informative and rep.centroid_similarity < CENTROID_STABLE
    if cos_shifted or rep.psi_mean > psi_moderate:
        rep.verdict = "shifted"
    elif cos_drifting or rep.psi_mean > psi_stable:
        rep.verdict = "drifting"
    else:
        rep.verdict = "stable"

    _raise_findings(rep)
    # Stability score: 100 at a perfectly stable corpus, 0 once mean PSI reaches
    # twice the moderate band. Not a linear map of cosine — cosine near 1.0 is
    # where all the signal is, and a linear scale throws it away.
    cos_part = max(0.0, min(1.0, (rep.centroid_similarity - CENTROID_SHIFTED) /
                            (1.0 - CENTROID_SHIFTED))) * 100 if rep.centroid_informative else None
    psi_part = max(0.0, 1 - rep.psi_mean / (psi_moderate * 2)) * 100
    value = psi_part if cos_part is None else min(cos_part, psi_part)
    rep.score = Score(
        "drift_stability", round(value, 1), Method.DETERMINISTIC, threshold=70.0,
        basis={"centroid_component": None if cos_part is None else round(cos_part, 1),
               "psi_component": round(psi_part, 1), "verdict": rep.verdict,
               "centroid_informative": rep.centroid_informative},
    )
    return rep


def _raise_findings(rep: DriftReport) -> None:
    if rep.verdict == "shifted":
        cos_txt = (f"centroid similarity {rep.centroid_similarity:.4f}, "
                   if rep.centroid_informative else "centroid signal excluded as uninformative, ")
        rep.findings.append(Finding(
            "corpus_semantic_shift", Severity.HIGH,
            f"the corpus has materially shifted ({cos_txt}mean PSI {rep.psi_mean:.4f}, "
            f"{rep.psi_dimensions_unstable} unstable dimensions)",
            "rag", Action.FLAG, "Art. 15",
            evidence={"centroid_similarity": rep.centroid_similarity, "psi_mean": rep.psi_mean},
            remediation="Re-run retrieval evaluation before trusting current answer quality. "
                        "Recall figures measured on the baseline no longer describe this corpus.",
            params={"cos": cos_txt, "psi": f"{rep.psi_mean:.4f}",
                    "unstable": rep.psi_dimensions_unstable},
        ))
    elif rep.verdict == "drifting":
        cos_txt = (f"centroid similarity {rep.centroid_similarity:.4f}, "
                   if rep.centroid_informative else "centroid signal excluded, ")
        rep.findings.append(Finding(
            "corpus_drift", Severity.MEDIUM,
            f"early drift signal ({cos_txt}mean PSI {rep.psi_mean:.4f})",
            "rag", Action.FLAG, "Art. 15",
            evidence={"centroid_similarity": rep.centroid_similarity, "psi_mean": rep.psi_mean},
            remediation="Watch it. Set this run as the new baseline only if the change was intended.",
            params={"cos": cos_txt, "psi": f"{rep.psi_mean:.4f}"},
        ))
    if rep.volume_ratio is not None and (rep.volume_ratio > 2 or rep.volume_ratio < 0.5):
        rep.findings.append(Finding(
            "corpus_volume_change", Severity.MEDIUM,
            f"the corpus changed size by {rep.volume_ratio:.2f}× "
            f"({rep.baseline_count} → {rep.current_count} chunks)",
            "rag", Action.FLAG,
            evidence={"volume_ratio": rep.volume_ratio},
            remediation="A corpus that halved or doubled has changed regardless of its geometry. "
                        "Confirm the ingestion did what was intended.",
            params={"ratio": f"{rep.volume_ratio:.2f}", "before": rep.baseline_count,
                    "after": rep.current_count},
        ))
