import { supabaseAdmin } from '$lib/server/supabase';
import { error } from '@sveltejs/kit';

export async function load({ url }) {
    const token = url.searchParams.get('token');

    if (!token) {
        throw error(400, 'Missing unsubscribe token.');
    }

    const { data: subscriber, error: fetchErr } = await supabaseAdmin
        .from('subscribers')
        .select('*')
        .eq('unsub_token', token)
        .maybeSingle();

    if (fetchErr || !subscriber) {
        throw error(400, 'Invalid or expired unsubscribe token.');
    }

    if (subscriber.status === 'unsubscribed') {
        return { success: true, alreadyUnsubscribed: true };
    }

    const { error: updateErr } = await supabaseAdmin
        .from('subscribers')
        .update({ status: 'unsubscribed' })
        .eq('id', subscriber.id);

    if (updateErr) {
        console.error('Unsubscribe update error:', updateErr);
        throw error(500, 'Error unsubscribing.');
    }

    return { success: true, alreadyUnsubscribed: false };
}
