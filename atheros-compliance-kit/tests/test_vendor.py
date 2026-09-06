from atheros_kit.vendor import CRITERIA, STATUS_WEIGHT, assess, known_providers, lookup


def test_unknown_is_penalised_not_skipped():
    """The design decision the module rests on: a vendor cannot score well by
    declining to answer."""
    assert 0 < STATUS_WEIGHT["unknown"] < STATUS_WEIGHT["partial"]
    unknown_vendor = assess("nobody_has_heard_of_this")
    assert unknown_vendor.score.value < 30
    assert len(unknown_vendor.unknown_criteria) == len(CRITERIA)


def test_unknown_vendor_is_assessed_not_refused():
    """Refusing to assess an unseeded vendor tells the customer nothing. The
    correct output is a bad score and a list of questions to send."""
    a = assess("acme_llm")
    assert a.report.findings and a.score.value is not None


def test_customer_overrides_beat_the_seed():
    a = assess("openai", overrides={"criteria": {"iso_42001": "met"}})
    assert a.statuses["iso_42001"] == "met" and a.entry.customer_verified


def test_unverified_assessment_says_so():
    a = assess("openai")
    assert any("not what is configured on this account" in lim for lim in a.report.limits)


def test_critical_gap_blocks():
    a = assess("x", overrides={"criteria": {"gdpr_dpa": "not_met"}})
    finding = next(f for f in a.report.findings if f.check == "vendor_gap.gdpr_dpa")
    assert finding.action.value == "block" and finding.severity.value == "critical"


def test_eu_only_provider_is_residency_compliant():
    assert assess("mistral", required_regions=["EU"]).residency.verdict == "compliant"


def test_us_processing_needs_a_mechanism_not_assumed_adequacy():
    """'The US has adequacy' is true of the framework and false of any particular
    company until its DPF certification is checked."""
    a = assess("openai", required_regions=["EU"], dpf_certified=None)
    assert a.residency.verdict == "requires_scc"
    assert any(f.check == "dpf_certification_unverified" for f in a.report.findings)


def test_no_transfer_route_blocks():
    entry_overrides = {"regions": ["CN"], "transfer_mechanism": "unknown", "as_of": "2026-02-01"}
    a = assess("someprovider", overrides=entry_overrides, required_regions=["EU"])
    finding = next(f for f in a.report.findings if f.check == "transfer_no_mechanism")
    assert finding.action.value == "block"


def test_optout_available_is_not_optout_enforced():
    """The distinction the whole module exists for."""
    without = assess("openai")
    with_evidence = assess("openai", contract_flags={"training_optout_enabled": True,
                                                     "training_optout_contractual": True})
    assert without.optout.verdict == "available_not_evidenced"
    assert with_evidence.optout.verdict == "enforced"


def test_no_optout_at_all_blocks():
    a = assess("x", overrides={"training_optout_available": False})
    finding = next(f for f in a.report.findings if f.check == "training_optout_unavailable")
    assert finding.action.value == "block"


def test_stale_facts_are_flagged():
    a = assess("x", overrides={"as_of": "2020-01-01", "criteria": {"gdpr_dpa": "met"}})
    assert a.entry.stale
    assert any(f.check == "vendor_facts_stale" for f in a.report.findings)


def test_every_seeded_provider_is_dated():
    for key in known_providers():
        assert lookup(key).as_of != "unknown"


def test_assessment_lands_on_the_chain(isolated_trail):
    assess("openai")
    assert isolated_trail.verify_chain() == (True, [])


def test_declared_sccs_cover_a_non_adequate_country():
    """SCCs are the mechanism FOR countries without adequacy.

    Checking `no_route` first made the finding contradict its own wording — it
    said "no declared transfer mechanism" about a provider that declares SCCs,
    and returned non_compliant where the route in fact exists and needs evidencing.
    """
    a = assess("p", overrides={"regions": ["EU", "ASIA"], "transfer_mechanism": "scc",
                               "as_of": "2026-02-01"}, required_regions=["EU"])
    assert a.residency.verdict == "requires_scc"
    finding = next(f for f in a.report.findings if f.check == "transfer_requires_scc")
    assert finding.action.value == "flag"


def test_no_mechanism_at_all_is_still_non_compliant():
    a = assess("p", overrides={"regions": ["CN"], "transfer_mechanism": "unknown",
                               "as_of": "2026-02-01"}, required_regions=["EU"])
    assert a.residency.verdict == "non_compliant"
