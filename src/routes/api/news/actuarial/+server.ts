import { json } from '@sveltejs/kit';
import { fetchBreakingCandidates } from '$lib/api/news';

// Short-lived cache specifically for the live actuarial dashboard
let cache: any | null = null;
let lastFetch = 0;
const CACHE_TTL_MS = 60 * 1000 * 5; // 5 minutes

export async function GET() {
    if (cache && (Date.now() - lastFetch < CACHE_TTL_MS)) {
        return json({ news: cache, _cached: true });
    }

    try {
        const candidates = await fetchBreakingCandidates();

        // Keywords for Actuarial categorizations
        const mhitRegex = /(mhit|health insurance|medical cost|medicare|healthcare cost|hospital billing)/i;
        const pcRegex = /(fire insurance|property and casualty|catastrophe bond|auto insurance|climate risk|property damage|natural disaster)/i;
        const lifeRegex = /(life insurance|mortality|longevity|annuity|pension|retirement planning)/i;

        const categorized = {
            mhit: [] as any[],
            property_casualty: [] as any[],
            life_pension: [] as any[],
            raw: [] as any[]
        };

        for (const item of candidates) {
            const content = (item.title + " " + item.severity_clues.join(" ")).toLowerCase();
            let matched = false;

            if (mhitRegex.test(content)) {
                categorized.mhit.push(item);
                matched = true;
            }
            if (pcRegex.test(content)) {
                categorized.property_casualty.push(item);
                matched = true;
            }
            if (lifeRegex.test(content)) {
                categorized.life_pension.push(item);
                matched = true;
            }

            // Always add to raw if it has some financial or risk relevance
            if (!matched && /(insurance|risk|actuarial|premium|claim|liability)/i.test(content)) {
                categorized.raw.push(item);
            }
        }

        cache = categorized;
        lastFetch = Date.now();

        return json({ news: categorized, _cached: false });
    } catch (e) {
        console.error("Live Actuarial News error:", e);
        // Return empty arrays on failure so the UI doesn't crash
        return json({
            news: { mhit: [], property_casualty: [], life_pension: [], raw: [] },
            error: true
        }, { status: 500 });
    }
}
