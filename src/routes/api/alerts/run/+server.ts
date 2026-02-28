import { json } from '@sveltejs/kit';
import { supabaseAdmin } from '$lib/server/supabase';
import { sendAlertEmail } from '$lib/server/email';
import { fetchBreakingCandidates } from '$lib/api/news';
import { fetchMarketSnapshot } from '$lib/api/markets';
import { detectAndClusterEvents } from '$lib/analysis/event';
import { summarizeEvent } from '$lib/analysis/summarize';

export async function POST({ request, url }) {
    // Basic protection (e.g., matching a cron secret)
    const authHeader = request.headers.get('authorization');
    if (authHeader !== `Bearer ${process.env.CRON_SECRET || 'dev-cron-secret'}`) {
        return json({ error: 'Unauthorized' }, { status: 401 });
    }

    try {
        console.log('[CRON] Starting alert check...');

        // 1. Fetch breaking news candidates
        const candidates = await fetchBreakingCandidates();
        console.log(`[CRON] Fetched ${candidates.length} candidates.`);

        // 2. Cluster and score events
        const clusters = detectAndClusterEvents(candidates);
        console.log(`[CRON] Detected ${clusters.length} high-severity actionable clusters.`);

        let sentCount = 0;

        // Fetch subscribers
        const { data: subscribers, error: subErr } = await supabaseAdmin
            .from('subscribers')
            .select('*')
            .eq('status', 'confirmed');

        if (subErr) throw subErr;

        for (const cluster of clusters) {
            // Idempotency: ensure we haven't alerted on this specific title/topic recently
            const { data: existingEvent } = await supabaseAdmin
                .from('events')
                .select('id')
                .eq('title', cluster.title)
                .maybeSingle();

            if (existingEvent) {
                console.log(`[CRON] Event "${cluster.title}" already processed. Skipping.`);
                continue;
            }

            // 3. Map to markets & summarize
            const marketSnapshot = await fetchMarketSnapshot(cluster.tickers);
            const summary = await summarizeEvent(cluster);

            // 4. Store in DB
            const { data: newEvent, error: eventErr } = await supabaseAdmin
                .from('events')
                .insert({
                    title: cluster.title,
                    summary,
                    severity: cluster.severityScore
                })
                .select()
                .single();

            if (eventErr || !newEvent) {
                console.error('[CRON] Error inserting event:', eventErr);
                continue;
            }

            const sourcesToInsert = cluster.sources.map(s => ({
                event_id: newEvent.id,
                source: s.source,
                url: s.url,
                title: s.title,
                published_at: s.published_at ? new Date(s.published_at) : new Date()
            }));

            await supabaseAdmin.from('event_sources').insert(sourcesToInsert);

            await supabaseAdmin.from('event_impacts').insert({
                event_id: newEvent.id,
                sectors: cluster.sectors,
                tickers: cluster.tickers,
                confidence: cluster.severityScore > 150 ? 'High' : 'Medium',
                market_snapshot: marketSnapshot
            });

            // 5. Email all confirmed subscribers
            if (subscribers && subscribers.length > 0) {
                for (const sub of subscribers) {
                    await sendAlertEmail(
                        sub.email,
                        {
                            title: cluster.title,
                            summary,
                            sectors: cluster.sectors,
                            tickers: cluster.tickers
                        },
                        sub.unsub_token,
                        url.origin
                    );

                    await supabaseAdmin.from('email_logs').insert({
                        event_id: newEvent.id,
                        subscriber_id: sub.id,
                        status: 'sent'
                    });
                    sentCount++;
                }
            }
        }

        console.log(`[CRON] Finished. Processed ${clusters.length} clusters, sent ${sentCount} emails.`);
        return json({ success: true, clustersProcessed: clusters.length, emailsSent: sentCount });

    } catch (e) {
        console.error('[CRON] Error run failed:', e);
        return json({ error: 'Server error' }, { status: 500 });
    }
}

export const GET = POST;
