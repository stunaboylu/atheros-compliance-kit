import random

from atheros_kit.core.findings import harmonic_mean
from atheros_kit.rag import Chunk, RAGAuditEngine, assess_chunks, detect, score_corpus


# ── quality ───────────────────────────────────────────────────────────────────
def test_empty_corpus_scores_none_not_zero():
    report = assess_chunks([])
    assert report.score.value is None and report.score.band == "unmeasured"


def test_duplicates_counted_as_redundant_copies():
    chunks = [Chunk(f"c{i}", "Exactly the same passage repeated here again.", [0.1] * 4)
              for i in range(5)]
    report = assess_chunks(chunks)
    assert len(report.exact_duplicates) == 1 and report.duplicate_chunk_count == 4


def test_exact_duplicates_are_not_double_reported_as_near_duplicates():
    chunks = [Chunk(f"c{i}", "The quick brown fox jumps over the lazy dog every day.", [0.1] * 4)
              for i in range(10)]
    assert assess_chunks(chunks).near_duplicate_pairs == []


def test_formatting_differences_still_count_as_duplicates():
    a = Chunk("a", "The  Same   Passage\nHere", [0.1] * 4)
    b = Chunk("b", "the same passage here", [0.1] * 4)
    assert len(assess_chunks([a, b]).exact_duplicates) == 1


def test_mixed_dimensions_block_and_cap_the_score():
    chunks = [Chunk("a", "A perfectly ordinary chunk of text here.", [0.1] * 8),
              Chunk("b", "Another perfectly ordinary chunk of text.", [0.1] * 16)]
    report = assess_chunks(chunks)
    finding = next(f for f in report.findings if f.check == "mixed_embedding_dimensions")
    assert finding.action.value == "block" and report.score.value <= 40


def test_orphans_are_reported():
    report = assess_chunks([Chunk("a", "A chunk that never got an embedding at all.", None)])
    assert report.orphans == ["a"]


def test_pii_findings_carry_categories_not_values():
    report = assess_chunks([Chunk("a", "Reach ali@example.com about the invoice today.", [0.1] * 4)])
    finding = next(f for f in report.findings if f.check == "personal_data_in_corpus")
    assert finding.evidence["categories"] == ["EMAIL"]
    assert "ali@example.com" not in str(finding.evidence)


# ── bias ──────────────────────────────────────────────────────────────────────
def test_balanced_corpus_scores_well(balanced_corpus):
    report = score_corpus(balanced_corpus, dimensions=["gender"])
    assert report.fairness_score.value >= 85


def test_skewed_corpus_scores_badly(skewed_corpus):
    report = score_corpus(skewed_corpus, dimensions=["gender"])
    assert report.fairness_score.value < 50
    assert "gender:feminine" in report.affected_groups


def test_unmeasurable_corpus_scores_none_not_one_hundred():
    """Silence is not fairness. This is the single most important assertion here."""
    report = score_corpus([Chunk("a", "Vector databases store embeddings.", None)])
    assert report.fairness_score.value is None
    assert report.assessed_dimensions == []
    assert any("not a fair one" in lim for lim in report.limits)


def test_unassessable_dimensions_are_named(balanced_corpus):
    report = score_corpus(balanced_corpus)
    assert "gender" in report.assessed_dimensions
    assert "socioeconomic" in report.unassessable


def test_framing_skew_is_caught_when_counts_are_balanced():
    """The bias that survives a representation audit: equal numbers, unequal language."""
    docs = [Chunk(f"m{i}", "He is a trusted and capable expert with excellent leadership.", None)
            for i in range(30)]
    docs += [Chunk(f"f{i}", "She is a risk, unreliable and problematic, and was rejected.", None)
             for i in range(30)]
    report = score_corpus(docs, dimensions=["gender"])
    dim = report.dimensions[0]
    assert dim.representation_score >= 80        # counts are fine
    assert dim.sentiment_score < 50              # language is not
    assert any(f.check == "framing_skew.gender" for f in report.findings)


def test_harmonic_mean_propagates_a_zero():
    assert harmonic_mean([90, 90, 0]) == 0.0


# ── drift ─────────────────────────────────────────────────────────────────────
def _cone(center, n, seed, spread=0.3):
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        v = [c + rnd.gauss(0, spread) for c in center]
        mag = sum(x * x for x in v) ** 0.5
        out.append(Chunk(f"x{i}", "t", [x / mag for x in v]))
    return out


def test_same_distribution_is_stable():
    a = _cone([1, 0, 0, 0, 0, 0, 0, 0], 200, 1)
    b = _cone([1, 0, 0, 0, 0, 0, 0, 0], 200, 2)
    assert detect(a, b).verdict == "stable"


def test_moved_distribution_is_shifted():
    a = _cone([1, 0, 0, 0, 0, 0, 0, 0], 200, 1)
    b = _cone([0, 1, 0, 0, 0, 0, 0, 0], 200, 2)
    assert detect(a, b).verdict == "shifted"


