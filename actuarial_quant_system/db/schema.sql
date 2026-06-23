-- ============================================================================
-- Actuarial Quant System — PostgreSQL schema (historical log & audit trail)
-- ----------------------------------------------------------------------------
-- Redis holds live/ephemeral state (loss reserves, locks). PostgreSQL is the
-- durable record: positions, fills, daily briefings, regime snapshots and a
-- tamper-evident audit log. On reboot the engine restores live state from Redis
-- and reconciles against the open positions persisted here.
-- ============================================================================

CREATE TABLE IF NOT EXISTS accounts (
    id              BIGSERIAL PRIMARY KEY,
    label           TEXT NOT NULL UNIQUE,
    venue           TEXT NOT NULL DEFAULT 'paper',
    paper           BOOLEAN NOT NULL DEFAULT TRUE,
    equity_usd      NUMERIC NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Open & historical positions. One row per (account, symbol, structure) lot.
CREATE TABLE IF NOT EXISTS positions (
    id              BIGSERIAL PRIMARY KEY,
    account_id      BIGINT REFERENCES accounts(id) ON DELETE CASCADE,
    symbol          TEXT NOT NULL,
    structure       TEXT NOT NULL,              -- CASH_LONG, SHORT_PUT, IRON_CONDOR, ...
    side            TEXT NOT NULL,              -- BUY | SELL
    notional_usd    NUMERIC NOT NULL,
    entry_price     NUMERIC,
    delta           NUMERIC DEFAULT 0,
    gamma           NUMERIC DEFAULT 0,
    vega            NUMERIC DEFAULT 0,
    theta           NUMERIC DEFAULT 0,
    loss_reserve_usd NUMERIC NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'OPEN',  -- OPEN | CLOSED
    opened_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at       TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_positions_account ON positions(account_id, status);

-- Every simulated (paper) or live fill.
CREATE TABLE IF NOT EXISTS trades (
    id              BIGSERIAL PRIMARY KEY,
    account_id      BIGINT REFERENCES accounts(id) ON DELETE CASCADE,
    symbol          TEXT NOT NULL,
    structure       TEXT NOT NULL,
    side            TEXT NOT NULL,
    notional_usd    NUMERIC NOT NULL,
    fill_price      NUMERIC NOT NULL,
    slippage_usd    NUMERIC NOT NULL DEFAULT 0,
    fee_usd         NUMERIC NOT NULL DEFAULT 0,
    paper           BOOLEAN NOT NULL DEFAULT TRUE,
    risk_verdict    TEXT NOT NULL,              -- APPROVED | REJECTED
    rationale       TEXT,
    executed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_trades_account_time ON trades(account_id, executed_at DESC);

-- Daily executive briefing snapshots (one per day per account).
CREATE TABLE IF NOT EXISTS daily_briefings (
    id                   BIGSERIAL PRIMARY KEY,
    account_id           BIGINT REFERENCES accounts(id) ON DELETE CASCADE,
    as_of                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    surplus_health_index NUMERIC,
    net_earnings_24h_usd NUMERIC,
    regime               TEXT,
    ruin_probability     NUMERIC,
    expected_shortfall_99 NUMERIC,
    free_capital_usd     NUMERIC,
    frozen_reserve_usd   NUMERIC,
    payload              JSONB NOT NULL          -- full briefing object
);
CREATE INDEX IF NOT EXISTS idx_briefings_account_time ON daily_briefings(account_id, as_of DESC);

-- Regime / vol model snapshots for historical analysis.
CREATE TABLE IF NOT EXISTS regime_snapshots (
    id              BIGSERIAL PRIMARY KEY,
    captured_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    regime          TEXT,
    garch_vol       NUMERIC,
    garch_forecast  NUMERIC,
    payload         JSONB NOT NULL
);

-- Append-only audit trail. Never UPDATE/DELETE — tamper-evident.
CREATE TABLE IF NOT EXISTS audit_log (
    id              BIGSERIAL PRIMARY KEY,
    ts              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor           TEXT NOT NULL,              -- 'engine' | 'risk_gate' | 'api'
    event           TEXT NOT NULL,
    detail          JSONB
);
CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(ts DESC);
