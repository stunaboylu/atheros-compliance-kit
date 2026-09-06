"""Vector-store connectors — read the corpus where it actually lives.

The interface is one method, `chunks()`, yielding a normalised `Chunk`. Every
store has a different client, a different pagination story and a different name
for "metadata"; none of that should reach the quality, drift or bias code, which
is why the normalisation happens here and exactly once.

All drivers are lazily imported and live in the `rag` extra. A CI image that only
runs the guard module must not be made to install `chromadb`.

The connector is **read-only by construction** — there is no write path in this
file. The Kit assesses a corpus; it does not mutate a customer's knowledge base.
`remediation` emits recipes for a human to run, deliberately.
"""
from __future__ import annotations

import hashlib
import math
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from ..core.errors import MissingDependencyError


@dataclass
class Chunk:
    id: str
    text: str
    vector: Sequence[float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    ingested_at: str | None = None

    @property
    def length(self) -> int:
        return len(self.text or "")

    @property
    def token_estimate(self) -> int:
        return max(1, self.length // 4)

    @property
    def fingerprint(self) -> str:
        """Normalised content hash — for exact-duplicate detection.

        Normalised on whitespace and case so that the same passage re-ingested
        with different formatting is caught. Two chunks that differ only in how a
        PDF extractor broke the lines are one duplicate, not two documents.
        """
        norm = " ".join((self.text or "").lower().split())
        return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]

    @property
    def shingles(self) -> set[str]:
        """5-word shingles, for near-duplicate detection via Jaccard overlap."""
        words = (self.text or "").lower().split()
        if len(words) < 5:
            return {" ".join(words)} if words else set()
        return {" ".join(words[i:i + 5]) for i in range(len(words) - 4)}


class VectorStoreConnector(Protocol):
    """Anything that can hand over a corpus, chunk by chunk."""

    name: str

    def chunks(self, limit: int | None = None) -> Iterator[Chunk]: ...

    def count(self) -> int | None: ...


@dataclass
class InMemoryConnector:
    """The reference implementation, and what tests and CI fixtures use.

    Also the escape hatch: a team with a store the Kit does not support reads it
    themselves and passes the chunks in. That path is first-class, not a fallback
    — it is why the assessment code never touches a driver.
    """

    documents: list[Chunk] = field(default_factory=list)
    name: str = "memory"

    @classmethod
    def from_texts(cls, texts: Iterable[str], *, vectors: Sequence[Sequence[float]] | None = None,
                   metadatas: Sequence[dict] | None = None, prefix: str = "doc") -> InMemoryConnector:
        docs = []
        for i, text in enumerate(texts):
            docs.append(Chunk(
                id=f"{prefix}-{i}",
                text=text,
                vector=list(vectors[i]) if vectors is not None and i < len(vectors) else None,
                metadata=dict(metadatas[i]) if metadatas is not None and i < len(metadatas) else {},
            ))
        return cls(documents=docs)

    def chunks(self, limit: int | None = None) -> Iterator[Chunk]:
        for i, c in enumerate(self.documents):
            if limit is not None and i >= limit:
                return
            yield c

    def count(self) -> int | None:
        return len(self.documents)


@dataclass
class ChromaConnector:
    collection_name: str
    path: str | None = None
    host: str | None = None
    port: int = 8000
    batch_size: int = 500
    name: str = "chroma"

    def _collection(self):
        try:
            import chromadb  # type: ignore
        except ImportError:
            raise MissingDependencyError("chromadb", "rag", "The Chroma connector") from None
        client = (chromadb.HttpClient(host=self.host, port=self.port) if self.host
                  else chromadb.PersistentClient(path=self.path or "./chroma_db"))
        return client.get_collection(self.collection_name)

    def count(self) -> int | None:
        return self._collection().count()

    def chunks(self, limit: int | None = None) -> Iterator[Chunk]:
        col = self._collection()
        total = limit if limit is not None else (col.count() or 0)
        fetched = 0
        while fetched < total:
            take = min(self.batch_size, total - fetched)
            page = col.get(limit=take, offset=fetched,
                           include=["documents", "metadatas", "embeddings"])
            ids = page.get("ids") or []
            if not ids:
                return
            docs = page.get("documents") or [None] * len(ids)
            metas = page.get("metadatas") or [{}] * len(ids)
            embs = page.get("embeddings")
            for i, cid in enumerate(ids):
                meta = metas[i] or {}
                yield Chunk(
                    id=str(cid), text=docs[i] or "",
                    vector=list(embs[i]) if embs is not None and i < len(embs) and embs[i] is not None else None,
                    metadata=dict(meta),
                    ingested_at=meta.get("ingested_at") or meta.get("created_at"),
                )
            fetched += len(ids)


@dataclass
class PgVectorConnector:
    """PostgreSQL + pgvector. The synchronous driver on purpose — every call site
    in this module is synchronous, and an async engine here would mean wrapping
    each of them in `asyncio.to_thread` for no gain."""

    dsn: str
    table: str
    id_column: str = "id"
    text_column: str = "content"
    vector_column: str = "embedding"
    metadata_column: str | None = "metadata"
    timestamp_column: str | None = "created_at"
    name: str = "pgvector"

    def _connect(self):
        try:
            import psycopg2  # type: ignore
            import psycopg2.extras  # type: ignore
        except ImportError:
            raise MissingDependencyError("psycopg2-binary", "rag", "The pgvector connector") from None
        try:
            from pgvector.psycopg2 import register_vector  # type: ignore
        except ImportError:
            raise MissingDependencyError("pgvector", "rag", "The pgvector connector") from None
        conn = psycopg2.connect(self.dsn)
        register_vector(conn)
        return conn

    def _ident(self, name: str) -> str:
        """Quote an identifier. These come from a config file the operator wrote,
        not from user input — but a table name that lands in SQL unquoted is a
        habit worth not having in a security product."""
        return '"' + name.replace('"', '""') + '"'

    def count(self) -> int | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT count(*) FROM {self._ident(self.table)}")
            return cur.fetchone()[0]

    def chunks(self, limit: int | None = None) -> Iterator[Chunk]:
        cols = [self._ident(self.id_column), self._ident(self.text_column),
                self._ident(self.vector_column)]
        if self.metadata_column:
            cols.append(self._ident(self.metadata_column))
        if self.timestamp_column:
            cols.append(self._ident(self.timestamp_column))
        sql = f"SELECT {', '.join(cols)} FROM {self._ident(self.table)}"
        if limit:
            sql += f" LIMIT {int(limit)}"
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql)
            for row in cur:
                meta = row[3] if self.metadata_column and len(row) > 3 else {}
                ts = row[-1] if self.timestamp_column else None
                yield Chunk(
                    id=str(row[0]), text=row[1] or "",
                    vector=list(row[2]) if row[2] is not None else None,
                    metadata=dict(meta) if isinstance(meta, dict) else {},
                    ingested_at=ts.isoformat() if isinstance(ts, datetime) else (str(ts) if ts else None),
                )


