"""
config.py
=========
Process-level configuration loaded from environment variables.

NOTE: The hardcoded RISK LIMITS deliberately do NOT live here. They are
constants inside src/risk_gate/pre_trade_check.py so they cannot be altered by
an env var, a database row, or a network payload. Only operational wiring
(hosts, ports, modes) is configurable here.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # --- infrastructure ---
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    postgres_dsn: str = os.getenv(
        "POSTGRES_DSN", "postgresql://localhost:5432/actuarial"
    )

    # --- api server ---
    api_host: str = os.getenv("API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("API_PORT", "8200"))
    cors_origin: str = os.getenv("CORS_ORIGIN", "http://localhost:3000")

    # --- venue / execution ---
    broker_base_url: str = os.getenv("BROKER_BASE_URL", "https://sandbox.exchange.local")
    broker_api_key: str = os.getenv("BROKER_API_KEY", "")
    broker_api_secret: str = os.getenv("BROKER_API_SECRET", "")

    # --- Tradier (equity options) ---
    # EXECUTION_MODE: "paper" (internal simulator) or "tradier_sandbox"/"tradier_live".
    execution_mode: str = os.getenv("EXECUTION_MODE", "paper")
    tradier_env: str = os.getenv("TRADIER_ENV", "sandbox")          # sandbox | production
    tradier_access_token: str = os.getenv("TRADIER_ACCESS_TOKEN", "")
    tradier_account_id: str = os.getenv("TRADIER_ACCOUNT_ID", "")

    # --- safety posture ---
    # Defaults to True: the engine is read-only/informational until a human
    # explicitly flips this off AND the key carries trade scope.
    paper_trading_only: bool = _env_bool("PAPER_TRADING_ONLY", True)

    # --- market data ---
    risk_free_series: str = os.getenv("FRED_SERIES", "DGS3MO")
    fred_api_key: str = os.getenv("FRED_API_KEY", "")

    # --- autonomous underwriting cycle ---
    # Seconds between paper underwriting cycles run by the background daemon.
    cycle_interval_seconds: int = int(os.getenv("CYCLE_INTERVAL_SECONDS", "60"))
    # Starting equity used to seed a fresh paper account on first boot.
    seed_equity_usd: float = float(os.getenv("SEED_EQUITY_USD", "180000"))


settings = Settings()
