import { supabaseAdmin } from '$lib/server/supabase';
import { error } from '@sveltejs/kit';

export async function load({ url }) {
    const token = url.searchParams.get('token');

    if (!token) {
        throw error(400, 'Missing confirmation token.');
    }

    const { data: subscriber, error: fetchErr } = await supabaseAdmin
        .from('subscribers')
        .select('*')
        .eq('confirm_token', token)
        .maybeSingle();

    if (fetchErr || !subscriber) {
        throw error(400, 'Invalid or expired confirmation token.');
    }

    if (subscriber.status === 'confirmed') {
        return { success: true, alreadyConfirmed: true };
    }

    const { error: updateErr } = await supabaseAdmin
        .from('subscribers')
        .update({ status: 'confirmed', confirmed_at: new Date().toISOString() })
        .eq('id', subscriber.id);

    if (updateErr) {
        console.error('Confirmation update error:', updateErr);
        throw error(500, 'Error confirming subscription.');
    }

    return { success: true, alreadyConfirmed: false };
}
