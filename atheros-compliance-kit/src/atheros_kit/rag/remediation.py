"""Remediation recipes — what to actually do about a finding.

Recipes are **generated, ordered and printed. They are never executed.** The Kit
holds a read-only connection to a customer's knowledge base by design; a tool
that both diagnoses and silently rewrites a corpus is one bug away from being the
incident. Each recipe carries the command or code a human runs, and the risk of
running it.

Ordering is by leverage, not severity: deleting 400 duplicate chunks is a
two-minute fix that lifts every retrieval metric, and it should be done before
anyone spends a week rebalancing a lexicon. `effort` and `impact` are on every
recipe so the order is inspectable rather than asserted.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from ..core import i18n
from ..core.findings import Finding


@dataclass
class Recipe:
    key: str
    title: str
    rationale: str
    steps: list[str]
    impact: str                 # high | medium | low — expected effect on retrieval quality
    effort: str                 # low | medium | high
    risk: str                   # what running this can break
    article: str | None = None
    affects: dict[str, Any] = field(default_factory=dict)
    code: str | None = None

    @property
    def leverage(self) -> int:
        weight = {"high": 3, "medium": 2, "low": 1}
        return weight[self.impact] * 3 - weight[self.effort]

    def to_dict(self) -> dict[str, Any]:
        return {"key": self.key, "title": self.title, "rationale": self.rationale,
                "steps": self.steps, "impact": self.impact, "effort": self.effort,
                "risk": self.risk, "article": self.article, "affects": self.affects,
                "code": self.code, "leverage": self.leverage}


def _for_finding(f: Finding) -> Recipe | None:
    e = f.evidence or {}
    check = f.check.split(".")[0]

    if check == "duplicate_chunks":
        return Recipe(
            key="dedupe", title="De-duplicate the corpus by content hash",
            rationale=(f"{e.get('redundant', '?')} redundant copies occupy retrieval slots that "
                       f"would otherwise hold distinct evidence, and inflate every recall figure "
                       f"measured on this collection."),
            steps=[
                "Group chunks by a whitespace- and case-normalised SHA-256 of their text.",
                "Keep the copy with the richest metadata; delete the rest.",
                "Add the same hash as a uniqueness constraint at ingestion so it cannot recur.",
                "Re-run `atheros-kit rag audit` to confirm the group count is zero.",
            ],
            impact="high", effort="low",
            risk="Deleting the wrong copy loses its metadata. Keep the richest, not the oldest.",
            article="Art. 10", affects=e,
            code=("from atheros_kit.rag import assess_chunks\n"
                  "report = assess_chunks(connector.chunks())\n"
                  "for fingerprint, ids in report.exact_duplicates.items():\n"
                  "    keep, remove = ids[0], ids[1:]      # inspect metadata before choosing\n"
                  "    print('delete', remove)             # then delete via YOUR store's client"),
        )
    if check == "unembedded_chunks":
        return Recipe(
            key="reembed_orphans", title="Embed the chunks that have no vector",
            rationale=(f"{e.get('count', '?')} chunks are in the corpus and absent from the index. "
                       f"They can never be retrieved, and every recall number computed over this "
                       f"collection is optimistic by that amount."),
            steps=[
                "Collect the orphan ids from the quality report.",
                "Re-run the embedding step for exactly those ids — not the whole corpus.",
                "Confirm the new vectors match the collection's existing dimension.",
                "Make the ingestion fail loudly when an embedding call returns nothing.",
            ],
            impact="high", effort="low",
            risk="Embedding with a different model than the rest of the collection is worse than "
                 "leaving them absent — it corrupts distances for every query.",
            article="Art. 10", affects=e,
        )
    if check == "mixed_embedding_dimensions":
        return Recipe(
            key="reembed_collection", title="Re-embed the whole collection with one model",
            rationale=("Two embedding models have written into one collection. Distances between "
                       "their vectors are not comparable, so retrieval is subtly and invisibly "
                       "wrong for every query that spans both."),
            steps=[
                "Decide which model the collection standardises on and pin its exact version.",
                "Create a NEW collection; do not migrate in place.",
                "Re-embed every chunk with the pinned model, writing to the new collection.",
                "Re-run retrieval evaluation against both before cutting over.",
                "Record the model version in the collection metadata so this is detectable next time.",
            ],
            impact="high", effort="high",
            risk="A full re-embed costs real money and time. Do it in a new collection so a "
                 "rollback is a config change, not a second re-embed.",
            article="Art. 15", affects=e,
        )
    if check == "empty_chunks":
        return Recipe(
            key="prune_empty", title="Delete empty chunks and fix the extractor that made them",
            rationale=("An empty chunk occupies a retrieval slot and returns nothing. It is "
                       "usually a symptom: a PDF page that extracted to whitespace."),
            steps=["Delete the listed ids.",
                   "Trace them back to their source documents.",
                   "Add a non-empty assertion at ingestion so the extractor fails visibly."],
            impact="medium", effort="low",
            risk="Low — but fix the extractor, or they return with the next ingestion.",
            article="Art. 10", affects=e,
        )
    if check == "near_duplicate_chunks":
        return Recipe(
            key="strip_boilerplate", title="Strip shared boilerplate before chunking",
            rationale=("High shingle overlap between otherwise different documents is almost "
                       "always a repeated header, footer, or confidentiality notice diluting "
                       "the embedding of every chunk that carries it."),
            steps=["Inspect the sample pairs to identify the repeated block.",
                   "Remove it in the pre-chunking cleanup, not with a post-hoc filter.",
                   "Re-chunk and re-embed the affected documents."],
            impact="medium", effort="medium",
            risk="An over-eager stripper removes real content. Anchor on exact repeated blocks.",
            article="Art. 10", affects=e,
        )
    if check == "oversized_chunks":
        return Recipe(
            key="rechunk", title="Re-chunk the oversized documents",
            rationale="A chunk far above the median buries its answer and crowds the context window.",
            steps=["Re-chunk the listed ids at the collection's target size with overlap.",
                   "Re-embed the resulting chunks and delete the originals.",
                   "Confirm the length distribution has one mode, not two."],
            impact="medium", effort="medium",
            risk="Re-chunking changes ids; update anything that references them.",
            affects=e,
        )
    if check == "personal_data_in_corpus":
        return Recipe(
            key="redact_pii", title="Redact personal data at ingestion",
            rationale=(f"{e.get('count', '?')} chunks carry structurally recognisable personal "
                       f"data ({', '.join(e.get('categories', []))}). Under Art. 10 and GDPR "
                       f"Art. 5(1)(c) a knowledge base should hold what the task needs and no more."),
            steps=["Run `atheros_kit.guard.Anonymizer` over documents in the ingestion pipeline.",
                   "Re-ingest the affected documents from source, masked.",
                   "Delete the unmasked chunks; masking a copy does not remove the original.",
                   "Add the masking step to CI so new documents cannot bypass it."],
            impact="high", effort="medium",
            risk="These detectors are structural. Names and free-text identifiers are NOT caught, "
                 "so this count is a floor. Do not treat a clean re-run as proof of a clean corpus.",
            article="Art. 10 / GDPR Art. 5(1)(c)", affects=e,
            code=("from atheros_kit.guard import Anonymizer\n"
                  "anon = Anonymizer(reversible=False)   # ingestion never needs to restore\n"
                  "clean = anon.mask(document_text).text"),
        )
    if check == "representation_imbalance":
        dim = f.check.split(".", 1)[-1]
        return Recipe(
            key=f"rebalance_{dim}", title=f"Rebalance corpus representation for '{dim}'",
            rationale=(f"The '{dim}' dimension fails the four-fifths rule (ratio "
                       f"{e.get('ratio', '?')}). A retrieval layer returns what the corpus "
                       f"contains, so this imbalance reaches every answer."),
            steps=[f"Identify source documents covering the under-represented groups: "
                   f"{', '.join(e.get('group_counts', {}))}.",
                   "Augment with real documents first. Synthetic augmentation is a last resort "
                   "and must be labelled as synthetic in metadata.",
                   "Re-run the bias scan and compare the ratio, not the score.",
                   "If augmentation is impossible, down-sample the dominant group and record "
                   "the decision — a smaller balanced corpus is defensible; a large skewed one is not."],
            impact="high", effort="high",
            risk="Never re-weight retrieval to mask this. It hides the imbalance from the metric "
                 "while leaving it in the evidence base, which is the failure mode Art. 10 exists "
                 "to prevent.",
            article="Art. 10", affects=e,
        )
    if check == "framing_skew":
        dim = f.check.split(".", 1)[-1]
        return Recipe(
            key=f"reframe_{dim}", title=f"Review how '{dim}' groups are described",
            rationale=(f"Groups are present in comparable numbers but described in measurably "
                       f"different language (gap {e.get('spread', '?')}). This is the form of "
                       f"bias that survives a representation audit and reaches the model intact."),
            steps=["Pull the chunks mentioning the negatively framed groups and read them.",
                   "Distinguish accurate domain language from editorialising in the source.",
                   "Where the source is the problem, replace the document; where the extraction is, "
                   "fix the pipeline.",
                   "Re-run and compare the sentiment spread per group."],
            impact="high", effort="high",
            risk="This one needs human reading. An automated rewrite of source documents destroys "
                 "the provenance that makes them evidence.",
            article="Art. 10", affects=e,
        )
    if check == "corpus_semantic_shift" or check == "corpus_drift":
        return Recipe(
            key="revalidate_retrieval", title="Re-run retrieval evaluation against the new corpus",
            rationale=("The corpus has moved. Recall and precision figures measured on the "
                       "baseline no longer describe what this system retrieves today."),
            steps=["Re-run the retrieval eval set against the current corpus.",
                   "Compare per-query recall to the baseline run, not just the mean.",
                   "If the shift was intended, promote this snapshot to the new baseline and say so.",
                   "If it was not, find the ingestion that caused it before promoting anything."],
            impact="medium", effort="medium",
            risk="Promoting a baseline hides the drift permanently. Only promote a change someone "
                 "decided to make.",
            article="Art. 15", affects=e,
        )
    if check == "bias_unassessable":
        dim = f.check.split(".", 1)[-1]
        return Recipe(
            key=f"extend_lexicon_{dim}", title=f"Extend the '{dim}' lexicon or confirm absence",
            rationale=(f"'{dim}' could not be scored. That is an open question, not a pass — the "
                       f"corpus either does not discuss it or discusses it in vocabulary the "
                       f"lexicon does not carry."),
            steps=["Read a sample of chunks and decide which of the two is true.",
                   "If the vocabulary is wrong, pass `extra_dimensions=` with your domain terms.",
                   "If the dimension genuinely does not apply, record that decision so the gap "
                   "is not re-litigated every quarter."],
            impact="low", effort="low",
            risk="None. But leaving it unresolved means the Fairness Score describes less of the "
                 "corpus than a reader will assume.",
            article="Art. 10", affects=e,
        )
    return None


def recommend(findings: Iterable[Finding]) -> list[Recipe]:
    """Ordered recipes, de-duplicated by key, highest leverage first."""
    out: dict[str, Recipe] = {}
    for f in findings:
        r = _for_finding(f)
        if r and r.key not in out:
            out[r.key] = r
    return sorted(out.values(), key=lambda r: (-r.leverage, r.key))


def to_markdown(recipes: list[Recipe], locale: str = "en") -> str:
    lo = i18n.resolve_locale(locale)
    t = lambda key, **kw: i18n.ui(key, lo, **kw)  # noqa: E731
    if not recipes:
        return t("remediation.none")
    lines = [f"# {t('remediation.title')}", "", t("remediation.intro"), ""]
    for i, r in enumerate(recipes, 1):
        lines += [
            f"## {i}. {r.title}", "",
            f"`{r.key}` · {t('remediation.impact')} **{r.impact}** · "
            f"{t('remediation.effort')} **{r.effort}**"
            + (f" · {r.article}" if r.article else ""), "",
            r.rationale, "", t("remediation.steps"), "",
        ]
        lines += [f"{j}. {step}" for j, step in enumerate(r.steps, 1)]
        lines += ["", f"> {t('remediation.risk')} {r.risk}"]
        if r.code:
            lines += ["", "```python", r.code, "```"]
        lines.append("")
    return "\n".join(lines)
