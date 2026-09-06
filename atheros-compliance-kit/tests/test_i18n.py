"""Bilingual guarantees.

The rule these tests defend: switching language changes the LANGUAGE and nothing
else. A report that also changes its claims, its citations, or its verdicts when
translated is two different reports, and an auditor comparing a Turkish copy
against an English one would be comparing two documents rather than one.
"""
import re

import pytest

from atheros_kit.core import i18n
from atheros_kit.core.findings import Action, Finding, Severity
from atheros_kit.euact import SystemSpec, classify, generate_dossier
from atheros_kit.euact.vocabulary import GPAI_OBLIGATIONS, OBLIGATIONS
from atheros_kit.rag import RAGAuditEngine
from atheros_kit.vendor import CRITERIA, assess
from atheros_kit.vendor.criteria import QUESTIONS_TR

LOCALES = ("en", "tr")


# ── catalogue completeness ────────────────────────────────────────────────────
@pytest.mark.parametrize("catalogue,name", [
    (i18n.UI, "UI"), (i18n.NOTES, "NOTES"), (i18n.REASONING, "REASONING"),
])
def test_every_catalogue_entry_has_both_languages(catalogue, name):
    missing = [k for k, v in catalogue.items() if not all(v.get(lo) for lo in LOCALES)]
    assert not missing, f"{name} entries missing a translation: {missing}"


def test_every_finding_entry_has_both_languages():
    missing = [
        f"{check}.{field}"
        for check, fields in i18n.FINDINGS.items()
        for field, langs in fields.items()
        if not all(langs.get(lo) for lo in LOCALES)
    ]
    assert not missing, f"finding templates missing a translation: {missing}"


def test_every_vendor_criterion_has_a_turkish_question():
    assert {c.key for c in CRITERIA} <= set(QUESTIONS_TR)


def test_every_obligation_has_a_turkish_duty():
    duties = [o for obs in OBLIGATIONS.values() for o in obs] + list(GPAI_OBLIGATIONS)
    assert all(o.get("duty_tr") for o in duties)


# ── identifiers must survive translation ──────────────────────────────────────
def test_article_citations_are_never_translated():
    """`Art. 10` in Turkish is still `Art. 10`.

    A Turkish report that renders it as `Madde 10` cannot be matched against an
    English one, and an auditor comparing two runs of the same system needs the
    citation to be the same token in both.
    """
    result = classify(SystemSpec("X", "hr", ["cv screening"]))
    for locale in LOCALES:
        md = generate_dossier(result).to_markdown(locale)
        assert "Art. 10" in md and "Annex IV" in md
        assert "Madde 10" not in md


def test_check_identifiers_are_never_translated():
    a = assess("openai")
    md_en, md_tr = a.report.to_markdown(locale="en"), a.report.to_markdown(locale="tr")
    for check in {f.check for f in a.report.findings}:
        assert check in md_en and check in md_tr


def test_the_two_languages_report_the_same_facts():
    """Same tier, same confidence, same articles, same finding count."""
    result = classify(SystemSpec("Y", "finance", ["credit scoring", "worker monitoring"]))
    assert len(result.reasoning) == len(result.reasoning_tr)
    assert len(result.limits) == len(result.limits_tr)
    en, tr = generate_dossier(result).to_dict("en"), generate_dossier(result).to_dict("tr")
    assert en["classification"]["tier"] == tr["classification"]["tier"]
    assert en["classification"]["articles"] == tr["classification"]["articles"]
    assert en["completeness_pct"] == tr["completeness_pct"]


def test_numbers_are_identical_across_locales(skewed_corpus):
    audit = RAGAuditEngine(chunks=skewed_corpus).run()
    en, tr = audit.report.to_dict(locale="en"), audit.report.to_dict(locale="tr")
    assert [s["value"] for s in en["scores"]] == [s["value"] for s in tr["scores"]]
    assert len(en["findings"]) == len(tr["findings"])
    assert [f["severity"] for f in en["findings"]] == [f["severity"] for f in tr["findings"]]


# ── no untranslated leakage in a Turkish report ───────────────────────────────
#: Phrases that would mean a Turkish reader is silently getting English. Each one
#: was an actual leak found while wiring this up.
_ENGLISH_LEAKS = (
    "could not be established", "not confirmed as enabled", "No baseline snapshot",
    "lexicon-based", "Seed facts dated", "criteria could not be established",
    "This verdict rests on", "Limits of this assessment", "No findings were raised",
    "mention(s) across",
)


