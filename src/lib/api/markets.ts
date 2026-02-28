import { resilientFetch } from '../services/fetch';
import { env } from '$env/dynamic/private';

const FINNHUB_KEY = env.FINNHUB_API_KEY || process.env.FINNHUB_API_KEY;

export async function fetchMarketSnapshot(tickers: string[]): Promise<Record<string, any>> {
    if (!FINNHUB_KEY) {
        console.warn('Finnhub API key missing, returning mocked market data.');
        const mock: Record<string, any> = {};
        for (const t of tickers) {
            mock[t] = { current: 100, changePercent: -1.2 };
        }
        return mock;
    }

    const results: Record<string, any> = {};

    for (const ticker of tickers) {
        try {
            const url = `https://finnhub.io/api/v1/quote?symbol=${ticker}&token=${FINNHUB_KEY}`;
            // Cache market data heavily if lots of tickers to avoid rate limits on free tier
            const data = await resilientFetch(url, { retries: 1, timeoutMs: 5000 }, true, 60000 * 15);
            if (data && data.c) {
                results[ticker] = {
                    current: data.c,
                    changePercent: data.dp // Daily percent change
                };
            }
            // Sleep slightly to respect rate limits
            await new Promise(r => setTimeout(r, 200));
        } catch (e) {
            console.error(`Failed to fetch quote for ${ticker}:`, e);
        }
    }

    return results;
}
