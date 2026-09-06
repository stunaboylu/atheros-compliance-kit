import pytest

from atheros_kit.core.audit import AuditTrail, set_default_trail
from atheros_kit.rag.connectors import Chunk


@pytest.fixture(autouse=True)
def isolated_trail(tmp_path):
    """Every test gets its own ledger.

    Autouse rather than opt-in: a test that forgets it would append to the
    developer's real .atheros/audit_trail.jsonl, and a test suite that writes to
    a production audit chain is its own compliance incident.
    """
    trail = AuditTrail(tmp_path / "audit_trail.jsonl")
    set_default_trail(trail)
    return trail


@pytest.fixture
def balanced_corpus():
    docs = []
    for i in range(30):
        docs.append(Chunk(f"m{i}", "He is a capable engineer and his work is reliable here.", [0.1] * 8))
        docs.append(Chunk(f"f{i}", "She is a capable engineer and her work is reliable here.", [0.1] * 8))
    return docs


@pytest.fixture
def skewed_corpus():
    docs = [Chunk(f"m{i}", "He is a trusted expert; his leadership is excellent and successful.", [0.1] * 8)
            for i in range(40)]
    docs += [Chunk(f"f{i}", "She was rejected as unreliable; her application was a risk and denied.", [0.1] * 8)
             for i in range(6)]
    return docs
