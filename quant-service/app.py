"""
quant-service — FastAPI micro-service for options/vol analysis.
Runs as a standalone container (Railway/Fly/Render), NOT on Vercel serverless.
Never places trades; read-only and informational only.
"""

import os
import math
import logging
from datetime import date, timedelta
from functools import lru_cache

import httpx
import pandas as pd
import yfinance as yf
from fastapi import FastAPI, HTTPException
from py_vollib.black_scholes.implied_volatility import implied_volatility
from py_vollib.black_scholes.greeks.analytical import delta, gamma, theta, vega

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="quant-service", version="0.1.0")

FRED_API_KEY = os.getenv("FRED_API_KEY", "")  # optional; public series works without key
FRED_SERIES = "DGS3MO"
FALLBACK_RISK_FREE = 0.043


# ---------------------------------------------------------------------------
# Risk-free rate (FRED DGS3MO)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _cache_key() -> str:
    """Returns today's date string so the cache resets once per day."""
    return str(date.today())


async def fetch_risk_free_rate() -> float:
    """Fetches the latest 3-month T-bill rate from FRED. Falls back to constant."""
    _cache_key()  # touch so callers can depend on daily refresh
    url = (
        f"https://api.stlouisfed.org/fred/series/observations"
        f"?series_id={FRED_SERIES}&sort_order=desc&limit=5&file_type=json"
    )
    if FRED_API_KEY:
        url += f"&api_key={FRED_API_KEY}"
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(url)
            r.raise_for_status()
            obs = r.json().get("observations", [])
            for o in obs:
                val = o.get("value", ".")
                if val != ".":
                    rate = float(val) / 100.0
                    logger.info(f"[FRED] DGS3MO = {rate:.4f} (date {o['date']})")
                    return rate
    except Exception as e:
        logger.warning(f"[FRED] fetch failed, using fallback: {e}")
    return FALLBACK_RISK_FREE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dte(expiry_str: str) -> int:
    exp = date.fromisoformat(expiry_str)
    return max((exp - date.today()).days, 1)


def _atm_strike(spot: float, strikes) -> float:
    return min(strikes, key=lambda k: abs(k - spot))


def _calc_iv_and_greeks(spot: float, strike: float, dte: int, mid_price: float,
                        r: float, flag: str) -> dict | None:
    T = dte / 365.0
    if T <= 0 or mid_price <= 0 or spot <= 0:
        return None
    try:
        iv = implied_volatility(mid_price, spot, strike, T, r, flag)
        if math.isnan(iv) or iv <= 0:
            return None
        return {
            "iv": round(iv, 4),
            "delta": round(delta(flag, spot, strike, T, r, iv), 4),
            "gamma": round(gamma(flag, spot, strike, T, r, iv), 6),
            "theta": round(theta(flag, spot, strike, T, r, iv), 4),
            "vega":  round(vega(flag, spot, strike, T, r, iv), 4),
        }
    except Exception:
        return None


def _atm_snapshot(spot: float, chain: "pd.DataFrame", expiry: str,
                  r: float) -> dict | None:
    """Return ATM IV + Greeks for one expiry from the call side."""
    dte = _dte(expiry)
    T = dte / 365.0
    atm = _atm_strike(spot, chain["strike"].values)
    row = chain[chain["strike"] == atm]
    if row.empty:
        return None
    bid = float(row["bid"].iloc[0])
    ask = float(row["ask"].iloc[0])
    mid = (bid + ask) / 2 if bid > 0 and ask > 0 else float(row["lastPrice"].iloc[0])
    result = _calc_iv_and_greeks(spot, atm, dte, mid, r, "c")
    if result is None:
        return None
    implied_move_pct = result["iv"] * math.sqrt(T) * 100
    return {
        "expiry": expiry,
        "dte": dte,
        "atm_strike": atm,
        "atm_iv": result["iv"],
        "implied_move_pct": round(implied_move_pct, 2),
        "greeks": {k: result[k] for k in ("delta", "gamma", "theta", "vega")},
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/options/{ticker}")
async def options_context(ticker: str):
    """
    Returns spot price, nearest expiry, ATM IV, implied move, and Greeks
    for the given ticker using the live FRED risk-free rate.
    """
    r = await fetch_risk_free_rate()
    ticker = ticker.upper()

    try:
        tk = yf.Ticker(ticker)
        info = tk.fast_info
        spot = float(info.last_price)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"yfinance error: {e}")

    expiries = tk.options
    if not expiries:
        raise HTTPException(status_code=404, detail="No options data available")

    expiry = expiries[0]
    try:
        chain = tk.option_chain(expiry).calls
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Option chain error: {e}")

    snap = _atm_snapshot(spot, chain, expiry, r)
    if snap is None:
        raise HTTPException(status_code=422, detail="Could not compute ATM IV")

    return {
        "ticker": ticker,
        "spot": round(spot, 2),
        "risk_free_rate": r,
        **snap,
    }


@app.get("/vol-summary/{ticker}")
async def vol_summary(ticker: str, max_expiries: int = 4):
    """
    IV term structure across the first N expiries.
    Front-month vol spike is the primary event signal.
    """
    r = await fetch_risk_free_rate()
    ticker = ticker.upper()

    try:
        tk = yf.Ticker(ticker)
        spot = float(tk.fast_info.last_price)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"yfinance error: {e}")

    expiries = tk.options
    if not expiries:
        raise HTTPException(status_code=404, detail="No options data available")

    term_structure = []
    for expiry in expiries[:max_expiries]:
        try:
            chain = tk.option_chain(expiry).calls
            snap = _atm_snapshot(spot, chain, expiry, r)
            if snap:
                term_structure.append({
                    "expiry": snap["expiry"],
                    "dte": snap["dte"],
                    "atm_iv": snap["atm_iv"],
                    "implied_move_pct": snap["implied_move_pct"],
                })
        except Exception as e:
            logger.warning(f"[vol-summary] {ticker} {expiry} error: {e}")

    if not term_structure:
        raise HTTPException(status_code=422, detail="Could not compute term structure")

    front_iv = term_structure[0]["atm_iv"] if term_structure else None
    back_iv = term_structure[-1]["atm_iv"] if len(term_structure) > 1 else None
    contango = (front_iv < back_iv) if (front_iv and back_iv) else None

    return {
        "ticker": ticker,
        "spot": round(spot, 2),
        "risk_free_rate": r,
        "term_structure": term_structure,
        "vol_contango": contango,  # False = backwardation = stress signal
    }
