"""
market_data.py
==============
Real OHLC market data with a synthetic fallback.

Sources (free, no API key):
  * Crypto (BTC, ETH) -> Kraken public OHLC API (global).
  * Equities (SPY, ...) -> Yahoo Finance chart API.

Results are cached for a few minutes to respect rate limits, and every fetch
fails soft: if a provider is unreachable we fall back to a synthetic series so
the rest of the system keeps working.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

import httpx
import numpy as np

from ..models.regime_models import simulate_clustered_returns

logger = logging.getLogger("market_data")

_TTL = 300  # seconds
_cache: dict[str, tuple[float, dict]] = {}

# Crypto symbols routed to Kraken; ANY other symbol (stocks/ETFs) goes to Yahoo,
# so the user can look up essentially any ticker.
_KRAKEN_PAIR = {
    "BTC": "XBTUSD", "ETH": "ETHUSD", "SOL": "SOLUSD", "XRP": "XRPUSD",
    "ADA": "ADAUSD", "DOT": "DOTUSD", "LINK": "LINKUSD", "AVAX": "AVAXUSD",
    "LTC": "LTCUSD", "DOGE": "XDGUSD", "MATIC": "MATICUSD",
}
# Plausible base prices for the synthetic fallback.
_FALLBACK_SPOT = {"BTC": 65_000.0, "ETH": 3_500.0, "SPY": 540.0}

_client: Optional[httpx.AsyncClient] = None


def _http() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=12.0, headers={"User-Agent": "Mozilla/5.0"})
    return _client


async def _kraken(symbol: str) -> list[dict]:
    pair = _KRAKEN_PAIR[symbol]
    r = await _http().get("https://api.kraken.com/0/public/OHLC",
                          params={"pair": pair, "interval": 60})
    r.raise_for_status()
    result = r.json()["result"]
    key = next(k for k in result if k != "last")
    rows = result[key]
    return [{"t": int(c[0]), "o": float(c[1]), "h": float(c[2]),
             "l": float(c[3]), "c": float(c[4]), "v": float(c[6])} for c in rows]


async def _yahoo(symbol: str) -> list[dict]:
    r = await _http().get(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
        params={"interval": "1d", "range": "1y"})
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    ts = res["timestamp"]
    q = res["indicators"]["quote"][0]
    out = []
    for i, t in enumerate(ts):
        o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
        if None in (o, h, l, c):
            continue
        out.append({"t": int(t), "o": float(o), "h": float(h),
                    "l": float(l), "c": float(c), "v": float(q["volume"][i] or 0)})
    return out


def _synthetic(symbol: str) -> list[dict]:
    """Build a plausible OHLC series from clustered returns (fallback only)."""
    base = _FALLBACK_SPOT.get(symbol.upper(), 100.0)
    rets = simulate_clustered_returns(n=300, seed=abs(hash(symbol)) % 1000)
    price = base
    now = int(time.time())
    candles = []
    for i, ret in enumerate(rets):
        o = price
        c = price * (1.0 + ret)
        h = max(o, c) * (1.0 + abs(ret) * 0.5)
        l = min(o, c) * (1.0 - abs(ret) * 0.5)
        candles.append({"t": now - (len(rets) - i) * 3600,
                        "o": round(o, 2), "h": round(h, 2), "l": round(l, 2),
                        "c": round(c, 2), "v": 0.0})
        price = c
    return candles


async def get_market(symbol: str) -> dict:
    """
    Return {symbol, source, last, candles}. `source` is "kraken" | "yahoo" |
    "synthetic". Cached for _TTL seconds.
    """
    symbol = symbol.upper()
    now = time.time()
    cached = _cache.get(symbol)
    if cached and now - cached[0] < _TTL:
        return cached[1]

    source = "synthetic"
    candles: list[dict] = []
    try:
        if symbol in _KRAKEN_PAIR:
            candles = await _kraken(symbol)
            source = "kraken"
        else:
            candles = await _yahoo(symbol)
            source = "yahoo"
    except Exception as exc:  # pragma: no cover - network
        logger.warning("Real data fetch failed for %s (%s); using synthetic.", symbol, exc)
        candles = []

    if not candles:
        candles = _synthetic(symbol)
        source = "synthetic"

    data = {"symbol": symbol, "source": source, "found": source != "synthetic",
            "last": round(candles[-1]["c"], 2), "candles": candles}
    _cache[symbol] = (now, data)
    return data


def closes(candles: list[dict]) -> np.ndarray:
    return np.array([c["c"] for c in candles], dtype=float)


def log_returns(candles: list[dict]) -> np.ndarray:
    px = closes(candles)
    px = px[px > 0]
    return np.diff(np.log(px)) if px.size > 1 else np.array([])


async def aclose() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
