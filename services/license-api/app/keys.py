"""Signing keys. The only place in the whole product that holds a private key.

Isolated to one module with one function so that replacing the local key with a
KMS/HSM signer is a substitution rather than a refactor — and so that a reader
auditing "where could our private key leak" has exactly one file to read.
"""
from __future__ import annotations

import base64
import json
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from .config import settings


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _private() -> ed25519.Ed25519PrivateKey:
    pem = settings.atheros_signing_key_pem
    if not pem:
        raise RuntimeError(
            "No signing key configured. Set ATHEROS_SIGNING_KEY_PEM. "
            "Refusing to fall back to an ephemeral key: tokens signed with one "
            "would verify nowhere, and the failure would surface as 'your licence "
            "is invalid' on a customer's machine rather than here."
        )
    key = serialization.load_pem_private_key(pem.encode("utf-8"), password=None)
    if not isinstance(key, ed25519.Ed25519PrivateKey):
        raise RuntimeError("ATHEROS_SIGNING_KEY_PEM is not an Ed25519 private key")
    return key


def public_key_hex() -> str:
    """The value that goes into the Kit's `TRUSTED_KEYS`."""
    raw = _private().public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return raw.hex()


def sign_token(payload: dict) -> str:
    """A compact JWS with a fixed algorithm.

    `alg` is written by us and never read from input. The Kit rejects anything
    that is not EdDSA for the same reason: a token that gets to nominate its own
    algorithm is how `alg: none` happens.
    """
    header = {"alg": "EdDSA", "typ": "JWT", "kid": settings.signing_key_id}
    h = _b64url(json.dumps(header, separators=(",", ":"), sort_keys=True).encode())
    p = _b64url(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    signature = _private().sign(f"{h}.{p}".encode("ascii"))
    return f"{h}.{p}.{_b64url(signature)}"


def jwks() -> dict:
    """Public keys, current first. Retired keys stay published through a rotation."""
    keys = [{"kty": "OKP", "crv": "Ed25519", "use": "sig", "alg": "EdDSA",
             "kid": settings.signing_key_id,
             "x": _b64url(bytes.fromhex(public_key_hex()))}]
    for i, hex_key in enumerate(settings.retired_public_keys):
        keys.append({"kty": "OKP", "crv": "Ed25519", "use": "sig", "alg": "EdDSA",
                     "kid": f"{settings.signing_key_id}-retired-{i}",
                     "x": _b64url(bytes.fromhex(hex_key))})
    return {"keys": keys}


def _generate() -> str:
    return ed25519.Ed25519PrivateKey.generate().private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "generate":
        print(_generate(), end="")
    else:
        print(public_key_hex())
