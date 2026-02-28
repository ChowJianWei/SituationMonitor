import { KEYWORD_SEVERITY, TOPIC_MAPPING } from '../config/topics';
import { THRESHOLDS } from '../config/thresholds';
import type { NewsCandidate } from '../api/news';

export interface EventCluster {
    title: string;
    sources: NewsCandidate[];
    severityScore: number;
    sectors: string[];
    tickers: string[];
}

export function detectAndClusterEvents(candidates: NewsCandidate[]): EventCluster[] {
    const clusters: Record<string, EventCluster> = {};

    for (const candidate of candidates) {
        if (!candidate.severity_clues || candidate.severity_clues.length === 0) continue;

        // Simple clustering: pick the most severe clue as the cluster ID
        const primaryClue = candidate.severity_clues.sort((a, b) => KEYWORD_SEVERITY[b] - KEYWORD_SEVERITY[a])[0];

        if (!clusters[primaryClue]) {
            clusters[primaryClue] = {
                title: `High Activity: ${primaryClue.toUpperCase()}`,
                sources: [],
                severityScore: 0,
                sectors: [],
                tickers: []
            };
        }

        const cluster = clusters[primaryClue];
        // Deduplicate URLs
        if (!cluster.sources.find(s => s.url === candidate.url)) {
            cluster.sources.push(candidate);
        }
    }

    const validClusters: EventCluster[] = [];

    for (const key of Object.keys(clusters)) {
        const cluster = clusters[key];

        // Severity score heuristic = keyword severity * spike mult
        const keywordSev = KEYWORD_SEVERITY[key] || 10;
        const spikeMultiplier = cluster.sources.length;
        cluster.severityScore = keywordSev * spikeMultiplier;

        // Apply topic mapping logic
        // We do a simple reverse search over TOPIC_MAPPING keys vs title/description
        // For hackathon sake, we'll map the primaryClue if it matches any
        for (const [topic, meta] of Object.entries(TOPIC_MAPPING)) {
            const hasTopic = cluster.sources.some(s => s.title.toLowerCase().includes(topic.toLowerCase()));
            if (hasTopic || topic.includes(key) || key.includes(topic)) {
                meta.sectors.forEach(sec => { if (!cluster.sectors.includes(sec)) cluster.sectors.push(sec) });
                meta.tickers.forEach(tic => { if (!cluster.tickers.includes(tic)) cluster.tickers.push(tic) });
                cluster.severityScore *= meta.baseWeight;
            }
        }

        // Output only valid
        if (cluster.sources.length >= THRESHOLDS.MINIMUM_NEW_ARTICLES_TO_TRIGGER_EVENT && cluster.severityScore >= THRESHOLDS.SEVERITY_THRESHOLD_FOR_EMAIL_ALERT) {
            validClusters.push(cluster);
        }
    }

    return validClusters.sort((a, b) => b.severityScore - a.severityScore);
}
