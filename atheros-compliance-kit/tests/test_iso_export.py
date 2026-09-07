"""The ISO/IEC 42001 evidence export.

This command produces the one artefact that leaves the customer's control and is
read by someone who cannot inspect the tool: an auditor. Every test here defends
the same property from a different side — the document must never read as
broader than the ledger it was built from.

The export also settled a contradiction the rest of the product had been
carrying. `AuditTrail.CLAUSES` tags `euact` entries `6.1.2`, while the public
documentation said clauses 4-7 were out of scope. Both could not be true. The
resolution is `kind="input"`: the classification is an input to clause 6.1.2, not
a discharge of it, and the pack says so wherever that clause appears.
"""
import json

import pytest

from atheros_kit.core.audit import AuditTrail
from atheros_kit.iso import build_pack
from atheros_kit.iso import clauses as K
from atheros_kit.iso.export import MAX_LISTED, write_pack


@pytest.fixture
def ledger(tmp_path):
    return AuditTrail(tmp_path / "ledger.jsonl")


@pytest.fixture
def populated(ledger):
    ledger.log("rag", "corpus_audit", {"chunks": 40})
    ledger.log("guard", "guarded_call", {"masked": 2})
    ledger.log("vendor", "assessment", {"provider": "openai"})
    ledger.log("euact", "classification", {"tier": "high"})
    ledger.log("cicd", "gate", {"exit_code": 0})
    return ledger


# ── the catalogue and the ledger must agree ──────────────────────────────────
def test_every_ledger_module_maps_to_a_clause():
    """Drift between the two would silently drop a module's entries.

    `AuditTrail.CLAUSES` decides what is written onto an entry; `MODULE_CLAUSE`
    decides where the export files it. A module added to one and not the other
    produces entries that exist in the chain and appear under no clause — the
    quietest possible way for evidence to go missing.
    """
    assert set(AuditTrail.CLAUSES) == set(K.MODULE_CLAUSE)


def test_the_clause_numbers_agree_with_the_tags_written_onto_entries():
    for module, tag in AuditTrail.CLAUSES.items():
        assert tag.startswith(K.MODULE_CLAUSE[module]), (module, tag)


# ── nothing is ever shown as broader than it is ──────────────────────────────
def test_a_clause_with_no_records_is_never_shown_as_covered(ledger):
    ledger.log("rag", "corpus_audit", {"chunks": 1})
    pack = build_pack(ledger)
    empty = [c for c in pack.coverage if not c.entries]
    assert {c.clause.number for c in empty} == {"6.1.2", "8.3", "8.5", "9.1"}
    assert all(c.status == "no_records" for c in empty)
    assert pack.evidenced == 1
    md = pack.to_markdown()
    assert "**no records**" in md and "No records." in md


def test_the_eu_act_classification_is_an_input_not_a_discharge(populated):
    """Clause 6.1.2 has an entry, and must still not be counted as evidenced."""
    pack = build_pack(populated)
    six = next(c for c in pack.coverage if c.clause.number == "6.1.2")
    assert six.entries and six.status == "input_only"
    assert pack.evidenced == 4                      # not 5
    assert "input" in pack.to_markdown() and "not a discharge of it" in pack.to_markdown()


@pytest.mark.parametrize("locale,needle", [
    ("en", "internal audit programme"), ("tr", "iç denetim programı"),
    ("en", "Statement of Applicability"), ("tr", "Uygulanabilirlik Bildirimi"),
])
def test_the_not_covered_section_is_always_rendered(populated, locale, needle):
    """There is no flag to suppress it, and no ledger state that omits it.

    A pack listing five clauses and stopping invites the reader to supply the
    rest of the standard from imagination.
    """
    assert needle in build_pack(populated).to_markdown(locale)


def test_a_pack_from_an_empty_ledger_still_names_what_is_not_covered(ledger):
    assert "internal audit programme" in build_pack(ledger).to_markdown()


def test_the_pack_never_claims_compliance(populated):
    md = build_pack(populated).to_markdown().lower()
    assert "not a statement of compliance" in md
    for banned in ("fully compliant", "certified", "iso 42001 compliance"):
        assert banned not in md


# ── a broken chain is loud, early, and fails ─────────────────────────────────
def test_a_broken_chain_warns_above_the_evidence(populated):
    """Placement is the control. A warning under the tables is read after them."""
    populated.path.write_text(
        populated.path.read_text().replace('"chunks": 40', '"chunks": 41'))
    pack = build_pack(populated)
    md = pack.to_markdown()
    assert not pack.chain_intact
    assert md.index("does not verify") < md.index("## Clause coverage")


def test_a_pack_from_a_broken_chain_is_not_fit_to_hand_over(populated):
    populated.path.write_text(populated.path.read_text().replace('"masked": 2', '"masked": 3'))
    pack = build_pack(populated)
    assert not pack.fit_to_hand_over
    assert pack.to_dict()["chain_intact"] is False


