"""Solana wallet activity tracking.

Detects *new* transactions for a watched wallet using the public Solana JSON-RPC
(no API key required). If a Helius API key is configured, each new transaction is
enriched with a human-readable description (e.g. "Swapped 1 SOL for 1.2M BONK").
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import httpx

import config

# Solana addresses and signatures are base58. Addresses are 32-44 chars.
_ADDRESS_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")

REQUEST_TIMEOUT = 15.0
HELIUS_PARSE_URL = "https://api.helius.xyz/v0/transactions"


@dataclass
class Activity:
    signature: str
    description: str  # human-readable, or "" if not enriched
    success: bool

    @property
    def solscan_url(self) -> str:
        return f"https://solscan.io/tx/{self.signature}"


def is_solana_address(value: str) -> bool:
    return bool(_ADDRESS_RE.match(value.strip()))


async def _rpc(method: str, params: list) -> dict:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.post(config.SOLANA_RPC_URL, json=payload)
        resp.raise_for_status()
        return resp.json()


async def get_recent_signatures(address: str, until: str | None = None, limit: int = 10) -> list[dict]:
    """Return recent confirmed signatures for an address, newest first.

    When ``until`` is given, only signatures *newer* than it are returned, which
    is how we detect activity since the last poll.
    """
    opts: dict = {"limit": limit}
    if until:
        opts["until"] = until
    data = await _rpc("getSignaturesForAddress", [address, opts])
    return data.get("result") or []


async def _enrich(signatures: list[str]) -> dict[str, str]:
    """Map signature -> human-readable description via Helius (if configured)."""
    if not config.HELIUS_API_KEY or not signatures:
        return {}
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(
                HELIUS_PARSE_URL,
                params={"api-key": config.HELIUS_API_KEY},
                json={"transactions": signatures},
            )
            resp.raise_for_status()
            parsed = resp.json()
    except Exception:
        return {}  # enrichment is best-effort; fall back to plain links
    return {
        tx.get("signature", ""): (tx.get("description") or "").strip()
        for tx in parsed
        if tx.get("signature")
    }


async def fetch_new_activity(address: str, last_signature: str | None) -> tuple[str | None, list[Activity]]:
    """Return (newest_signature, new_activity_items_oldest_first).

    ``newest_signature`` should be persisted as the new high-water mark. If there
    is no new activity it equals ``last_signature``.
    """
    sigs = await get_recent_signatures(address, until=last_signature, limit=10)
    if not sigs:
        return last_signature, []

    newest = sigs[0]["signature"]
    descriptions = await _enrich([s["signature"] for s in sigs])

    # Report oldest-first so notifications arrive in chronological order.
    items = [
        Activity(
            signature=s["signature"],
            description=descriptions.get(s["signature"], ""),
            success=s.get("err") is None,
        )
        for s in reversed(sigs)
    ]
    return newest, items


async def latest_signature(address: str) -> str | None:
    """Newest signature right now — used as the baseline when watching starts."""
    sigs = await get_recent_signatures(address, limit=1)
    return sigs[0]["signature"] if sigs else None
