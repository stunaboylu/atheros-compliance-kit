import pytest

from atheros_kit.euact import REGULATION_VERSION, SystemSpec, classify, generate_dossier
from atheros_kit.euact.decision_tree import missing_required, to_spec
from atheros_kit.euact.transparency import (
    metadata_block,
    strip_watermark,
    verify_watermark,
    watermark,
)


@pytest.mark.parametrize("spec,tier", [
    (SystemSpec("A", "government", ["social scoring of citizens"]), "unacceptable"),
    (SystemSpec("B", "hr", ["cv screening"]), "high"),
    (SystemSpec("C", "retail", ["customer support chatbot"]), "limited"),
    (SystemSpec("D", "media", ["summarise internal documents"]), "minimal"),
])
def test_tier_ordering(spec, tier):
    assert classify(spec).tier == tier


def test_prohibited_beats_high_risk():
    """Art. 5 is evaluated first. A prohibited practice is not 'high risk'."""
    spec = SystemSpec("E", "law_enforcement", ["predictive policing", "biometric identification"])
    result = classify(spec)
    assert result.tier == "unacceptable" and result.articles == ["Art. 5"]


def test_minimal_verdict_states_what_it_rests_on():
    result = classify(SystemSpec("F", "media", ["summarise internal documents"]))
    assert result.evidence_basis == "no_indicator_matched"
    assert any("not the same as evidence of low risk" in lim for lim in result.limits)


def test_multiple_annex_categories_raise_a_grey_zone():
    result = classify(SystemSpec("G", "finance", ["credit scoring", "worker monitoring"]))
    assert result.tier == "high" and result.grey_zone
    assert result.confidence < 0.85


def test_high_risk_sector_without_a_use_case_is_unknown_not_minimal():
    """The failure mode this prevents: a vaguely described medical tool reported
    as minimal because the lexicon happened not to match."""
    result = classify(SystemSpec("H", "healthcare", [], "summarises clinical notes"))
    assert result.tier == "unknown" and result.grey_zone
    assert result.evidence_basis == "sector_only"


def test_emotion_recognition_is_contextual():
    """Prohibited at work and school (Art. 5(1)(f)); merely transparency-bound elsewhere."""
    assert classify(SystemSpec("I", "hr", ["emotion recognition workplace"])).tier == "unacceptable"
    assert classify(SystemSpec("J", "gaming", ["emotion recognition"])).tier == "limited"


def test_gpai_duties_are_additional_not_alternative():
    result = classify(SystemSpec("K", "hr", ["cv screening"], is_gpai=True))
    assert result.tier == "high"
    assert any(o["article"] == "Art. 53" for o in result.gpai_obligations)
    assert result.grey_zone   # both regimes apply — a human must confirm the split


def test_systemic_risk_duty_only_when_declared():
    plain = classify(SystemSpec("L", "media", ["generates text"], is_gpai=True))
    systemic = classify(SystemSpec("M", "media", ["generates text"], is_gpai=True,
                                   gpai_systemic_risk=True))
    assert not any(o["article"] == "Art. 55" for o in plain.gpai_obligations)
    assert any(o["article"] == "Art. 55" for o in systemic.gpai_obligations)


def test_every_classification_records_its_regulation_version():
    assert classify(SystemSpec("N", "retail", ["chatbot"])).regulation_version == REGULATION_VERSION


def test_obligations_name_the_module_that_evidences_them():
    for o in classify(SystemSpec("O", "hr", ["cv screening"])).obligations:
        assert o["evidence_source"]


# ── dossier ───────────────────────────────────────────────────────────────────
def test_dossier_prints_gaps_as_gaps():
    doc = generate_dossier(classify(SystemSpec("P", "hr", ["cv screening"])))
    assert doc.completeness == 0.0 and len(doc.gaps) == len(doc.sections)
    assert "This document is incomplete" in doc.to_markdown()


def test_evidence_alone_is_partial_never_covered():
    """Annex IV asks for an account of the system. Machine evidence supports one;
    it does not replace one."""
    doc = generate_dossier(classify(SystemSpec("Q", "hr", ["cv screening"])),
                           evidence={"rag.bias": {"fairness_score": 62}})
    section = next(s for s in doc.sections if s.key == "data_requirements")
    assert section.coverage.value == "partial"


def test_narrative_plus_evidence_is_covered():
    doc = generate_dossier(
        classify(SystemSpec("R", "hr", ["cv screening"])),
        evidence={"rag.bias": {"fairness_score": 90}, "rag.quality": {}, "rag.drift": {}},
        narrative={"data_requirements": "Datasets are described here."})
    section = next(s for s in doc.sections if s.key == "data_requirements")
    assert section.coverage.value == "covered"


def test_dossier_never_claims_certification():
    md = generate_dossier(classify(SystemSpec("S", "hr", ["cv screening"]))).to_markdown().lower()
    for banned in ("certified", "fully compliant", "guaranteed"):
        assert banned not in md


# ── transparency ──────────────────────────────────────────────────────────────
def test_watermark_round_trips_and_is_invisible():
    marked, _ = watermark("Quarterly summary.", system="Bot", model="m")
    assert marked.startswith("Quarterly summary.")
    assert verify_watermark(marked)["valid"]
    assert not verify_watermark(strip_watermark(marked))["present"]


def test_absent_marker_is_not_a_provenance_claim():
    result = verify_watermark("ordinary human text")
    assert result["present"] is False
    assert "does not establish" in result["note"]


def test_metadata_block_carries_a_hash_not_the_prompt():
    block = metadata_block(system="Bot", model="m", prompt_hash="abc123")
    assert block["prompt_hash"] == "abc123"
    assert "prompt" not in str(block).replace("prompt_hash", "")


# ── intake ────────────────────────────────────────────────────────────────────
def test_intake_coerces_human_answers():
    spec = to_spec({"name": "X", "sector": "hr", "use_cases": "cv screening, hiring",
                    "is_gpai": "yes", "eu_market": "no"})
    assert spec.use_cases == ["cv screening", "hiring"] and spec.is_gpai and not spec.eu_market


def test_missing_required_is_reported():
    assert set(missing_required({"name": "X"})) == {"sector", "use_cases"}
