import { json } from '@sveltejs/kit';
import { fetchBreakingCandidates } from '$lib/api/news';

// Cache the results for 15 minutes to avoid spamming the GDELT API on every page load
let cache: { data: any, timestamp: number } | null = null;
const CACHE_VARS = { TTL: 15 * 60 * 1000 };

export async function GET() {
    const now = Date.now();
    if (cache && now - cache.timestamp < CACHE_VARS.TTL) {
        return json(cache.data);
    }

    try {
        // Fetch candidates without strictly adhering to a high threshold, as the dashboard needs volume
        const candidates = await fetchBreakingCandidates();

        // Categorize candidates for UI matching the original hipcityreg repo
        const categorizedNews = {
            politics: candidates.filter(c => c.severity_clues.includes('geopolitics') || c.title.toLowerCase().match(/election|war|president|minister|gov|policy|court/)).slice(0, 10),
            tech: candidates.filter(c => c.title.toLowerCase().match(/tech|ai|cyber|apple|google|meta|microsoft|crypto|bitcoin/)).slice(0, 10),
            finance: candidates.filter(c => c.severity_clues.includes('macro') || c.title.toLowerCase().match(/market|economy|fed|bank|stock|inflation|rate/)).slice(0, 10),
            gov: candidates.filter(c => c.title.toLowerCase().match(/senate|congress|parliament|law|bill|agency|fcc|sec/)).slice(0, 10),
            ai: candidates.filter(c => c.title.toLowerCase().match(/ai|artificial intelligence|openai|llm|deepmind/)).slice(0, 10),
            raw: candidates.slice(0, 50) // Fallback list
        };

        // If categories are empty due to GDELT keyword matching, fallback somewhat randomly
        if (categorizedNews.politics.length === 0) categorizedNews.politics = candidates.slice(0, 8);
        if (categorizedNews.tech.length === 0) categorizedNews.tech = candidates.slice(8, 16);
        if (categorizedNews.finance.length === 0) categorizedNews.finance = candidates.slice(16, 24);

        const responseData = {
            status: 'success',
            news: categorizedNews,
            fetchedAt: now
        };

        cache = { data: responseData, timestamp: now };
        return json(responseData);
    } catch (e) {
        console.error("Live news fetch error:", e);
        return json({ status: 'error', message: 'Failed to fetch live feed' }, { status: 500 });
    }
}