@dataclass
class PineconeConnector:
    index_name: str
    namespace: str = ""
    api_key: str | None = None
    batch_size: int = 100
    name: str = "pinecone"

    def _index(self):
        try:
            from pinecone import Pinecone  # type: ignore
        except ImportError:
            raise MissingDependencyError("pinecone", "rag", "The Pinecone connector") from None
        import os
        return Pinecone(api_key=self.api_key or os.environ.get("PINECONE_API_KEY")).Index(self.index_name)

    def count(self) -> int | None:
        stats = self._index().describe_index_stats()
        ns = (stats.get("namespaces") or {}).get(self.namespace or "", {})
        return ns.get("vector_count") or stats.get("total_vector_count")

    def chunks(self, limit: int | None = None) -> Iterator[Chunk]:
        index = self._index()
        yielded, pagination = 0, None
        while True:
            page = index.list_paginated(namespace=self.namespace, limit=self.batch_size,
                                        pagination_token=pagination)
            ids = [v["id"] if isinstance(v, dict) else v.id for v in (page.vectors or [])]
            if not ids:
                return
            fetched = index.fetch(ids=ids, namespace=self.namespace)
            for cid, vec in (fetched.vectors or {}).items():
                meta = dict(getattr(vec, "metadata", None) or {})
                yield Chunk(
                    id=str(cid), text=meta.get("text") or meta.get("content") or "",
                    vector=list(getattr(vec, "values", []) or []), metadata=meta,
                    ingested_at=meta.get("ingested_at"),
                )
                yielded += 1
                if limit and yielded >= limit:
                    return
            pagination = getattr(page.pagination, "next", None) if page.pagination else None
            if not pagination:
                return


@dataclass
class MilvusConnector:
    collection_name: str
    uri: str = "http://localhost:19530"
    text_field: str = "text"
    vector_field: str = "vector"
    batch_size: int = 500
    name: str = "milvus"

    def _client(self):
        try:
            from pymilvus import MilvusClient  # type: ignore
        except ImportError:
            raise MissingDependencyError("pymilvus", "rag", "The Milvus connector") from None
        return MilvusClient(uri=self.uri)

    def count(self) -> int | None:
        stats = self._client().get_collection_stats(self.collection_name)
        return int(stats.get("row_count", 0)) or None

    def chunks(self, limit: int | None = None) -> Iterator[Chunk]:
        client = self._client()
        offset, yielded = 0, 0
        while True:
            rows = client.query(
                collection_name=self.collection_name, filter="", limit=self.batch_size,
                offset=offset, output_fields=["*"],
            )
            if not rows:
                return
            for row in rows:
                yield Chunk(
                    id=str(row.get("id") or row.get("pk") or f"milvus-{offset}"),
                    text=row.get(self.text_field, "") or "",
                    vector=list(row.get(self.vector_field) or []) or None,
                    metadata={k: v for k, v in row.items()
                              if k not in (self.text_field, self.vector_field)},
                )
                yielded += 1
                if limit and yielded >= limit:
                    return
            offset += len(rows)


_REGISTRY = {
    "memory": InMemoryConnector,
    "chroma": ChromaConnector,
    "pgvector": PgVectorConnector,
    "pinecone": PineconeConnector,
    "milvus": MilvusConnector,
}


def get_connector(kind: str, **config: Any) -> VectorStoreConnector:
    """`get_connector("chroma", collection_name="regulations", path="./chroma_db")`."""
    try:
        cls = _REGISTRY[kind]
    except KeyError:
        raise ValueError(
            f"Unknown vector store {kind!r}. Known: {', '.join(sorted(_REGISTRY))}. "
            f"For anything else, read the corpus yourself and pass it as "
            f"InMemoryConnector.from_texts(...) — that path is fully supported."
        ) from None
    return cls(**config)  # type: ignore[arg-type]


# ── vector maths (pure stdlib; numpy is an accelerator, never a requirement) ──
def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return 0.0 if na == 0 or nb == 0 else dot / (na * nb)


def centroid(vectors: Sequence[Sequence[float]]) -> list[float]:
    vectors = [v for v in vectors if v]
    if not vectors:
        return []
    dim = len(vectors[0])
    # A ragged batch means two embedding models wrote into one collection. That
    # is a real and serious corpus defect, so it is surfaced by the caller rather
    # than silently truncated here.
    usable = [v for v in vectors if len(v) == dim]
    return [sum(v[i] for v in usable) / len(usable) for i in range(dim)]
