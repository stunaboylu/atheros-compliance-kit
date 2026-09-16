"""The one table.

One row per licence, and the row holds exactly what README.md says it holds:
the key hash, the tier, the seat count, the account, the status, the expiry,
and the salted fingerprints that have activated. Nothing about what the
customer assessed — there is no column for it, so nothing can drift into one.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Licence(Base):
    __tablename__ = "licences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    #: SHA-256 of the licence key. The key itself is never stored: a database
    #: dump must not be a list of working licences.
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    #: "team" or "enterprise". The free tier has no row — it needs no activation,
    #: so this service never learns who evaluates.
    tier: Mapped[str] = mapped_column(String(16))
    seats: Mapped[int] = mapped_column(Integer)
    #: A name for the contract, e.g. the customer's company. Not a person.
    account: Mapped[str] = mapped_column(String(200))

    #: "active" or "suspended". `activate` answers both "no such key" and
    #: "suspended" with the same message; the distinction lives here only.
    status: Mapped[str] = mapped_column(String(16), default="active")
    expires: Mapped[date] = mapped_column(Date)

    #: HMAC-salted fingerprints, newline-joined, sorted. A text column rather
    #: than a second table: the set is small (seats + headroom), it is only ever
    #: read whole, and one row per licence keeps "what do we store" answerable
    #: by reading this file.
    fingerprints: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_activation: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def expired(self) -> bool:
        return self.expires < date.today()

    def fingerprint_set(self) -> set[str]:
        return {f for f in self.fingerprints.split("\n") if f}
