import { supabaseAdmin } from '$lib/server/supabase';
import { fetchMarketSnapshot } from '$lib/api/markets';
import { KEYWORD_SEVERITY, TOPIC_MAPPING } from '$lib/config/topics';

export async function load() {
    // 1. Fetch top recent events
    const { data: events, error: evErr } = await supabaseAdmin
        .from('events')
        .select(`
            id, title, summary, severity, created_at,
            event_impacts ( sectors, tickers )
        `)
        .order('created_at', { ascending: false })
        .limit(10);

    // 2. Fetch a broad market snapshot for the top bar (e.g. major indices)
    // We'll mock a short list of interesting tickers spanning the topics
    const baselineTickers = ['SPY', 'QQQ', 'VIX', 'GLD', 'USO'];
    const marketSnapshot = await fetchMarketSnapshot(baselineTickers);

    return {
        events: events || [],
        marketSnapshot
    };
}
