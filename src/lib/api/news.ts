import { resilientFetch } from '../services/fetch';
import { KEYWORD_SEVERITY } from '../config/topics';

const GDELT_BASE = 'https://api.gdeltproject.org/api/v2/doc/doc';

export interface NewsCandidate {
    url: string;
    title: string;
    published_at: string;
    source: string;
    severity_clues: string[];
}

// Queries GDELT for recent news based on some broad keywords
export async function fetchBreakingCandidates(): Promise<NewsCandidate[]> {
    const keywords = Object.keys(KEYWORD_SEVERITY).join(' OR ');
    // Search the last few hours
    const query = `(${keywords}) sourcelang:eng`;
    const url = `${GDELT_BASE}?query=${encodeURIComponent(query)}&mode=artlist&maxrecords=50&format=json&sort=datedesc`;

    try {
        const response = await resilientFetch(url, { retries: 2, timeoutMs: 15000 });
        if (!response || !response.articles) return [];

        return response.articles.map((art: any) => {
            const titleLower = art.title.toLowerCase();
            const clues = Object.keys(KEYWORD_SEVERITY).filter(k => titleLower.includes(k));

            return {
                url: art.url,
                title: art.title,
                published_at: art.seendate, // GDELT format might need parsing
                source: art.domain,
                severity_clues: clues
            };
        });
    } catch (e) {
        console.error('Failed to fetch GDELT candidates:', e);
        return [];
    }
}
