from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://licence:licence@localhost:5432/licence"

    #: PEM-encoded Ed25519 private key. Read from the environment so that swapping
    #: in a KMS-backed signer is one function rather than a rewrite. It must never
    #: be baked into an image or committed.
    atheros_signing_key_pem: str = ""
    #: Key id published in JWKS and carried in each token header, so a token
    #: signed before a rotation can still be attributed to the key that signed it.
    signing_key_id: str = "atheros-2026"
    #: Previous public keys, hex, still published during a rotation overlap.
    retired_public_keys: list[str] = []

    #: Token lifetime. Long on purpose: it is a grace period, not a heartbeat.
    #: At 90 days a customer whose network cannot reach us keeps building for a
    #: quarter, which is longer than any outage we could plausibly have.
    token_days: int = 90

    #: Activations allowed per licence beyond the seat count, for CI runners that
    #: come and go. Set generously — a legitimate customer hitting an activation
    #: wall mid-release is a support call we caused.
    fingerprint_headroom: int = 20

    debug: bool = False


settings = Settings()
