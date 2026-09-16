"""The licence service.

Two endpoints. Nothing here can break a customer's build: the token it issues is
verified offline for 90 days, so this service being down means a customer cannot
RENEW, not that they cannot RUN.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import settings
from .keys import jwks, public_key_hex, sign_token
from .models import Base, Licence

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
Session = async_sessionmaker(engine, expire_on_commit=False)

#: Salt for fingerprint hashing. Without it, a fingerprint is a stable global
#: identifier for a machine and a database dump becomes a cross-customer join key.
_FINGERPRINT_SALT = os.environ.get("ATHEROS_FINGERPRINT_SALT", "")


async def startup() -> None:
    # Fail loudly at boot rather than on the first customer request. A signing key
    # discovered missing during an activation surfaces to the customer as "your
    # licence is invalid", which is both wrong and the hardest kind of bug to
    # attribute.
    public_key_hex()
    if not _FINGERPRINT_SALT:
        raise RuntimeError(
            "ATHEROS_FINGERPRINT_SALT is not set. Without it, stored fingerprints are "
            "unsalted hashes of stable machine ids — a cross-customer join key in a "
            "database that is supposed to hold nothing of the sort."
        )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await startup()
    yield
    await engine.dispose()


app = FastAPI(
    title="AtherosAI licence service",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,   # never in production
    lifespan=lifespan,
)


async def get_session() -> AsyncSession:
    async with Session() as session:
        yield session


class ActivateRequest(BaseModel):
    licence_key: str = Field(min_length=8, max_length=200)
    #: A salted hash of a stable machine id, computed by the CLIENT. The raw id
    #: never leaves the customer's machine.
    machine_fingerprint: str = Field(min_length=8, max_length=128)


class ActivateResponse(BaseModel):
    token: str
    tier: str
    expires: date
    token_expires: date
    seats: int
    note: str


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.strip().encode("utf-8")).hexdigest()


def _hash_fingerprint(fingerprint: str) -> str:
    return hmac.new(_FINGERPRINT_SALT.encode(), fingerprint.encode(), hashlib.sha256).hexdigest()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/health/ready")
async def ready(session: AsyncSession = Depends(get_session)) -> dict:
    await session.execute(select(1))
    return {"status": "ready", "signing_key": settings.signing_key_id}


@app.get("/v1/jwks")
async def get_jwks() -> dict:
    """Public keys. Published so a customer can verify a token independently of us."""
    return jwks()


@app.post("/v1/activate", response_model=ActivateResponse)
async def activate(
    body: ActivateRequest,
    session: AsyncSession = Depends(get_session),
) -> ActivateResponse:
    key_hash = _hash_key(body.licence_key)
    result = await session.execute(select(Licence).where(Licence.key_hash == key_hash))
    licence = result.scalar_one_or_none()

    # One message for "no such key" and "suspended": distinguishing them tells an
    # attacker which keys exist.
    if licence is None or licence.status != "active":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Licence key is not active.")
    if licence.expired:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"Licence expired on {licence.expires}. Renew at info@atherosai.com — the free "
            f"tier continues to work with no activation.",
        )

    fingerprint = _hash_fingerprint(body.machine_fingerprint)
    seen = licence.fingerprint_set()
    if fingerprint not in seen:
        ceiling = licence.seats + settings.fingerprint_headroom
        if len(seen) >= ceiling:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"This licence has activated on {len(seen)} machines, above the {ceiling} "
                f"allowed for {licence.seats} seats. If these are CI runners rather than "
                f"people, contact info@atherosai.com and we will raise it — we would rather "
                f"raise a ceiling than block a release.",
            )
        seen.add(fingerprint)
        licence.fingerprints = "\n".join(sorted(seen))

    licence.last_activation = datetime.now(timezone.utc)
    await session.commit()

    # The token expires at the earlier of the grace window and the licence itself,
    # so a token can never outlive what it attests to.
    token_expiry = min(date.today() + timedelta(days=settings.token_days), licence.expires)
    token = sign_token({
        "tier": licence.tier,
        "account": licence.account,
        "seats": licence.seats,
        "exp_date": token_expiry.isoformat(),
        "iat_date": date.today().isoformat(),
        "iss": "atheros.ai",
    })
    return ActivateResponse(
        token=token,
        tier=licence.tier,
        expires=licence.expires,
        token_expires=token_expiry,
        seats=licence.seats,
        note=(
            f"Verified offline for {(token_expiry - date.today()).days} days. This service "
            f"being unreachable will not stop your builds; re-activate before "
            f"{token_expiry.isoformat()}."
        ),
    )
