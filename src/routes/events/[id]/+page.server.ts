import { supabaseAdmin } from '$lib/server/supabase';
import { error } from '@sveltejs/kit';

export async function load({ params }) {
    const eventId = params.id;

    // Fetch the event
    const { data: event, error: evErr } = await supabaseAdmin
        .from('events')
        .select('*')
        .eq('id', eventId)
        .maybeSingle();

    if (evErr || !event) {
        throw error(404, 'Event not found');
    }

    // Fetch its sources and impacts
    const { data: sources } = await supabaseAdmin
        .from('event_sources')
        .select('*')
        .eq('event_id', eventId);

    const { data: impacts } = await supabaseAdmin
        .from('event_impacts')
        .select('*')
        .eq('event_id', eventId)
        .maybeSingle();

    return {
        event,
        sources: sources || [],
        impacts: impacts || null
    };
}
