"""What the service promises, tested against the promises rather than the code.

README.md: one endpoint mints, one publishes the key; nothing here can break a
customer's build; the free tier never touches this; what is stored is the key
hash, tier, seats, account and salted fingerprints, nothing else.
"""
from __future__ import annotations

import json
from datetime import date, timedelta

import pytest

from app import main as service

pytestmark = pytest.mark.asyncio

KEY = "ATH-TEAM-0001-TESTKEY"


def _activate(key: str = KEY, fingerprint: str = "fp-machine-A-0123456789"):
    return {"licence_key": key, "machine_fingerprint": fingerprint}


async def test_health_and_readiness(client):
    assert (await client.get("/health")).json() == {"status": "ok"}
    ready = (await client.get("/health/ready")).json()
    assert ready["status"] == "ready"
    assert ready["signing_key"] == "atheros-2026"


async def test_docs_are_off_outside_debug(client):
    # A public OpenAPI page on the only service that holds a private key is a
    # map handed to anyone who asks.
    assert (await client.get("/docs")).status_code == 404


async def test_jwks_publishes_the_signing_key(client, public_key_hex):
    body = (await client.get("/v1/jwks")).json()
    assert len(body["keys"]) == 1
    k = body["keys"][0]
    assert (k["kty"], k["crv"], k["alg"], k["use"]) == ("OKP", "Ed25519", "EdDSA", "sig")
    assert k["kid"] == "atheros-2026"
    import base64
    raw = base64.urlsafe_b64decode(k["x"] + "=" * (-len(k["x"]) % 4))
    assert raw.hex() == public_key_hex


async def test_unknown_and_suspended_keys_get_the_same_answer(client, licence_factory):
    # Distinguishing "no such key" from "suspended" tells an attacker which
    # keys exist. One message for both, and the same status code.
    await licence_factory("ATH-SUSPENDED", status="suspended")
    unknown = await client.post("/v1/activate", json=_activate("ATH-NO-SUCH-KEY"))
    suspended = await client.post("/v1/activate", json=_activate("ATH-SUSPENDED"))
    assert unknown.status_code == suspended.status_code == 403
    assert unknown.json() == suspended.json()


async def test_an_expired_licence_says_so_and_points_at_the_free_tier(client, licence_factory):
    await licence_factory(days=-1)
    r = await client.post("/v1/activate", json=_activate())
    assert r.status_code == 403
    assert "expired" in r.json()["detail"]
    assert "free tier" in r.json()["detail"]


async def test_activation_mints_a_token_the_kit_verifies_offline(client, licence_factory, public_key_hex):
    """The critical path. The Kit ships a pure-Python Ed25519 verifier and a
    compiled-in public key; this service ships `cryptography` and the private
    key. They share no code. If this test fails, every paying customer is on
    the free tier and nobody is told."""
    await licence_factory(seats=5)
    r = await client.post("/v1/activate", json=_activate())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["tier"] == "team"
    assert body["seats"] == 5
    assert "will not stop your builds" in body["note"]

    from atheros_kit.core.license import TIERS, parse
    lic = parse(body["token"], keys=(public_key_hex,))
    assert lic.verified, lic.reason
    assert lic.tier == "team"
    assert lic.account == "Example B.V."
    assert lic.seats == 5
    assert TIERS["team"] <= lic.capabilities
    assert lic.expires == body["token_expires"]

    # And with the Kit's PLACEHOLDER key — what a customer has until the
    # production key is compiled in — the same token is refused, not accepted.
    placeholder = parse(body["token"])
    assert not placeholder.verified
    assert placeholder.tier == "free"


async def test_the_token_never_outlives_the_licence(client, licence_factory):
    await licence_factory(days=30)         # licence ends before the 90-day grace
    body = (await client.post("/v1/activate", json=_activate())).json()
    assert body["token_expires"] == body["expires"] == (date.today() + timedelta(days=30)).isoformat()

    await licence_factory("ATH-LONG", days=3650)
    body = (await client.post("/v1/activate", json=_activate("ATH-LONG"))).json()
    assert body["token_expires"] == (date.today() + timedelta(days=service.settings.token_days)).isoformat()


