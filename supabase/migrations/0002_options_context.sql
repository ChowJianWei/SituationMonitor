-- Stores the options/vol snapshot captured at alert time for each impacted ticker.
-- One row per event × ticker so we can build historical IV datasets.

CREATE TABLE IF NOT EXISTS event_options_context (
    id              BIGSERIAL PRIMARY KEY,
    event_id        BIGINT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    ticker          TEXT NOT NULL,
    captured_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Spot & nearest expiry
    spot            NUMERIC,
    expiry          DATE,
    dte             INT,

    -- ATM vol (front expiry)
    atm_iv          NUMERIC,
    implied_move_pct NUMERIC,

    -- Greeks at ATM
    delta           NUMERIC,
    gamma           NUMERIC,
    theta           NUMERIC,
    vega            NUMERIC,

    -- Vol term structure (up to 4 expiries)
    vol_term_structure JSONB,   -- [{expiry, dte, atm_iv, implied_move_pct}]

    -- Risk-free rate used (from FRED DGS3MO)
    risk_free_rate  NUMERIC,

    UNIQUE (event_id, ticker)
);

CREATE INDEX ON event_options_context (event_id);
CREATE INDEX ON event_options_context (ticker, captured_at);
