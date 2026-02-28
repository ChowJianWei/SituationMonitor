import type { EventCluster } from './event';
import { env } from '$env/dynamic/private';
import { evaluateEvent, type DecisionEngineOutput } from './decisionEngine';

export interface EventSummary extends DecisionEngineOutput {
    what_happened: string[];
    // Removed old positive/negative impacts as we now use causalLogic and structured impacts from DecisionEngine
}

export async function summarizeEvent(cluster: EventCluster): Promise<EventSummary> {
    const llmKey = env.LLM_API_KEY || process.env.LLM_API_KEY;

    // 1. Run the deterministic Decision Engine
    const decisionOutput = evaluateEvent(cluster.title, cluster.sources.map(s => s.title));

    // 2. Generate the "What Happened" context (Simulated LLM or Fallback)
    let what_happened: string[] = [];
    if (!llmKey) {
        what_happened = cluster.sources.slice(0, 3).map(s => s.title);
    } else {
        console.log('Sending to LLM to summarize breaking sources...');
        what_happened = [
            `Multiple sources report significant developments regarding ${cluster.title.replace('High Activity: ', '')}.`,
            ...cluster.sources.slice(0, 2).map(s => `As noted by ${s.source}: ${s.title}`)
        ];
    }

    return {
        ...decisionOutput,
        what_happened
    };
}