async def test_the_token_header_fixes_the_algorithm(client, licence_factory):
    await licence_factory()
    token = (await client.post("/v1/activate", json=_activate())).json()["token"]
    import base64
    h = token.split(".")[0]
    header = json.loads(base64.urlsafe_b64decode(h + "=" * (-len(h) % 4)))
    assert header == {"alg": "EdDSA", "kid": "atheros-2026", "typ": "JWT"}


async def test_reactivating_the_same_machine_does_not_consume_a_seat(client, licence_factory):
    await licence_factory(seats=1)
    service.settings.fingerprint_headroom = 0
    try:
        for _ in range(3):
            assert (await client.post("/v1/activate", json=_activate(fingerprint="fp-same-machine-1"))).status_code == 200
        other = await client.post("/v1/activate", json=_activate(fingerprint="fp-other-machine-2"))
        assert other.status_code == 409
        assert "rather raise a ceiling than block a release" in other.json()["detail"]
    finally:
        service.settings.fingerprint_headroom = 20


async def test_headroom_exists_for_ci_runners(client, licence_factory):
    # Seats are people; CI runners come and go. The ceiling is seats + headroom,
    # so a 1-seat licence still activates on a handful of ephemeral runners.
    await licence_factory(seats=1)
    service.settings.fingerprint_headroom = 3
    try:
        for i in range(4):   # 1 seat + 3 headroom
            assert (await client.post("/v1/activate", json=_activate(fingerprint=f"fp-runner-{i}-xxxx"))).status_code == 200
        assert (await client.post("/v1/activate", json=_activate(fingerprint="fp-runner-5-xxxx"))).status_code == 409
    finally:
        service.settings.fingerprint_headroom = 20


async def test_what_is_stored_and_what_is_not(client, licence_factory):
    """The row after an activation holds a salted fingerprint, not the
    fingerprint, and nothing the request did not send. README.md, "What is
    stored"."""
    from sqlalchemy import inspect, select
    from app.models import Licence

    row = await licence_factory()
    fp = "fp-machine-A-0123456789"
    await client.post("/v1/activate", json=_activate(fingerprint=fp))

    async with service.Session() as s:
        stored = (await s.execute(select(Licence).where(Licence.id == row.id))).scalar_one()
    assert stored.fingerprint_set() == {service._hash_fingerprint(fp)}
    assert fp not in stored.fingerprints
    assert stored.last_activation is not None
    assert KEY not in (stored.key_hash + stored.fingerprints + stored.account)

    columns = {c.key for c in inspect(Licence).mapper.column_attrs}
    assert columns == {"id", "key_hash", "tier", "seats", "account", "status", "expires",
                       "fingerprints", "created_at", "last_activation"}
    for forbidden in ("hostname", "ip", "repo", "repository", "project", "email"):
        assert not any(forbidden in c for c in columns), forbidden


async def test_the_salt_changes_the_stored_fingerprint(monkeypatch):
    # An unsalted fingerprint is a cross-customer join key. The service refuses
    # to boot without a salt (startup); here: the salt actually takes part.
    a = service._hash_fingerprint("fp-x")
    monkeypatch.setattr(service, "_FINGERPRINT_SALT", "another-salt")
    assert service._hash_fingerprint("fp-x") != a


async def test_boot_refuses_without_a_salt(monkeypatch):
    monkeypatch.setattr(service, "_FINGERPRINT_SALT", "")
    with pytest.raises(RuntimeError, match="ATHEROS_FINGERPRINT_SALT"):
        await service.startup()


async def test_request_validation_bounds_the_inputs(client):
    too_short = await client.post("/v1/activate", json={"licence_key": "x", "machine_fingerprint": "y"})
    assert too_short.status_code == 422
