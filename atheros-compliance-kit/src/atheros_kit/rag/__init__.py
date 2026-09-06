"""Module 1 — advanced RAG and data-quality / bias engine.

    from atheros_kit.rag import RAGAuditEngine

    audit = RAGAuditEngine.from_store("chroma", collection_name="kb").run()
    audit.fairness_score          # 0-100, harmonic across assessed dimensions
    audit.quality_score           # duplicates, orphans, sizing, PII
    audit.bias.unassessable       # what could NOT be measured — read this one
    print(audit.remediation_markdown())
"""
from .bias import DIMENSIONS, BiasReport, DimensionResult, score_corpus
from .connectors import (
    ChromaConnector,
    Chunk,
    InMemoryConnector,
    MilvusConnector,
    PgVectorConnector,
    PineconeConnector,
    VectorStoreConnector,
    centroid,
    cosine,
    get_connector,
)
from .drift import DriftReport, detect, js_divergence, psi
from .engine import RAGAuditEngine, RAGAuditReport
from .quality import QualityReport, assess_chunks
from .remediation import Recipe, recommend
from .remediation import to_markdown as remediation_markdown

__all__ = [
    "RAGAuditEngine", "RAGAuditReport",
    "assess_chunks", "QualityReport",
    "score_corpus", "BiasReport", "DimensionResult", "DIMENSIONS",
    "detect", "DriftReport", "psi", "js_divergence",
    "recommend", "Recipe", "remediation_markdown",
    "Chunk", "get_connector", "VectorStoreConnector", "InMemoryConnector",
    "ChromaConnector", "PgVectorConnector", "PineconeConnector", "MilvusConnector",
    "cosine", "centroid",
]
