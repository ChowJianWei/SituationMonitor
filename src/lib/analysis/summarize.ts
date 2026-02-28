import type { EventCluster } from './event';
import { env } from '$env/dynamic/private';

export async function summarizeEvent(cluster: EventCluster): Promise<{ what_happened: string[], why_it_matters: string[] }> {
    const llmKey = env.LLM_API_KEY || process.env.LLM_API_KEY;

    // Fallback template approach if no LLM configured
    if (!llmKey) {
        return {
            what_happened: cluster.sources.slice(0, 3).map(s => s.title),
            why_it_matters: [
                `This event triggered a severity score of ${cluster.severityScore}.`,
                `It heavily involves topics related to: ${cluster.sectors.join(', ') || 'General Markets'}`,
                `Keep an eye on related assets as volatility may increase.`
            ]
        };
    }

    // Mocking an actual LLM call for the template
    // In a real app, this would use OpenAI or OpenRouter to digest `cluster.sources` into bullets
    console.log('Sending to LLM for summarization...');
    return {
        what_happened: [
            `Multiple sources report significant developments regarding ${cluster.title.replace('High Activity: ', '')}.`,
            ...cluster.sources.slice(0, 2).map(s => `As noted by ${s.source}: ${s.title}`)
        ],
        why_it_matters: [
            `This development could have immediate cascading effects on ${cluster.sectors.join(', ')} sectors.`,
            `Potential regulatory or supply chain shifts are anticipated.`
        ]
    };
}