def test_an_empty_ledger_is_not_a_successful_export(ledger):
    """Zero evidence rendered as a green exit is the failure this product hates."""
    pack = build_pack(ledger)
    assert pack.total_entries == 0 and not pack.fit_to_hand_over
    assert "ledger is empty" in pack.to_markdown()


def test_entries_from_an_unknown_module_are_counted_not_dropped(ledger):
    """A module this file does not know about is a gap HERE, and must show as one."""
    ledger.log("rag", "corpus_audit", {"n": 1})
    ledger.log("futuremodule", "event", {"n": 2})
    pack = build_pack(ledger)
    assert pack.total_entries == 2 and pack.unattributed == 1
    assert "this export does not map to a clause" in pack.to_markdown()


# ── the document is auditable on its own terms ───────────────────────────────
def test_the_pack_is_a_pure_function_of_the_ledger(populated):
    """No generation timestamp, no run id: an auditor can re-run and diff.

    A document that differs on every run cannot be checked by re-running it,
    which removes the cheapest verification the reader has.
    """
    assert build_pack(populated).to_markdown() == build_pack(populated).to_markdown()


def test_the_pack_pins_the_chain_head(populated):
    last = list(populated.entries())[-1]["hash"]
    pack = build_pack(populated)
    assert pack.chain_head == last
    assert last[:16] in pack.to_markdown()


def test_a_capped_record_list_states_the_remainder(ledger):
    """A cap that is not reported reads as 'that was all of them'."""
    for i in range(MAX_LISTED + 7):
        ledger.log("rag", "corpus_audit", {"n": i})
    md = build_pack(ledger).to_markdown()
    assert md.count("| `rag` |") == MAX_LISTED
    assert "7 further record(s)" in md


def test_every_row_can_be_traced_to_the_ledger_by_digest(populated):
    md = build_pack(populated).to_markdown()
    for entry in populated.entries():
        assert entry["hash"][:12] in md


# ── both languages say the same thing ────────────────────────────────────────
def test_turkish_keeps_the_clause_numbers_and_the_boundary(populated):
    md = build_pack(populated).to_markdown("tr")
    for number in ("6.1.2", "8.3", "8.4", "8.5", "9.1"):
        assert number in md
    assert "uygunluk beyanı ya da belgelendirme değildir" in md
    assert "yalnızca girdi" in md


def test_neither_language_omits_a_clause(populated):
    en, tr = build_pack(populated).to_dict("en"), build_pack(populated).to_dict("tr")
    assert [c["number"] for c in en["clauses"]] == [c["number"] for c in tr["clauses"]]
    assert [c["status"] for c in en["clauses"]] == [c["status"] for c in tr["clauses"]]
    assert len(en["not_covered"]) == len(tr["not_covered"])


def test_the_evidence_pack_is_a_paid_capability():
    """The chain is free; the auditor-facing artefact built from it is not.

    Stated as a test because the free tier is a promise: an evaluator must never
    meet a licence check, so anything moved OUT of the free set is a deliberate
    commercial decision rather than a default.
    """
    from atheros_kit.core.license import FREE_CAPABILITIES, TIERS

    assert "iso.export" not in FREE_CAPABILITIES
    assert "iso.export" in TIERS["team"] and "iso.export" in TIERS["enterprise"]
    assert "audit" in FREE_CAPABILITIES          # the ledger itself stays free


# ── the command ──────────────────────────────────────────────────────────────
def test_write_pack_writes_both_formats(populated, tmp_path):
    written = write_pack(build_pack(populated), tmp_path / "out", "en")
    assert {p.name for p in written} == {"iso-42001-evidence.md", "iso-42001-evidence.json"}
    doc = json.loads((tmp_path / "out" / "iso-42001-evidence.json").read_text())
    assert doc["schema"] == "atheros.iso42001-evidence/v1"
    assert doc["fit_to_hand_over"] is True and len(doc["clauses"]) == 5


@pytest.mark.parametrize("locale", ["en", "tr"])
def test_cli_exits_zero_on_a_usable_pack(populated, tmp_path, locale):
    from atheros_kit.cli import main
    assert main(["iso", "export", "--lang", locale, "--file", str(populated.path),
                 "--out", str(tmp_path / locale)]) == 0


def test_cli_exits_one_on_an_empty_ledger(tmp_path):
    from atheros_kit.cli import main
    assert main(["iso", "export", "--file", str(tmp_path / "none.jsonl"),
                 "--out", str(tmp_path / "o")]) == 1


def test_cli_exits_one_on_a_broken_chain_but_still_writes_the_pack(populated, tmp_path):
    """Refusing to write would destroy the evidence of which entries changed."""
    from atheros_kit.cli import main
    populated.path.write_text(populated.path.read_text().replace('"exit_code": 0', '"exit_code": 1'))
    out = tmp_path / "o"
    assert main(["iso", "export", "--file", str(populated.path), "--out", str(out)]) == 1
    assert "does not verify" in (out / "iso-42001-evidence.md").read_text()
