"""Licence verification.

Two things are being defended here. The first is that the free tier never meets a
licence check — an evaluating engineer who hits one concludes the product is
locked, and never comes back. The second is that our hand-written Ed25519
verifier is actually correct: an implementation with no test vectors is a guess,
and a signature check that silently accepts everything is worse than none.
"""
import base64
import json
from datetime import date, timedelta

import pytest

from atheros_kit.core import license as L
from atheros_kit.core.ed25519 import verify

#: RFC 8032 §7.1 — the canonical Ed25519 test vectors.
RFC8032 = [
    ("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a", "",
     "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc"
     "61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"),
    ("3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c", "72",
     "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15996e4"
     "58f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"),
    ("fc51cd8e6218a1a38da47ed00230f0580816ed13ba3303ac5deb911548908025", "af82",
     "6291d657deec24024827e69c3abe01a30ce548a284743a445e3680d7db5ac3ac18ff9b538d16f290a"
     "e67f760984dc6594a7c15e9716ed28dc027beceea1ec40a"),
]


@pytest.mark.parametrize("pk,msg,sig", RFC8032)
def test_rfc8032_vectors(pk, msg, sig):
    assert verify(bytes.fromhex(pk), bytes.fromhex(msg), bytes.fromhex(sig))


def test_a_tampered_message_does_not_verify():
    pk, _msg, sig = RFC8032[1]
    assert not verify(bytes.fromhex(pk), b"\x73", bytes.fromhex(sig))


def test_a_tampered_signature_does_not_verify():
    pk, msg, sig = RFC8032[1]
    assert not verify(bytes.fromhex(pk), bytes.fromhex(msg), bytes.fromhex(sig[:-2] + "ff"))


def test_the_wrong_key_does_not_verify():
    _pk, msg, sig = RFC8032[1]
    assert not verify(bytes.fromhex(RFC8032[0][0]), bytes.fromhex(msg), bytes.fromhex(sig))


@pytest.mark.parametrize("pk,msg,sig", [
    (b"too-short", b"m", b"x" * 64),
    (b"\x00" * 32, b"m", b"x" * 63),
    (b"\x00" * 32, b"m", b"\xff" * 64),          # not a point, non-canonical S
])
def test_malformed_inputs_return_false_rather_than_raising(pk, msg, sig):
    assert verify(pk, msg, sig) is False


def test_non_canonical_s_is_rejected():
    """S must be reduced mod L. An unreduced S makes signatures malleable."""
    pk, msg, sig = RFC8032[1]
    bad = bytes.fromhex(sig)[:32] + (b"\xff" * 32)
    assert not verify(bytes.fromhex(pk), bytes.fromhex(msg), bad)


# ── licence resolution ────────────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def clean_licence(monkeypatch):
    for var in ("ATHEROS_LICENCE", "ATHEROS_LICENSE",
                "ATHEROS_LICENCE_FILE", "ATHEROS_LICENSE_FILE"):
        monkeypatch.delenv(var, raising=False)
    L.set_current(None)
    yield
    L.set_current(None)


def test_no_licence_means_free_tier_and_no_network():
    lic = L.current(refresh=True)
    assert lic.tier == "free" and not lic.verified


def test_the_free_tier_never_needs_activation():
    """The load-bearing property: an evaluator must never meet a licence check."""
    lic = L.current(refresh=True)
    for capability in L.FREE_CAPABILITIES:
        assert lic.allows(capability)
        L.require(capability)          # must not raise


def _token(payload: dict) -> tuple[str, str]:
    """Sign a token exactly the way the licence service does."""
    pytest.importorskip("cryptography", reason="signing is a server-side concern")
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519

    def b64(b: bytes) -> str:
        return base64.urlsafe_b64encode(b).decode().rstrip("=")

    priv = ed25519.Ed25519PrivateKey.generate()
    pub = priv.public_key().public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw).hex()
    h = b64(json.dumps({"alg": "EdDSA", "typ": "JWT", "kid": "test"},
                       separators=(",", ":"), sort_keys=True).encode())
    p = b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    return f"{h}.{p}.{b64(priv.sign(f'{h}.{p}'.encode()))}", pub


def test_a_valid_team_token_unlocks_the_team_capabilities():
    token, pub = _token({"tier": "team", "account": "Acme BV", "seats": 12,
                         "exp_date": (date.today() + timedelta(days=90)).isoformat()})
    lic = L.parse(token, keys=(pub,))
    assert lic.verified and lic.tier == "team" and lic.seats == 12
    assert lic.allows("rag") and lic.allows("vendor")
    assert not lic.allows("airgap")            # enterprise only


def test_a_tampered_payload_is_refused():
    token, pub = _token({"tier": "team", "exp_date": "2099-01-01"})
    header, _payload, signature = token.split(".")
    forged_payload = base64.urlsafe_b64encode(
        json.dumps({"tier": "enterprise"}).encode()).decode().rstrip("=")
    lic = L.parse(f"{header}.{forged_payload}.{signature}", keys=(pub,))
    assert not lic.verified and lic.tier == "free"


def test_an_untrusted_key_is_refused():
    token, _pub = _token({"tier": "enterprise", "exp_date": "2099-01-01"})
    assert not L.parse(token, keys=("00" * 32,)).verified


def test_alg_none_is_refused():
    """The token never gets to nominate its own algorithm."""
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none"}).encode()).decode().rstrip("=")
    payload = base64.urlsafe_b64encode(
        json.dumps({"tier": "enterprise"}).encode()).decode().rstrip("=")
    lic = L.parse(f"{header}.{payload}.")
    assert not lic.verified and "EdDSA" in lic.reason


def test_an_expired_licence_degrades_to_free_and_says_so():
    token, pub = _token({"tier": "team", "account": "Acme",
                         "exp_date": (date.today() - timedelta(days=1)).isoformat()})
    lic = L.parse(token, keys=(pub,))
    assert lic.tier == "free" and "expired" in lic.reason
    assert lic.allows("guard")                 # the free tier still works


@pytest.mark.parametrize("token", ["", "not-a-token", "a.b", "a.b.c", "..", "x.y.z"])
def test_garbage_tokens_degrade_rather_than_raise(token):
    assert L.parse(token).tier == "free"


def test_status_states_the_enforcement_position_plainly():
    """A control that is not on must not be described as though it were."""
    s = L.status()
    assert s["enforced"] is L.ENFORCED
    if not L.ENFORCED:
        assert "enforcement is OFF" in s["note"]
