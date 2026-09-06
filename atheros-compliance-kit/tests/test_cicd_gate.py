import json

from atheros_kit.cicd import gate
from atheros_kit.core.config import Config
from atheros_kit.euact import SystemSpec, classify
from atheros_kit.rag import RAGAuditEngine
from atheros_kit.vendor import assess


def _cfg(tmp_path, **fail_on):
    base = {"fairness_score_below": 70, "quality_score_below": 70, "vendor_score_below": 60,
            "drift_verdict_in": ["shifted"], "risk_tier_in": ["unacceptable"],
            "residency_verdict_in": ["non_compliant"], "guard_blocks_above": 0,
            "chain_violation": True}
    base.update(fail_on)
    return Config.load(report_dir=str(tmp_path / "reports"), fail_on=base)


def test_clean_run_passes(tmp_path, balanced_corpus):
    audit = RAGAuditEngine(chunks=balanced_corpus).run()
    result = gate.run(_cfg(tmp_path, quality_score_below=None, fairness_score_below=70),
                      rag_audit=audit)
    assert result.exit_code == 0 and result.passed


def test_low_fairness_fails_the_build(tmp_path, skewed_corpus):
    audit = RAGAuditEngine(chunks=skewed_corpus).run()
    result = gate.run(_cfg(tmp_path), rag_audit=audit)
    assert result.exit_code == 1
    assert any(o.name == "fairness_score" and o.status == "fail" for o in result.outcomes)


def test_unmeasured_score_fails_rather_than_passes(tmp_path):
    """A gate that goes green when the measurement breaks is worse than no gate."""
    from atheros_kit.rag import Chunk
    audit = RAGAuditEngine(chunks=[Chunk("a", "Vector databases store embeddings.", [0.1] * 4)]).run()
    result = gate.run(_cfg(tmp_path), rag_audit=audit)
    outcome = next(o for o in result.outcomes if o.name == "fairness_score")
    assert outcome.status == "unmeasured" and outcome.blocking and result.exit_code == 1


def test_skipped_modules_are_reported_not_hidden(tmp_path):
    result = gate.run(_cfg(tmp_path))
    skipped = [o.name for o in result.outcomes if o.status == "skipped"]
    assert {"rag_audit", "eu_ai_act", "vendor", "guard"} <= set(skipped)
    assert "check(s) did not run" in result.to_markdown()


def test_prohibited_tier_fails(tmp_path):
    result = gate.run(_cfg(tmp_path),
                      classification=classify(SystemSpec("X", "gov", ["social scoring"])))
    assert result.exit_code == 1


def test_grey_zone_is_unmeasured_certainty(tmp_path):
    result = gate.run(
        _cfg(tmp_path),
        classification=classify(SystemSpec("Y", "finance", ["credit scoring", "worker monitoring"])))
    assert any(o.name == "classification_certainty" and o.status == "unmeasured"
               for o in result.outcomes)


def test_broken_chain_fails(tmp_path, isolated_trail):
    isolated_trail.log("core", "e", {"a": 1})
    isolated_trail.path.write_text(isolated_trail.path.read_text().replace('"a": 1', '"a": 2'))
    result = gate.run(_cfg(tmp_path), trail=isolated_trail)
    assert any(o.name == "audit_chain" and o.status == "fail" for o in result.outcomes)


def test_vendor_residency_breach_fails(tmp_path):
    a = assess("p", overrides={"regions": ["CN"], "transfer_mechanism": "unknown",
                               "as_of": "2026-02-01"}, required_regions=["EU"])
    result = gate.run(_cfg(tmp_path), vendor_assessments=[a])
    assert result.exit_code == 1


def test_artefacts_are_written(tmp_path, balanced_corpus):
    result = gate.run(_cfg(tmp_path), rag_audit=RAGAuditEngine(chunks=balanced_corpus).run())
    report = json.loads((tmp_path / "reports" / "atheros-report.json").read_text())
    assert report["schema"] == "atheros.gate/v1"
    assert (tmp_path / "reports" / "atheros-summary.md").exists()