def test_turkish_reports_do_not_leak_english_prose(skewed_corpus):
    docs = [
        assess("openai", required_regions=["EU"]).report.to_markdown(locale="tr"),
        RAGAuditEngine(chunks=skewed_corpus).run().report.to_markdown(locale="tr"),
        generate_dossier(classify(SystemSpec("Z", "media", ["summarise notes"]))).to_markdown("tr"),
    ]
    for doc in docs:
        found = [p for p in _ENGLISH_LEAKS if p in doc]
        assert not found, f"untranslated English in a Turkish report: {found}"


def test_turkish_reports_never_claim_certification():
    """The banned-phrase lint applies in both languages.

    'belgelendirilmiş' and 'tamamen uyumlu' carry the same legal weight in Turkish
    as 'certified' and 'fully compliant' do in English.
    """
    banned_tr = ("belgelendirilmiştir", "tamamen uyumlu", "%100 uyumlu",
                 "uyum garantisi", "ek işlem gerekmez")
    docs = [
        generate_dossier(classify(SystemSpec("W", "hr", ["cv screening"]))).to_markdown("tr"),
        assess("openai").report.to_markdown(locale="tr"),
    ]
    for doc in docs:
        for phrase in banned_tr:
            assert phrase not in doc.lower(), f"{phrase!r} appears in a Turkish report"


# ── graceful degradation ──────────────────────────────────────────────────────
def test_unknown_locale_falls_back_to_english():
    assert i18n.resolve_locale("de") == "en"
    assert i18n.resolve_locale("tr-TR") == "tr"
    assert i18n.resolve_locale(None) == "en"


def test_a_finding_with_no_catalogue_entry_renders_in_english():
    f = Finding("some_future_check", Severity.LOW, "English detail", "rag", Action.FLAG)
    assert f.detail_in("tr") == "English detail"


def test_bad_params_fall_back_rather_than_raising():
    """A translation whose placeholders do not match must not break a compliance run."""
    f = Finding("duplicate_chunks", Severity.HIGH, "English detail", "rag", Action.FLAG,
                params={"wrong": "shape"})
    assert f.detail_in("tr") == "English detail"


def test_locale_is_recorded_on_every_report():
    a = assess("openai")
    assert a.report.to_dict(locale="tr")["locale"] == "tr"
    assert a.report.to_dict(locale="en")["locale"] == "en"


def test_html_declares_its_language():
    a = assess("openai")
    assert 'lang="tr"' in a.report.to_html(locale="tr")
    assert 'lang="en"' in a.report.to_html(locale="en")


def test_no_view_mixes_languages(skewed_corpus):
    """One locale per document: never mix languages inside one view.

    A Turkish report whose section headings are English is the failure this
    checks for — the headings are the first thing read.
    """
    md = RAGAuditEngine(chunks=skewed_corpus).run().report.to_markdown(locale="tr")
    headings = re.findall(r"^## (.+)$", md, re.MULTILINE)
    assert headings
    for heading in headings:
        assert heading in ("Skorlar", "Bulgular", "Kapsam", "Bu değerlendirmenin sınırları"), heading


def test_no_english_clause_survives_inside_a_turkish_finding():
    """The leak a bilingual report is actually judged on.

    The staleness finding embedded "(217 days old, past the 180-day window)" —
    an English parenthetical inside an otherwise Turkish sentence.
    """
    a = assess("openai", required_regions=["EU"])
    finding = next(f for f in a.report.findings if f.check == "vendor_facts_stale")
    tr = finding.detail_in("tr")
    for fragment in ("days old", "day window", "carry no date"):
        assert fragment not in tr, f"English leaked into a Turkish finding: {tr}"


def test_chain_violations_are_reported_in_the_requested_language(isolated_trail):
    """No view mixes languages — including the diagnostics."""
    isolated_trail.log("core", "e", {"a": 1})
    isolated_trail.path.write_text(isolated_trail.path.read_text().replace('"a": 1', '"a": 2'))
    _, en = isolated_trail.verify_chain(locale="en")
    _, tr = isolated_trail.verify_chain(locale="tr")
    assert "content altered" in en[0]
    assert "içerik değiştirilmiş" in tr[0] and "content altered" not in tr[0]
