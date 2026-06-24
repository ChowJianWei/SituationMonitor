import { json } from '@sveltejs/kit';
import { supabaseAdmin } from '$lib/server/supabase';
import { sendAlertEmail, sendDailyReportEmail } from '$lib/server/email';
import { fetchBreakingCandidates } from '$lib/api/news';
import { fetchMarketSnapshot } from '$lib/api/markets';
import { detectAndClusterEvents } from '$lib/analysis/event';
import { summarizeEvent } from '$lib/analysis/summarize';
import { getOptionsContext } from '$lib/services/quant';

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

            // 3b. Options context for each impacted ticker (non-blocking)
            const optionsContexts = await Promise.all(
                cluster.tickers.map((t: string) => getOptionsContext(t))
            );

            // 4. Store in DB
            const { data: newEvent, error: eventErr } = await supabaseAdmin
                .from('events')
                .insert({
                    title: cluster.title,
                    summary,
                    severity: summary.confidenceScore
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

            // Store per-ticker options context
            const optionsRows = optionsContexts
                .filter(Boolean)
                .map((ctx) => ({
                    event_id: newEvent.id,
                    ticker: ctx!.ticker,
                    spot: ctx!.spot,
                    expiry: ctx!.expiry,
                    dte: ctx!.dte,
                    atm_iv: ctx!.atm_iv,
                    implied_move_pct: ctx!.implied_move_pct,
                    delta: ctx!.greeks.delta,
                    gamma: ctx!.greeks.gamma,
                    theta: ctx!.greeks.theta,
                    vega: ctx!.greeks.vega,
                    risk_free_rate: ctx!.risk_free_rate,
                }));
            if (optionsRows.length > 0) {
                try {
                    const { error: optErr } = await supabaseAdmin.from('event_options_context').insert(optionsRows);
                    if (optErr) {
                        console.warn('[CRON] Options context insert failed (table might be missing):', optErr);
                    }
                } catch (optEx) {
                    console.warn('[CRON] Exception inserting options context:', optEx);
                }
            }

            // Build implied-move lines for email body
            const impliedMoveLines = optionsContexts
                .filter(Boolean)
                .map((ctx) =>
                    `${ctx!.ticker}: options imply ±${ctx!.implied_move_pct.toFixed(1)}% move by ${ctx!.expiry} (ATM IV ${(ctx!.atm_iv * 100).toFixed(1)}%)`
                );

            // 5. Email all confirmed subscribers
            if (subscribers && subscribers.length > 0) {
                for (const sub of subscribers) {
                    await sendAlertEmail(
                        sub.email,
                        {
                            title: cluster.title,
                            summary,
                            sectors: cluster.sectors,
                            tickers: cluster.tickers,
                            impliedMoveLines,
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

        if (clusters.length === 0) {
            console.log('[CRON] No high-severity clusters detected. Sending daily summary to subscribers...');
            const marketSnapshot = await fetchMarketSnapshot(['SPY', 'QQQ', 'VIX', 'GLD', 'USO']);
            if (subscribers && subscribers.length > 0) {
                for (const sub of subscribers) {
                    try {
                        await sendDailyReportEmail(
                            sub.email,
                            marketSnapshot,
                            sub.unsub_token,
                            url.origin
                        );
                        sentCount++;
                    } catch (mailEx) {
                        console.error(`[CRON] Failed to send daily report email to ${sub.email}:`, mailEx);
                    }
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
