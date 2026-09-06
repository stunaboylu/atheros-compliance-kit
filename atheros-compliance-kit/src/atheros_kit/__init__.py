"""AtherosAI Compliance Kit.

Four modules over one core, each usable alone:

    atheros_kit.rag      RAG corpus quality, semantic drift, bias → Fairness Score
    atheros_kit.guard    third-party LLM guardrails: PII masking, injection defence
    atheros_kit.euact    EU AI Act classification and Annex IV dossier
    atheros_kit.vendor   vendor due diligence, residency, training opt-out
    atheros_kit.cicd     the gate that turns any of the above into an enforced control

The core is stdlib-only and every module has a deterministic path, so this
installs and runs in a CI image with no network, no vector-store driver, and no
model key. Where a model was configured and did not answer, the result says
`degraded` rather than quietly presenting the fallback as the real thing.

    from atheros_kit import classify, SystemSpec, GuardedClient, GuardPolicy

    classify(SystemSpec("TalentFlow", "hr", ["cv screening"])).tier   # "high"
"""
from .core import (
    Action,
    AtherosError,
    AuditTrail,
    Config,
    Coverage,
    Finding,
    Method,
    Report,
    Score,
    Severity,
    default_trail,
    resolve,
    warn_on_floating,
)
from .euact import RiskTier, SystemSpec, classify, generate_dossier, watermark
from .guard import CustomEntity, GuardedClient, GuardPolicy
from .rag import RAGAuditEngine, assess_chunks, score_corpus
from .vendor import assess as assess_vendor

__version__ = "1.0.0"

__all__ = [
    "__version__",
    # core
    "AuditTrail", "default_trail", "Config", "Report", "Finding", "Score",
    "Severity", "Action", "Method", "Coverage", "AtherosError", "resolve", "warn_on_floating",
    # modules
    "RAGAuditEngine", "assess_chunks", "score_corpus",
    "GuardedClient", "GuardPolicy", "CustomEntity",
    "classify", "SystemSpec", "RiskTier", "generate_dossier", "watermark",
    "assess_vendor",
]
