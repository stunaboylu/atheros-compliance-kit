"""ISO/IEC 42001 evidence export.

The Kit produces records for five clauses and no more. This package collects
those records out of the hash-chained ledger and renders them as one document an
auditor can read — together with the chain verification, the clauses that have no
records, and the list of what the product does not cover at all.

Nothing here generates evidence. If a clause has no entries the pack says so.
"""
from .clauses import CLAUSES, NOT_COVERED, Clause
from .export import ClauseCoverage, EvidencePack, build_pack

__all__ = ["CLAUSES", "NOT_COVERED", "Clause", "ClauseCoverage", "EvidencePack", "build_pack"]