def test_isotropic_vectors_do_not_false_positive():
    """A near-zero centroid has a meaningless direction: two samples from the SAME
    distribution scored a cosine near zero and were reported as shifted."""
    rnd = random.Random(5)
    a = [Chunk(f"a{i}", "t", [rnd.gauss(0, 1) for _ in range(16)]) for i in range(300)]
    b = [Chunk(f"b{i}", "t", [rnd.gauss(0, 1) for _ in range(16)]) for i in range(300)]
    report = detect(a, b)
    assert report.verdict == "stable" and not report.centroid_informative
    assert any("isotropic" in lim for lim in report.limits)


def test_missing_vectors_are_unmeasurable_not_stable():
    report = detect([Chunk("a", "t", None)], [Chunk("b", "t", None)])
    assert report.verdict == "unmeasurable" and report.score.value is None


def test_dimension_mismatch_blocks():
    report = detect([Chunk("a", "t", [0.1] * 8)], [Chunk("b", "t", [0.1] * 16)])
    assert report.verdict == "unmeasurable"
    assert report.findings[0].action.value == "block"


# ── engine ────────────────────────────────────────────────────────────────────
def test_engine_notes_that_drift_was_not_measured(balanced_corpus):
    audit = RAGAuditEngine(chunks=balanced_corpus, subject="kb").run()
    assert audit.drift is None
    assert any("No baseline snapshot" in lim for lim in audit.report.limits)


def test_engine_writes_to_the_chain(isolated_trail, balanced_corpus):
    RAGAuditEngine(chunks=balanced_corpus).run()
    assert isolated_trail.verify_chain() == (True, [])
    assert sum(1 for _ in isolated_trail.entries()) == 1


def test_recipes_are_ordered_by_leverage(skewed_corpus):
    audit = RAGAuditEngine(chunks=skewed_corpus).run()
    leverages = [r.leverage for r in audit.recipes]
    assert leverages == sorted(leverages, reverse=True)


def test_recipes_never_execute_anything(skewed_corpus):
    audit = RAGAuditEngine(chunks=skewed_corpus).run()
    assert "Nothing here runs automatically" in audit.remediation_markdown()


# ── non-English corpora ───────────────────────────────────────────────────────
# The tokeniser was ASCII-only, so every Turkish word was truncated at its first
# non-ASCII character: "kadın" tokenised as "kad" and matched nothing, while
# "erkek" (pure ASCII) matched fully. The dimension then reported a 40:0 split on
# a corpus that was 40:7 — an under-count in one direction is a bias finding the
# tool INVENTED, which is worse than not measuring at all. Found by running it.
def test_the_tokeniser_is_unicode_aware():
    from atheros_kit.rag.bias import _WORD_RE
    assert _WORD_RE.findall("kadın güvenilmez çünkü şüpheliydi") == [
        "kadın", "güvenilmez", "çünkü", "şüpheliydi"]


def _turkish(masculine: int, feminine: int, skewed: bool):
    good = "Bu erkek aday yetkin ve güvenilir bir mühendis; liderliği mükemmel ve başarılı oldu."
    bad = "Bu kadın aday güvenilmez bulunarak reddedildi; başvurusu riskli ve sorunlu görüldü."
    neutral = "Bu kadın aday yetkin ve güvenilir bir mühendis; liderliği mükemmel ve başarılı oldu."
    docs = [Chunk(f"m{i}", good, None) for i in range(masculine)]
    docs += [Chunk(f"f{i}", bad if skewed else neutral, None) for i in range(feminine)]
    return docs


def test_a_skewed_turkish_corpus_is_scored_not_skipped():
    report = score_corpus(_turkish(40, 7, skewed=True), dimensions=["gender"])
    dim = report.dimensions[0]
    assert dim.assessed
    assert dim.group_counts["feminine"] == 7 and dim.group_counts["masculine"] == 40
    assert report.fairness_score.value < 50
    assert "gender:feminine" in report.affected_groups


def test_a_balanced_turkish_corpus_scores_well():
    report = score_corpus(_turkish(30, 30, skewed=False), dimensions=["gender"])
    assert report.fairness_score.value >= 85


def test_turkish_stems_match_inflected_forms():
    """Turkish is agglutinative: kadının, kadınlar, kadına are all one mention."""
    docs = [Chunk(f"a{i}", "kadınların başvurusu yetkin ve güvenilir bulundu", None)
            for i in range(20)]
    docs += [Chunk(f"b{i}", "erkeklerin başvurusu yetkin ve güvenilir bulundu", None)
             for i in range(20)]
    report = score_corpus(docs, dimensions=["gender"])
    dim = report.dimensions[0]
    assert dim.group_counts["feminine"] == 20 and dim.group_counts["masculine"] == 20


def test_english_scoring_is_unchanged_by_the_unicode_tokeniser(skewed_corpus):
    report = score_corpus(skewed_corpus, dimensions=["gender"])
    assert report.dimensions[0].assessed and report.fairness_score.value < 50
