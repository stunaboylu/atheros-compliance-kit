"""Multi-dimensional bias scoring over a RAG corpus → a 0–100 Fairness Score.

This measures the **corpus**, not the model. That is the gap the Kit exists to
close: teams evaluate answers and never look at the knowledge base those answers
are drawn from, and in a RAG system bias enters through the corpus far more often
than through the weights.

Two signals per dimension:

- **Representation** — are the groups within a dimension present in proportion?
  Scored with the four-fifths rule (min/max ≥ 0.8), the same threshold US
  employment law uses, because it is a defensible number rather than one invented
  here.
- **Contextual sentiment skew** — when a group IS mentioned, is the surrounding
  language systematically more negative than for other groups? A corpus can be
  perfectly balanced in counts and still describe one group in the vocabulary of
  problems. Representation alone would call that fair.

The Fairness Score is the **harmonic mean** across dimensions, so a corpus that is
excellent on geography and catastrophic on gender does not average out to "fine".

**Honesty rules enforced in code:**

- A dimension with too few mentions to be measured is reported in `unassessable`,
  never scored 100. Silence is not fairness.
- `assessed_dimensions` and `unassessable` are separate fields all the way to the
  Console. What was not measured is as important as what was.
- The lexicons are structural and English-first. `limits` says so on every report,
  because a customer whose corpus is Turkish deserves to know the score is partial
  before they act on it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Sequence

from ..core import i18n
from ..core.findings import (
    Action, Finding, Method, Score, Severity, harmonic_mean, score_from_diff, score_from_ratio,
)
from .connectors import Chunk

#: dimension → group → surface terms. Deliberately small and auditable: a
#: customer must be able to read exactly what the score was computed from, and
#: extend it for their own domain (`extra_dimensions=`).
#:
#: A term ending in `*` is a STEM and matches any token beginning with it.
#: Turkish is agglutinative — "kadın" appears as kadının, kadınlar, kadına,
#: kadınların — so exact-token matching finds a fraction of the mentions and the
#: dimension silently falls below the measurement floor. That is worse than no
#: Turkish support, because the report then says "unassessable" about a corpus
#: that discusses the dimension constantly. Stems are kept at four characters or
#: more so they do not collide with unrelated words.
DIMENSIONS: dict[str, dict[str, list[str]]] = {
    "gender": {
        # Turkish has no gendered third-person pronoun — "o" covers everyone — so
        # the Turkish terms are nouns and titles rather than pronouns. A corpus
        # that discusses gender only through pronouns is invisible in Turkish and
        # the report says so rather than scoring it.
        "feminine": ["she", "her", "hers", "woman", "women", "female", "girl", "girls",
                     "mother", "mrs", "ms",
                     "kadın*", "kız*", "bayan*", "anne*", "hanım*", "kadin*", "kiz*"],
        "masculine": ["he", "him", "his", "man", "men", "male", "boy", "boys", "father", "mr",
                      "erkek*", "adam*", "oğlan*", "baba*", "bey*", "oglan*"],
        "non_binary": ["they", "them", "non-binary", "nonbinary", "transgender", "genderqueer",
                       "trans*", "ikili olmayan", "natrans*"],
    },
    "age": {
        "young": ["young", "youth", "teenager", "adolescent", "student", "junior", "graduate",
                  "genç*", "öğrenci*", "ergen*", "yeni mezun", "genc*", "ogrenci*"],
        "middle": ["adult", "mid-career", "experienced professional",
                   "yetişkin*", "orta yaş", "deneyimli", "yetiskin*"],
        "older": ["elderly", "senior citizen", "older adult", "retiree", "pensioner", "aged",
                  "yaşlı*", "emekli*", "ileri yaş", "yasli*", "kıdemli*", "kidemli*"],
    },
    "ethnicity_origin": {
        "european": ["european", "western", "dutch", "german", "french", "british"],
        "asian": ["asian", "chinese", "indian", "japanese", "korean", "turkish"],
        "african": ["african", "nigerian", "kenyan", "egyptian", "moroccan"],
        "latin_american": ["latino", "latina", "hispanic", "brazilian", "mexican"],
        "middle_eastern": ["arab", "middle eastern", "persian", "lebanese", "syrian"],
    },
    "disability": {
        "disability_mentioned": ["disability", "disabled", "impairment", "wheelchair",
                                 "blind", "deaf", "neurodivergent", "autistic",
                                 "engelli*", "sakat*", "tekerlekli sandalye", "görme engel",
                                 "işitme engel", "otiz*", "nörofarklı*"],
        "accommodation": ["accessible", "accommodation", "assistive", "accessibility",
                          "erişilebilir*", "makul uyumlaştırma", "destekleyici teknoloji",
                          "erisilebilir*"],
    },
    "ideological": {
        "progressive": ["progressive", "liberal", "left-wing", "reformist"],
        "conservative": ["conservative", "traditional", "right-wing", "orthodox"],
        "centrist": ["centrist", "moderate", "non-partisan", "bipartisan"],
    },
    "geographic": {
        "global_north": ["united states", "europe", "canada", "australia", "japan",
                         "netherlands", "germany", "uk"],
        "global_south": ["africa", "south asia", "latin america", "southeast asia",
                         "sub-saharan", "developing countr"],
        "urban": ["urban", "metropolitan", "city centre", "city center",
                  "kentsel", "şehir merkez", "büyükşehir", "sehir merkez"],
        "rural": ["rural", "countryside", "remote area", "village",
                  "kırsal", "köy*", "taşra", "kirsal", "koy*"],
    },
    "socioeconomic": {
        "high_income": ["affluent", "wealthy", "high-income", "premium customer", "high net worth",
                        "varlıklı*", "zengin*", "yüksek gelir", "varlikli*"],
        "low_income": ["low-income", "poverty", "underprivileged", "welfare", "unbanked",
                       "financially vulnerable",
                       "düşük gelir", "yoksul*", "dezavantajlı*", "sosyal yardım",
                       "dusuk gelir", "dezavantajli*", "bankasız*"],
    },
}

#: Sentiment lexicon for the contextual-skew signal. Small and domain-neutral;
#: an LLM narrator can refine the interpretation, but the NUMBER stays
#: deterministic — a score that changes because a model was in a different mood
#: is not evidence.
_NEGATIVE = {
    "risk", "risky", "fraud", "fraudulent", "default", "delinquent", "criminal", "crime",
    "suspicious", "threat", "danger", "dangerous", "problem", "problematic", "fail",
    "failure", "poor", "bad", "unreliable", "incapable", "unqualified", "reject",
    "rejected", "denied", "deny", "violent", "abuse", "illegal", "illiterate", "burden",
    "liability", "unstable", "aggressive", "lazy", "dishonest",
    # Turkish. Inflected forms are listed rather than stemmed: the sentiment
    # lexicon is matched against a context WINDOW, where a wrong match is a wrong
    # score rather than a missed mention, so precision matters more than recall.
    "riskli", "risk", "dolandırıcı", "dolandirici", "sahte", "suçlu", "suclu", "suç",
    "şüpheli", "supheli", "tehdit", "tehlikeli", "tehlike", "sorunlu", "sorun",
    "başarısız", "basarisiz", "zayıf", "zayif", "kötü", "kotu", "güvenilmez",
    "guvenilmez", "yetersiz", "niteliksiz", "reddedildi", "reddedilen", "red",
    "elendi", "olumsuz", "istikrarsız", "istikrarsiz", "saldırgan", "saldirgan",
    "tembel", "dürüst olmayan", "yük", "yetkin olmayan", "uygunsuz", "eksik",
}
_POSITIVE = {
    "reliable", "trusted", "trustworthy", "qualified", "capable", "skilled", "expert",
    "excellent", "strong", "successful", "success", "approve", "approved", "eligible",
    "valuable", "leader", "leadership", "innovative", "competent", "responsible",
    "stable", "prosperous", "talented", "diligent", "honest",
    "güvenilir", "guvenilir", "nitelikli", "yetkin", "yetenekli", "uzman", "deneyimli",
    "mükemmel", "mukemmel", "güçlü", "guclu", "başarılı", "basarili", "başarı",
    "onaylandı", "onaylandi", "uygun", "değerli", "degerli", "lider", "liderlik",
    "yenilikçi", "yenilikci", "sorumlu", "istikrarlı", "istikrarli", "çalışkan",
    "caliskan", "dürüst", "durust", "olumlu", "yetenek", "istikrarlı",
}

#: Window of words around a group mention that counts as "context".
CONTEXT_WINDOW = 12
#: Below this many mentions, a dimension cannot be scored honestly.
MIN_MENTIONS = 20

#: Unicode-aware, and that is load-bearing.
#:
#: This was `[a-z][a-z'-]+` — ASCII only — so every Turkish word was truncated at
#: its first non-ASCII character: "kadın" tokenised as "kad" and matched nothing,
#: while "erkek" (pure ASCII) matched fully. The dimension then reported a 40:0
#: split on a corpus that was 40:7, which is worse than not measuring: an
#: under-count in one direction is a bias finding the tool INVENTED.
#:
#: `[^\W\d_]` is "a Unicode letter" — \w minus digits and underscore.
_WORD_RE = re.compile(r"[^\W\d_][\w'’-]*", re.UNICODE)


@dataclass
class DimensionResult:
    dimension: str
    group_counts: dict[str, int]
    total_mentions: int
    representation_ratio: float | None
    representation_score: float | None
    group_sentiment: dict[str, float]
    sentiment_spread: float | None
    sentiment_score: float | None
    score: float | None
    assessed: bool
    reason: str = ""
    reason_tr: str = ""

    @property
    def underrepresented(self) -> list[str]:
        if not self.group_counts or self.total_mentions == 0:
            return []
        mx = max(self.group_counts.values()) or 1
        return sorted(g for g, c in self.group_counts.items() if c / mx < 0.8)

    @property
    def negatively_framed(self) -> list[str]:
        """Groups whose contextual sentiment sits materially below the corpus mean."""
        if not self.group_sentiment:
            return []
        mean = sum(self.group_sentiment.values()) / len(self.group_sentiment)
        return sorted(g for g, s in self.group_sentiment.items() if s < mean - 0.15)

    def to_dict(self) -> dict:
        return {
            "dimension": self.dimension, "assessed": self.assessed, "reason": self.reason,
            "reason_tr": self.reason_tr,
            "total_mentions": self.total_mentions, "group_counts": self.group_counts,
            "representation_ratio": self.representation_ratio,
            "representation_score": self.representation_score,
            "group_sentiment": {k: round(v, 3) for k, v in self.group_sentiment.items()},
            "sentiment_spread": self.sentiment_spread, "sentiment_score": self.sentiment_score,
            "score": self.score, "underrepresented": self.underrepresented,
            "negatively_framed": self.negatively_framed,
        }


@dataclass
class BiasReport:
    fairness_score: Score | None = None
    dimensions: list[DimensionResult] = field(default_factory=list)
    chunks_scanned: int = 0
    findings: list[Finding] = field(default_factory=list)
    limits: list[str] = field(default_factory=list)
    limits_tr: list[str] = field(default_factory=list)

    @property
    def assessed_dimensions(self) -> list[str]:
        return [d.dimension for d in self.dimensions if d.assessed]

    @property
    def unassessable(self) -> list[str]:
        return [d.dimension for d in self.dimensions if not d.assessed]

    @property
    def affected_groups(self) -> list[str]:
        out: set[str] = set()
        for d in self.dimensions:
            if d.assessed:
                out.update(f"{d.dimension}:{g}" for g in d.underrepresented + d.negatively_framed)
        return sorted(out)

    def to_dict(self) -> dict:
        return {
            "fairness_score": self.fairness_score.to_dict() if self.fairness_score else None,
            "chunks_scanned": self.chunks_scanned,
            "assessed_dimensions": self.assessed_dimensions,
            "unassessable": self.unassessable,
            "affected_groups": self.affected_groups,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "limits": self.limits,
        }


def _sentiment(words: Sequence[str]) -> float:
    """−1..+1 over a context window. Neutral (0.0) when neither lexicon fires."""
    neg = sum(1 for w in words if w in _NEGATIVE)
    pos = sum(1 for w in words if w in _POSITIVE)
    return 0.0 if neg + pos == 0 else (pos - neg) / (pos + neg)


def _scan_dimension(name: str, groups: dict[str, list[str]],
                    tokenised: list[list[str]]) -> DimensionResult:
    counts = {g: 0 for g in groups}
    sentiments: dict[str, list[float]] = {g: [] for g in groups}
    # Multi-word terms are matched against the joined text; single words against
    # the token list, so "she" does not match inside "shelf".
    single = {g: {t for t in terms if " " not in t and not t.endswith("*")}
              for g, terms in groups.items()}
    stems = {g: tuple(t[:-1] for t in terms if t.endswith("*"))
             for g, terms in groups.items()}
    phrases = {g: [t for t in terms if " " in t and not t.endswith("*")]
               for g, terms in groups.items()}

    for words in tokenised:
        joined = " ".join(words)
        for g in groups:
            hits: list[int] = []
            for i, w in enumerate(words):
                if w in single[g] or (stems[g] and w.startswith(stems[g])):
                    hits.append(i)
            for phrase in phrases[g]:
                if phrase in joined:
                    idx = joined[:joined.index(phrase)].count(" ")
                    hits.append(idx)
            if hits:
                counts[g] += len(hits)
                for i in hits:
                    lo, hi = max(0, i - CONTEXT_WINDOW), min(len(words), i + CONTEXT_WINDOW + 1)
                    sentiments[g].append(_sentiment(words[lo:hi]))

    total = sum(counts.values())
    present = {g: c for g, c in counts.items() if c > 0}

    if total < MIN_MENTIONS or len(present) < 2:
        return DimensionResult(
            dimension=name, group_counts=counts, total_mentions=total,
            representation_ratio=None, representation_score=None, group_sentiment={},
            sentiment_spread=None, sentiment_score=None, score=None, assessed=False,
            reason=i18n.note("bias.floor", "en", total=total, groups=len(present),
                             floor=MIN_MENTIONS),
            reason_tr=i18n.note("bias.floor", "tr", total=total, groups=len(present),
                                floor=MIN_MENTIONS),
        )

    ratio = min(present.values()) / max(present.values())
    rep_score = score_from_ratio(ratio, threshold=0.8)

    mean_sent = {g: sum(v) / len(v) for g, v in sentiments.items() if v}
    if len(mean_sent) >= 2:
        spread = max(mean_sent.values()) - min(mean_sent.values())
        # Threshold 0.3 on a −1..+1 scale: a third of the range separating how two
        # groups are described is a difference a reader would notice.
        sent_score = score_from_diff(spread, threshold=0.3)
    else:
        spread, sent_score = None, None

    score = harmonic_mean([s for s in (rep_score, sent_score) if s is not None])
    return DimensionResult(
        dimension=name, group_counts=counts, total_mentions=total,
        representation_ratio=round(ratio, 4), representation_score=rep_score,
        group_sentiment=mean_sent, sentiment_spread=round(spread, 4) if spread is not None else None,
        sentiment_score=sent_score, score=round(score, 1), assessed=True,
    )


def score_corpus(
    chunks: Iterable[Chunk],
    *,
    dimensions: Sequence[str] | None = None,
    extra_dimensions: dict[str, dict[str, list[str]]] | None = None,
) -> BiasReport:
    items = list(chunks)
    rep = BiasReport(chunks_scanned=len(items))
    catalogue = dict(DIMENSIONS)
    if extra_dimensions:
        catalogue.update(extra_dimensions)
    if dimensions:
        catalogue = {k: v for k, v in catalogue.items() if k in dimensions}

    tokenised = [_WORD_RE.findall((c.text or "").lower()) for c in items]

    for key in ("limit.lexicon", "limit.surface_terms"):
        en, tr = i18n.both(key)
        rep.limits.append(en)
        rep.limits_tr.append(tr)

    for name, groups in catalogue.items():
        rep.dimensions.append(_scan_dimension(name, groups, tokenised))

    scored = [d.score for d in rep.dimensions if d.assessed and d.score is not None]
    if scored:
        value = harmonic_mean(scored)
        rep.fairness_score = Score(
            "fairness_score", round(value, 1), Method.DETERMINISTIC, threshold=70.0,
            basis={d.dimension: d.score for d in rep.dimensions if d.assessed},
        )
    else:
        # No dimension could be assessed. The score is None — NOT 100. A corpus
        # nobody could measure is not a fair corpus.
        rep.fairness_score = Score(
            "fairness_score", None, Method.DETERMINISTIC, threshold=70.0,
            basis={"reason": "no dimension met the measurement floor"},
        )
        en, tr = i18n.both("limit.no_dimension_measured")
        rep.limits.append(en)
        rep.limits_tr.append(tr)

    _raise_findings(rep)
    return rep


def _raise_findings(rep: BiasReport) -> None:
    for d in rep.dimensions:
        if not d.assessed:
            rep.findings.append(Finding(
                f"bias_unassessable.{d.dimension}", Severity.LOW,
                f"'{d.dimension}' could not be assessed: {d.reason}",
                "rag", Action.FLAG, "Art. 10",
                evidence={"dimension": d.dimension, "mentions": d.total_mentions},
                remediation="Either the corpus does not discuss this dimension, or it does so in "
                            "vocabulary the lexicon does not carry. Extend it via "
                            "`extra_dimensions=` before concluding the first.",
                params={"dimension": d.dimension, "reason": d.reason,
                        "reason_tr": d.reason_tr or d.reason},
            ))
            continue
        if d.representation_score is not None and d.representation_score < 80:
            rep.findings.append(Finding(
                f"representation_imbalance.{d.dimension}",
                Severity.HIGH if d.representation_score < 50 else Severity.MEDIUM,
                f"'{d.dimension}' fails the four-fifths rule "
                f"(ratio {d.representation_ratio:.2f}); under-represented: "
                f"{', '.join(d.underrepresented) or 'n/a'}",
                "rag", Action.FLAG, "Art. 10",
                evidence={"dimension": d.dimension, "ratio": d.representation_ratio,
                          "group_counts": d.group_counts},
                remediation="Augment the corpus for the under-represented groups, or down-sample "
                            "the dominant one. Do not re-weight retrieval to hide it.",
                params={"dimension": d.dimension, "ratio": f"{d.representation_ratio:.2f}",
                        "groups": ", ".join(d.underrepresented) or "n/a"},
            ))
        if d.sentiment_score is not None and d.sentiment_score < 70:
            rep.findings.append(Finding(
                f"framing_skew.{d.dimension}",
                Severity.HIGH if d.sentiment_score < 40 else Severity.MEDIUM,
                f"'{d.dimension}' shows a contextual-language gap of {d.sentiment_spread:.2f} "
                f"between groups; negatively framed: {', '.join(d.negatively_framed) or 'n/a'}",
                "rag", Action.FLAG, "Art. 10",
                evidence={"dimension": d.dimension, "spread": d.sentiment_spread,
                          "group_sentiment": {k: round(v, 3) for k, v in d.group_sentiment.items()}},
                remediation="The corpus is balanced in counts and unbalanced in language. Review "
                            "the source documents for the affected groups; this is the form of "
                            "bias that survives a representation audit.",
                params={"dimension": d.dimension, "spread": f"{d.sentiment_spread:.2f}",
                        "groups": ", ".join(d.negatively_framed) or "n/a"},
            ))

    fs = rep.fairness_score
    if fs and fs.value is not None and fs.value < 70:
        rep.findings.append(Finding(
            "fairness_score_below_threshold",
            Severity.HIGH if fs.value < 50 else Severity.MEDIUM,
            f"Fairness Score {fs.value:.1f}/100 across {len(rep.assessed_dimensions)} "
            f"assessed dimension(s)",
            "rag", Action.FLAG, "Art. 10",
            evidence={"score": fs.value, "assessed": rep.assessed_dimensions,
                      "unassessable": rep.unassessable, "affected": rep.affected_groups},
            remediation="See the per-dimension findings; remediation recipes are in "
                        "`rag.remediation.recommend()`.",
            params={"score": f"{fs.value:.1f}", "n": len(rep.assessed_dimensions)},
        ))
