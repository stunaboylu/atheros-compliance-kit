"""Module 3 — EU AI Act risk classification and compliance engine.

    from atheros_kit.euact import classify, SystemSpec, dossier

    result = classify(SystemSpec("TalentFlow", "hr", ["cv screening"]))
    result.tier            # "high"
    result.grey_zone       # ambiguity is reported, not smoothed over
    doc = dossier.generate(result, evidence={"rag.bias": bias_report})
    doc.completeness       # what is actually documented, gaps printed as gaps
"""
from . import decision_tree, dossier, transparency, vocabulary
from .classifier import RiskClassification, RiskTier, SystemSpec, classify
from .decision_tree import QUESTIONS, Question, relevant_questions, to_spec
from .dossier import Dossier
from .dossier import generate as generate_dossier
from .transparency import metadata_block, verify_watermark, watermark
from .vocabulary import REGULATION_VERSION

__all__ = [
    "classify", "SystemSpec", "RiskClassification", "RiskTier",
    "dossier", "generate_dossier", "Dossier",
    "transparency", "watermark", "verify_watermark", "metadata_block",
    "decision_tree", "QUESTIONS", "Question", "relevant_questions", "to_spec",
    "vocabulary", "REGULATION_VERSION",
]
