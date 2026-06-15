"""Price lookups for Solana tokens via the free DexScreener API.

No API key required. We accept either a token mint address or a ticker symbol
and return the price (in USD) from the most liquid Solana trading pair.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import httpx

DEXSCREENER_TOKENS = "https://api.dexscreener.com/latest/dex/tokens/{query}"
DEXSCREENER_SEARCH = "https://api.dexscreener.com/latest/dex/search"

# Solana mint addresses are base58 strings, typically 32-44 chars.
_ADDRESS_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")

REQUEST_TIMEOUT = 10.0


@dataclass
class TokenPrice:
    symbol: str
    name: str
    address: str
    price_usd: float
    price_change_24h: float | None
    liquidity_usd: float | None
    url: str


def _looks_like_address(query: str) -> bool:
    return bool(_ADDRESS_RE.match(query))


def _best_solana_pair(pairs: list[dict]) -> dict | None:
    """Return the Solana pair with the deepest liquidity (most reliable price)."""
    solana_pairs = [p for p in pairs if p.get("chainId") == "solana"]
    if not solana_pairs:
        return None
    return max(
        solana_pairs,
        key=lambda p: (p.get("liquidity") or {}).get("usd", 0) or 0,
    )


def _pair_to_price(pair: dict) -> TokenPrice | None:
    price_raw = pair.get("priceUsd")
    if price_raw is None:
        return None
    base = pair.get("baseToken", {})
    return TokenPrice(
        symbol=(base.get("symbol") or "?").upper(),
        name=base.get("name") or base.get("symbol") or "Unknown",
        address=base.get("address") or "",
        price_usd=float(price_raw),
        price_change_24h=(pair.get("priceChange") or {}).get("h24"),
        liquidity_usd=(pair.get("liquidity") or {}).get("usd"),
        url=pair.get("url") or "",
    )


async def get_price(query: str) -> TokenPrice | None:
    """Look up the current price for a token by address or symbol.

    Returns None if the token cannot be found.
    """
    query = query.strip()
    if not query:
        return None

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        if _looks_like_address(query):
            resp = await client.get(DEXSCREENER_TOKENS.format(query=query))
        else:
            resp = await client.get(DEXSCREENER_SEARCH, params={"q": query})
        resp.raise_for_status()
        data = resp.json()

    pair = _best_solana_pair(data.get("pairs") or [])
    if pair is None:
        return None
    return _pair_to_price(pair)
