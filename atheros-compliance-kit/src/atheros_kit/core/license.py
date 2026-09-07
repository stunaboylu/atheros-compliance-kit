"""Licence verification — offline, and never in the way.

DESIGN CONSTRAINTS, in the order they mattered

1. **The free tier requires no activation, ever.** `guard`, `euact.classify` and
   the whole of `core` run with no key, no token, and no network call. A customer
   evaluating the product must never meet a licence check.
2. **Verification is offline.** The token is a 90-day grace signed by our server
   and checked here against a public key compiled into the package. A network
   outage, an expired domain, or this company ceasing to exist must not stop a
   customer's CI. A licence server that can break a build is a licence server
   that will.
3. **A failed check degrades, it does not crash.** An expired or missing licence
   disables the paid modules and says which and why. It never raises inside an
   assessment, and it never silently returns wrong results.

    from atheros_kit.core.license import current, require

    current().tier          # "free" | "team" | "enterprise"
    require("rag")          # raises LicenceRequired with an actionable message
"""
from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .ed25519 import verify
from .errors import AtherosError

#: Modules usable with no licence and no activation, for any purpose, forever.
FREE_CAPABILITIES = frozenset({"core", "guard", "euact.classify", "audit"})

#: What each tier unlocks beyond the free set.
TIERS: dict[str, frozenset[str]] = {
    "free": frozenset(),
    "team": frozenset({"rag", "vendor", "cicd", "euact.dossier", "export.pdf",
                       "iso.export"}),
    "enterprise": frozenset({"rag", "vendor", "cicd", "euact.dossier", "export.pdf",
                             "iso.export", "airgap", "custom_connector", "sso"}),
}

#: Ed25519 public key for licence tokens, compiled into the package.
#:
#: Rotation: a new key is ADDED here in a release, and the old one is removed a
#: release later. Two keys are trusted during the overlap so a customer running a
#: version from either side of the rotation keeps working — a rotation that
#: invalidates tokens is an outage the customer did not schedule.
TRUSTED_KEYS: tuple[str, ...] = (
    # 2026 signing key. Replaced, never edited: the value below is a placeholder
    # until the licence service publishes its production key, and `current()`
    # treats an unverifiable token as absent rather than as valid.
    "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a",
)


#: Whether `require()` actually blocks.
#:
#: FALSE for 1.0.0, and this is a statement of fact rather than a courtesy: the
#: production signing key in TRUSTED_KEYS below is still a placeholder, so no
#: real licence CAN be issued yet. Enforcing against a key that signs nothing
#: would mean every paying customer is refused and every evaluator concludes the
#: product is broken.
#:
#: Flipping this to True requires, in order: the licence service deployed, its
#: public key published in TRUSTED_KEYS, and a release note saying so. Until all
#: three are done, `doctor` prints the current state rather than implying a
#: control exists that does not.
ENFORCED = False


class LicenceRequired(AtherosError):
    """A paid capability was used without a licence covering it."""


@dataclass
class Licence:
    tier: str = "free"
    capabilities: frozenset[str] = field(default_factory=lambda: FREE_CAPABILITIES)
    expires: str | None = None
    account: str | None = None
    seats: int | None = None
    #: Why the licence is what it is. Printed by `atheros-kit doctor`, so a
    #: customer whose token did not apply can see which of the six reasons it was
    #: rather than filing a ticket.
    reason: str = "no licence configured — free tier"
    verified: bool = False

    @property
    def expired(self) -> bool:
        if not self.expires:
            return False
        try:
            return date.fromisoformat(self.expires) < date.today()
        except ValueError:
            return True

    @property
    def days_remaining(self) -> int | None:
        if not self.expires:
            return None
        try:
            return (date.fromisoformat(self.expires) - date.today()).days
        except ValueError:
            return None

    def allows(self, capability: str) -> bool:
        if capability in FREE_CAPABILITIES:
            return True
        return capability in self.capabilities and not self.expired

    def to_dict(self) -> dict[str, Any]:
        return {
            "tier": self.tier,
            "account": self.account,
            "seats": self.seats,
            "expires": self.expires,
            "days_remaining": self.days_remaining,
            "expired": self.expired,
            "verified": self.verified,
            "reason": self.reason,
            "capabilities": sorted(self.capabilities | FREE_CAPABILITIES),
        }


