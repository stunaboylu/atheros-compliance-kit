"""Settings are read at import time, so the environment is set before `app`
is imported — a fresh signing key per session, a salt, and a SQLite file
standing in for Postgres. Nothing here reaches a network."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import pytest_asyncio

HERE = Path(__file__).resolve().parent
SERVICE = HERE.parent
REPO = SERVICE.parent.parent

os.environ["ATHEROS_SIGNING_KEY_PEM"] = subprocess.run(
    [sys.executable, "-m", "app.keys", "generate"], cwd=SERVICE, check=True,
    capture_output=True, text=True).stdout
os.environ["ATHEROS_FINGERPRINT_SALT"] = "test-salt-not-for-production"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test-licences.sqlite"
os.environ["DEBUG"] = "false"

# The Kit's verifier, imported from source: the one test that matters is that a
# token minted here verifies THERE, with no shared code between the two.
sys.path.insert(0, str(REPO / "atheros-compliance-kit" / "src"))

from app import main as service  # noqa: E402
from app.models import Licence  # noqa: E402


@pytest_asyncio.fixture
async def client():
    from httpx import ASGITransport, AsyncClient
    db = SERVICE / "test-licences.sqlite"
    if db.exists():
        db.unlink()
    await service.startup()
    async with AsyncClient(transport=ASGITransport(app=service.app), base_url="http://t") as c:
        yield c
    await service.engine.dispose()
    if db.exists():
        db.unlink()


@pytest_asyncio.fixture
async def licence_factory(client):
    from datetime import date, timedelta

    async def make(key: str = "ATH-TEAM-0001-TESTKEY", *, tier: str = "team", seats: int = 5,
                   status: str = "active", days: int = 365, account: str = "Example B.V.") -> Licence:
        async with service.Session() as s:
            row = Licence(key_hash=service._hash_key(key), tier=tier, seats=seats,
                          account=account, status=status,
                          expires=date.today() + timedelta(days=days))
            s.add(row)
            await s.commit()
            await s.refresh(row)
            return row
    return make


@pytest.fixture
def public_key_hex() -> str:
    from app.keys import public_key_hex
    return public_key_hex()
