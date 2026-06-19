const QUANT_SERVICE_URL = process.env.QUANT_SERVICE_URL ?? 'http://localhost:8000';

export interface OptionsContext {
    ticker: string;
    spot: number;
    risk_free_rate: number;
    expiry: string;
    dte: number;
    atm_strike: number;
    atm_iv: number;
    implied_move_pct: number;
    greeks: {
        delta: number;
        gamma: number;
        theta: number;
        vega: number;
    };
}

export interface VolTermEntry {
    expiry: string;
    dte: number;
    atm_iv: number;
    implied_move_pct: number;
}

export interface VolSummary {
    ticker: string;
    spot: number;
    risk_free_rate: number;
    term_structure: VolTermEntry[];
    vol_contango: boolean | null;
}

/**
 * Fetches spot + nearest-expiry ATM IV + Greeks from quant-service.
 * Returns null on any error so the caller (alert run) is never blocked.
 */
export async function getOptionsContext(ticker: string): Promise<OptionsContext | null> {
    try {
        const res = await fetch(`${QUANT_SERVICE_URL}/options/${encodeURIComponent(ticker)}`, {
            signal: AbortSignal.timeout(10_000),
        });
        if (!res.ok) return null;
        return (await res.json()) as OptionsContext;
    } catch {
        return null;
    }
}

/**
 * Fetches IV term structure (up to 4 expiries) from quant-service.
 * Returns null on any error.
 */
export async function getVolSummary(ticker: string): Promise<VolSummary | null> {
    try {
        const res = await fetch(`${QUANT_SERVICE_URL}/vol-summary/${encodeURIComponent(ticker)}`, {
            signal: AbortSignal.timeout(12_000),
        });
        if (!res.ok) return null;
        return (await res.json()) as VolSummary;
    } catch {
        return null;
    }
}
