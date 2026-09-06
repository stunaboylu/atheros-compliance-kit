"""Ed25519 signature VERIFICATION, in pure Python (RFC 8032, §5.1.7).

Why this exists rather than a `cryptography` dependency: `atheros_kit.core` is
stdlib-only, and that promise is what lets `pip install atheros-compliance-kit`
succeed in a locked-down CI image. Making licence verification pull in a compiled
crypto library would break it for every customer, including the free-tier ones
who never need a licence at all.

**Verification only.** There is no key generation and no signing here, and there
never should be: this module handles public keys and public signatures, so the
timing-independence that a constant-time implementation buys protects nothing
that is secret. Signing happens on the licence server, with a real crypto
library, against a private key this codebase never sees.

Checked against the RFC 8032 §7.1 test vectors in `tests/test_license.py`. A
hand-written implementation with no test vectors is not an implementation, it is
a guess, and a licence check that silently accepts everything is worse than none.
"""
from __future__ import annotations

import hashlib

# Curve25519 / edwards25519 domain parameters (RFC 8032 §5.1).
_P = 2 ** 255 - 19
_L = 2 ** 252 + 27742317777372353535851937790883648493
_D = -121665 * pow(121666, _P - 2, _P) % _P
_I = pow(2, (_P - 1) // 4, _P)          # sqrt(-1) mod p


def _sha512(data: bytes) -> bytes:
    return hashlib.sha512(data).digest()


def _x_recover(y: int) -> int:
    """Recover x from y on the curve, choosing the even root (RFC 8032 §5.1.3)."""
    xx = (y * y - 1) * pow(_D * y * y + 1, _P - 2, _P)
    x = pow(xx, (_P + 3) // 8, _P)
    if (x * x - xx) % _P != 0:
        x = (x * _I) % _P
    if x % 2 != 0:
        x = _P - x
    return x


_BY = 4 * pow(5, _P - 2, _P) % _P
_B = (_x_recover(_BY) % _P, _BY, 1, _x_recover(_BY) * _BY % _P)   # base point, extended coords


def _edwards_add(p: tuple, q: tuple) -> tuple:
    """Extended-coordinate point addition. Projective, so no modular inverse per add."""
    x1, y1, z1, t1 = p
    x2, y2, z2, t2 = q
    a = (y1 - x1) * (y2 - x2) % _P
    b = (y1 + x1) * (y2 + x2) % _P
    c = t1 * 2 * _D * t2 % _P
    d = z1 * 2 * z2 % _P
    e, f, g, h = b - a, d - c, d + c, b + a
    return (e * f % _P, g * h % _P, f * g % _P, e * h % _P)


def _edwards_double(p: tuple) -> tuple:
    return _edwards_add(p, p)


def _scalar_mult(p: tuple, e: int) -> tuple:
    """Double-and-add. Not constant time — and does not need to be: every value
    this module multiplies is public."""
    q = (0, 1, 1, 0)                     # neutral element
    while e > 0:
        if e & 1:
            q = _edwards_add(q, p)
        p = _edwards_double(p)
        e >>= 1
    return q


def _compress(p: tuple) -> bytes:
    x, y, z, _ = p
    zi = pow(z, _P - 2, _P)
    x, y = x * zi % _P, y * zi % _P
    return int.to_bytes(y | ((x & 1) << 255), 32, "little")


def _decompress(data: bytes) -> tuple | None:
    """Point from its 32-byte encoding, or None if it is not on the curve.

    Returning None rather than raising: a malformed public key is a
    configuration error the caller must report as "this licence cannot be
    verified", not an exception that escapes into a compliance run.
    """
    if len(data) != 32:
        return None
    y = int.from_bytes(data, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    if y >= _P:
        return None
    x = _x_recover(y)
    if x % 2 != sign:
        x = _P - x
    point = (x, y, 1, x * y % _P)
    # Confirm it satisfies the curve equation rather than trusting the encoding.
    if (-x * x + y * y - 1 - _D * x * x * y * y) % _P != 0:
        return None
    return point


def verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
    """Whether `signature` is a valid Ed25519 signature over `message`.

    Returns False for every malformed input rather than raising. A licence check
    must have exactly two outcomes — valid, or not — because a third outcome is
    one a caller will eventually handle by ignoring it.
    """
    if len(signature) != 64 or len(public_key) != 32:
        return False
    r_bytes, s_bytes = signature[:32], signature[32:]
    s = int.from_bytes(s_bytes, "little")
    if s >= _L:
        return False                       # non-canonical S: reject (RFC 8032 §5.1.7)

    a = _decompress(public_key)
    r = _decompress(r_bytes)
    if a is None or r is None:
        return False

    h = int.from_bytes(_sha512(r_bytes + public_key + message), "little") % _L
    # [S]B == R + [H(R,A,M)]A
    lhs = _scalar_mult(_B, s)
    rhs = _edwards_add(r, _scalar_mult(a, h))
    return _compress(lhs) == _compress(rhs)