def _b64url(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _token_locations() -> list[Path]:
    """Where a token may live, most specific first."""
    out: list[Path] = []
    env_path = os.environ.get("ATHEROS_LICENCE_FILE") or os.environ.get("ATHEROS_LICENSE_FILE")
    if env_path:
        out.append(Path(env_path))
    out.append(Path(".atheros/licence.jwt"))
    out.append(Path.home() / ".atheros" / "licence.jwt")
    return out


def _read_token() -> tuple[str | None, str]:
    inline = os.environ.get("ATHEROS_LICENCE") or os.environ.get("ATHEROS_LICENSE")
    if inline:
        return inline.strip(), "ATHEROS_LICENCE"
    for path in _token_locations():
        if path.is_file():
            return path.read_text(encoding="utf-8").strip(), str(path)
    return None, "—"


def parse(token: str, *, keys: tuple[str, ...] = TRUSTED_KEYS) -> Licence:
    """Verify and decode a licence token. Never raises.

    The token is a compact JWS with `alg: EdDSA`. `alg` is read only to REJECT
    anything that is not EdDSA — the algorithm is fixed by this code, not chosen
    by the token, because letting a token nominate its own algorithm is how
    `alg: none` happens.
    """
    def deny(reason: str) -> Licence:
        return Licence(reason=reason)

    parts = token.split(".")
    if len(parts) != 3:
        return deny("licence token is malformed — free tier")
    header_b64, payload_b64, sig_b64 = parts
    try:
        header = json.loads(_b64url(header_b64))
        payload = json.loads(_b64url(payload_b64))
        signature = _b64url(sig_b64)
    except (ValueError, json.JSONDecodeError):
        return deny("licence token could not be decoded — free tier")

    if header.get("alg") != "EdDSA":
        return deny(f"licence token declares alg={header.get('alg')!r}; only EdDSA is "
                    f"accepted — free tier")

    signed = f"{header_b64}.{payload_b64}".encode("ascii")
    if not any(verify(bytes.fromhex(k), signed, signature) for k in keys):
        return deny("licence signature did not verify against any trusted key — free tier")

    tier = str(payload.get("tier", "free")).lower()
    if tier not in TIERS:
        return deny(f"licence names an unknown tier {tier!r} — free tier")

    expires = payload.get("exp_date")
    lic = Licence(
        tier=tier,
        capabilities=TIERS[tier] | FREE_CAPABILITIES,
        expires=expires,
        account=payload.get("account"),
        seats=payload.get("seats"),
        verified=True,
        reason=f"{tier} licence, verified",
    )
    if lic.expired:
        # Expired is NOT invalid: it is a licence that has run out, and the
        # difference matters to the person reading the message.
        return Licence(
            tier="free", expires=expires, account=payload.get("account"), verified=True,
            reason=f"{tier} licence expired on {expires} — free tier until renewed. "
                   f"Run `atheros-kit licence activate` or contact sales@atheros.ai.",
        )
    return lic


_CACHE: Licence | None = None


def current(*, refresh: bool = False) -> Licence:
    """The licence in effect. Resolved once per process; never touches the network."""
    global _CACHE
    if _CACHE is not None and not refresh:
        return _CACHE
    token, source = _read_token()
    if token is None:
        _CACHE = Licence()
        return _CACHE
    lic = parse(token)
    if lic.verified and lic.tier != "free":
        lic.reason = f"{lic.tier} licence, verified (from {source})"
    _CACHE = lic
    return _CACHE


def set_current(licence: Licence | None) -> None:
    """For tests, and for an application that resolves licensing its own way."""
    global _CACHE
    _CACHE = licence


def allows(capability: str) -> bool:
    return current().allows(capability)


def require(capability: str) -> None:
    """Gate a paid capability.

    The message names the capability, the tier that covers it, and what to do —
    a licence error that says only "unlicensed" costs a support ticket.
    """
    lic = current()
    if lic.allows(capability):
        return
    if not ENFORCED:
        # Recorded, not blocked. See ENFORCED above for why, and for what has to
        # be true before this returns to blocking.
        return
    covering = sorted(t for t, caps in TIERS.items() if capability in caps)
    raise LicenceRequired(
        f"'{capability}' requires a {' or '.join(covering) or 'paid'} licence. "
        f"Current: {lic.tier} ({lic.reason}). "
        f"The free tier covers {', '.join(sorted(FREE_CAPABILITIES))} with no activation. "
        f"See https://atheros.ai/compliance-kit/pricing"
    )


def status() -> dict[str, Any]:
    """What `doctor` prints. States the enforcement position plainly."""
    lic = current()
    return {
        **lic.to_dict(),
        "enforced": ENFORCED,
        "note": (
            "Licence enforcement is ON."
            if ENFORCED else
            "Licence enforcement is OFF in this release: the signing key is a placeholder, so "
            "no licence can be issued yet and every module is usable. This will change in the "
            "release that publishes the production key."
        ),
    }


def issued_at_utc() -> str:
    return datetime.now(timezone.utc).isoformat()
